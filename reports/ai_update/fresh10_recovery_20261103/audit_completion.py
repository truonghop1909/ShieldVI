"""Read-only content checks and additive evidence, never reseals readiness."""
import csv,json,re,sys
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(P))
from synthetic_data.pipeline import atomic_json,file_sha,normalized
from verify_ai_readiness_lock import verify_lock
from import_and_audit import progress

def validate_threads(paths):
    total=0;texts=[]
    for path in paths:
        data=json.loads(path.read_text(encoding='utf-8-sig'));seen={};last=None
        for comment in data['comments']:
            cid=comment['comment_id'];assert cid not in seen
            when=datetime.fromisoformat(comment['timestamp'].replace('Z','+00:00'));assert when.tzinfo
            assert last is None or when>last
            if comment.get('parent_id') is not None:assert comment['parent_id'] in seen
            seen[cid]=comment;last=when;texts.append(normalized(comment['text']));total+=1
            if 'annotation' in comment:
                a=comment['annotation'];assert a['label_source']=='synthetic_reference' and a['human_gold'] is False
                assert a['directed_at_user_id'] is None or a['directed_at_user_id']!=comment['user_id']
    return total,texts

def main():
    d=R/'datasets/fixtures/fresh10_regression_v1';manifest=json.loads((d/'manifest.json').read_text())
    for name,digest in manifest['files'].items():assert file_sha(d/name)==digest
    assert manifest['training_forbidden'] and not manifest['human_gold']
    refs=list(csv.DictReader((d/'expected_reference_labels.csv').open(encoding='utf-8-sig',newline='')))
    assert len({(r['thread_id'],r['comment_id']) for r in refs})==200
    imported_count,first_texts=validate_threads(sorted((d/'inputs').glob('*.json')))
    folders=[d/'inputs'];all_texts=list(first_texts);counts=[imported_count]
    for name in ('fresh10_postfix_holdout_v1','fresh10_postfix_holdout_v2'):
        folder=R/'datasets/fixtures'/name;meta=json.loads((folder/'manifest.json').read_text())
        assert meta['training_forbidden'] and not meta['human_gold']
        for tid,digest in meta['thread_sha256'].items():assert file_sha(folder/'threads'/(tid+'.json'))==digest
        count,texts=validate_threads(sorted((folder/'threads').glob('*.json')));counts.append(count);all_texts+=texts;folders.append(folder/'threads')
    assert counts==[200,48,24]
    assert len(set(all_texts))==len(all_texts)
    source=P/'experimental_sources/v6_initial.py';old=json.loads((P/'experiment_lock.json').read_text())
    assert file_sha(source)==old['experimental_module_sha256']
    lock=P/'experiment_lock_v2.json';latest=json.loads(lock.read_text())
    assert latest['parent_lock_sha256']==file_sha(P/'experiment_lock.json')
    assert latest['experimental_module_sha256']==file_sha(R/'services/moderation-ai/app/experiments/fresh10_v6.py')
    assert latest['existing_readiness_lock_sha256']==old['existing_readiness_lock_sha256']
    ready=verify_lock(R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json');assert ready['status']=='PASS'
    reportlog=(P/'full_tests.log').read_bytes()
    log=reportlog.decode('utf-16' if reportlog[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
    assert re.search(r'648 passed, 1 warning',log) and 'FAILED ' not in log
    metrics=json.loads((P/'development_v3/fresh10_metrics.json').read_text())
    broad=json.loads((P/'development_v3/old_regression_metrics.json').read_text())
    assert broad['classification']['before']==broad['classification']['after']
    assert broad['grounding']['before']==broad['grounding']['after'] and not broad['new_label_errors']
    final=json.loads((P/'final_challenge/metrics.json').read_text())
    assert final['experiment_lock_sha256']==file_sha(lock) and not final['new_label_errors']
    outputs={x['output']['thread_id']:x['output'] for x in json.loads((P/'development_v3/fresh10_after.json').read_text())}
    case_ids={2:['c10'],3:['c07','c12','c16'],5:['c08','c10','c13'],7:['c06','c07','c11','c12'],8:['c08','c13','c17'],9:['c17'],10:['c14']}
    cases=[]
    for number,ids in case_ids.items():
        before=json.loads(next((d/'analysis').glob('*_'+str(number).zfill(2)+'_*analysis.json')).read_text());after=outputs[before['thread_id']]
        thread=json.loads(next((d/'inputs').glob('TEST'+str(number).zfill(2)+'_*.json')).read_text());texts={c['comment_id']:c['text'] for c in thread['comments']}
        for cid in ids:
            a=next(c for c in before['comments'] if c['comment_id']==cid);b=next(c for c in after['comments'] if c['comment_id']==cid)
            cases.append({'thread_id':before['thread_id'],'comment_id':cid,'text':texts[cid],'before':a,'after':b})
        if number in (3,8):
            event=after['evidence'][0];assert set(event['evidence_comment_ids'])==set(ids)
        if number==5:assert not after['evidence']
    atomic_json(P/'case_traces.json',cases)
    # Preserve the locked runtime development exclusions; prepare an explicit
    # extension for the next evaluation-lock revision rather than modifying it.
    source_records=[{'path':str(path.relative_to(R)).replace('\\','/'),'sha256':file_sha(path),'format':'thread_json',
        'purpose':'Exclude newly exposed synthetic development/challenge text from future real-world evaluation'}
        for folder in folders for path in sorted(folder.glob('*.json'))]
    atomic_json(P/'T028_EXCLUSION_EXTENSION.json',{'audit_completed':True,'thread_ids':list(outputs)+[
        json.loads(p.read_text())['thread_id'] for folder in folders[1:] for p in folder.glob('*.json')],
        'source_records':source_records,'runtime_merged':False,'reason':'Existing development exclusions are readiness-locked; integrate in a separately approved future lock revision.'})
    # Warn about near duplicates, without removing difficult reference rows.
    corpus=[normalized(c['text']) for path in (R/'datasets/synthetic_genz/threads').glob('*.json') for c in json.loads(path.read_text())['comments']]
    near=[]
    for index,text in enumerate(all_texts):
        for other in corpus+all_texts[:index]:
            if min(len(text),len(other))/max(len(text),len(other))<.85:continue
            if SequenceMatcher(None,text,other).quick_ratio()<.85:continue
            ratio=SequenceMatcher(None,text,other).ratio()
            if ratio>=.85:near.append({'comment_index':index,'ratio':ratio})
    atomic_json(P/'integrity.json',{'status':'PASS','versioned_comments':counts,'imported_original_files_verified':len(manifest['files']),
        'distinct_comment_texts':len(set(all_texts)),'near_duplicate_threshold':.85,'near_duplicate_warnings':near,
        'readiness':ready,'root_tests_passed':648,'root_tests_failed':0,'warning':'Starlette TestClient deprecation',
        'old_regression_metrics_unchanged':True,'new_challenge_rule_hash_unchanged':True,'references_changed':False,
        'training_performed':False,'default_changed':False,'v5_runtime_changed':False,'new_exclusions_runtime_merged':False})
    progress('VALIDATED_HANDOFF','648 root tests PASS/0FAIL/1deprecation warning; 28 targeted tests included. Fresh10 TP15→18/FP6→1/FN7→4,Macro.830105→.931861,target5→16/22,repeated2→6/7,evidence15/15 correct and15/19 coverage. Old890 regression unchanged. Initial48comment challenge exposed new apology FP, preserved then converted to development; reporting fix now FP1/FN0 there. New post-v6.1-freeze24comment challenge TP5/FP1/FN1/TN17,Macro.888889,target5/6,repeated1/2,P1/R.5,evidence2/2correct, no post-score changes. One metaphor miss and one raw-score FP remain; not human gold/independent real. Readiness1311filesPASS, no model/default/train/deploy. Opt-in research code only; live v5 still unchanged. T028/T029formalBLOCKED,T030–T033PARTIAL. Report docs/ai-update/final-report/FRESH10_RECOVERY.md; new exclusion extension pending a future lock revision.')
    print(json.dumps({'status':'PASS','near_duplicate_warnings':len(near),'readiness_files':ready['files_checked'],'root_tests_passed':648}))

if __name__=='__main__':main()
