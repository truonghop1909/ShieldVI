"""Read-only prediction audit and additive exclusion revision after scoring."""
import csv,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent;D=R/'datasets/fixtures/v62_postfreeze_challenge_v1'
sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(P))
from synthetic_data.pipeline import atomic_json,file_sha
from check_development_exclusions import check
from evaluate_research_v62 import annotated,fresh_items,target_truth
from verify_ai_readiness_lock import verify_lock
from progress import record

def write_csv(path,rows,fields):
    with path.open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)

if __name__=='__main__':
    frozen=json.loads((P/'V62_LOCK.json').read_text())
    for name,digest in frozen['files'].items():assert file_sha(R/name)==digest
    base=R/'datasets/real_conversations/manifests/development_exclusions.research_20261104.json'
    output=R/'datasets/real_conversations/manifests/development_exclusions.research_v62_20261104.json';assert not output.exists()
    index=json.loads(base.read_text());records={r['path']:r for r in index['source_records']};ids=set(index['thread_ids'])
    for path in sorted((D/'threads').glob('*.json')):
        thread=json.loads(path.read_text());ids.add(thread['thread_id']);name=str(path.relative_to(R)).replace('\\','/')
        records[name]={'path':name,'sha256':file_sha(path),'format':'thread_json','purpose':'Newly viewed v6.2 synthetic challenge excluded from independent evaluation'}
    index.update(version='research-exclusions-v62-20261104',parent_manifest_sha256=file_sha(base),thread_ids=sorted(ids),source_records=list(records.values()),
        activation='Explicit versioned preflight only; sealed default loader unchanged')
    atomic_json(output,index)
    checks=[]
    for folder in (D/'threads',R/'datasets/fixtures/nov10_regression_v1/inputs'):
        for path in sorted(folder.glob('*.json')):
            result=check(output,json.loads(path.read_text()));assert result['status']=='EXCLUDED_DEVELOPMENT';checks.append(result)
    atomic_json(P/'exclusion_verification.json',{'status':'PASS','manifest':str(output.relative_to(R)).replace('\\','/'),
        'manifest_sha256':file_sha(output),'verified_threads':len(checks),'default_loader_modified':False,'checks':checks})
    errors=[];uncertain=[];bad_targets=[];bad_evidence=[];missing_evidence=[]
    small={
        'postfix48':('fresh10_postfix_holdout_v1','fresh10_recovery_20261103/postfix_scores.json'),
        'postfix24':('fresh10_postfix_holdout_v2','fresh10_recovery_20261103/final_scores.json'),
        'nov_audit24':('nov10_audit_challenge_v1','nov10_audit_20261104/challenge_scores.json'),
        'repeated74':('repeated_holdout_20261103','repeated_recovery_20261103/evaluation/fresh_scores.json')}
    cohorts=[(path.parent.name,path.parent) for path in (P/'frozen_development').glob('*/metrics.json')]+[('postfreeze36',P/'postfreeze_challenge/paired')]
    for name,folder in cohorts:
        metrics=json.loads((folder/'metrics.json').read_text());rows=json.loads((folder/'rows.json').read_text())
        for row in metrics['remaining_errors']:errors.append({'cohort':name,'kind':'FP' if row['reference']=='CLEAN' else 'FN',**row})
        uncertain += [{'cohort':name,**row,'review_status':'UNREVIEWED_SYNTHETIC_REFERENCE'} for row in rows if row['reference']=='UNCERTAIN']
        if name in ('fresh10','nov10'):_,truth=fresh_items(R/'datasets/fixtures'/(name+'_regression_v1'))
        elif name=='old890':truth=target_truth()
        elif name=='postfreeze36':_,truth,_=annotated(D,P/'postfreeze_scores.json')
        else:
            data,cache=small[name];_,truth,_=annotated(R/'datasets/fixtures'/data,R/'reports/ai_update'/cache)
        outputs=json.loads((folder/'after.json').read_text())
        for item in outputs:
            t=item['output'];tid=t['thread_id']
            for row in t['comments']:
                ref=truth.get((tid,row['comment_id']));target=row['directed_at_user_id']
                if ref is None or ref['label']=='UNCERTAIN':continue
                correct=ref['label']=='TOXIC' and target is not None and target==ref['target']
                if target is not None and not correct:
                    bad_targets.append({'cohort':name,'thread_id':tid,'comment_id':row['comment_id'],'predicted_target':target,'reference_label':ref['label'],'reference_target':ref['target']})
            for event in t['evidence']:
                for cid in event['evidence_comment_ids']:
                    ref=truth.get((tid,cid))
                    if ref is None or ref['label']=='UNCERTAIN':continue
                    if not (ref['label']=='TOXIC' and ref['actor']==event['actor_user_id'] and ref['target']==event['target_user_id']):
                        bad_evidence.append({'cohort':name,'thread_id':tid,'comment_id':cid,'event':event,'reference':ref})
        missing_evidence += [{'cohort':name,**item} for item in metrics.get('reference_evidence',{}).get('after',{}).get('missing_evidence',[])]
    fields=['cohort','kind','thread_id','comment_id','text','reference','raw_score','before','after','before_target','after_target']
    write_csv(P/'remaining_fp_fn.csv',errors,fields)
    write_csv(P/'uncertain_reference_cases.csv',uncertain,['cohort','thread_id','comment_id','text','reference','before','after','review_status'])
    atomic_json(P/'evidence_and_target_errors.json',{'emitted_target_errors':bad_targets,'emitted_evidence_errors':bad_evidence,
        'missing_reference_evidence':missing_evidence,'human_gold':False,'note':'Unknown/UNCERTAIN reference grounding is omitted, never silently treated as verified; completeness is separate from emitted correctness.'})
    ready=verify_lock(R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json');assert ready['status']=='PASS'
    atomic_json(P/'readiness_after.json',ready)
    record('STABILIZED_EXPERIMENTAL_NO_PROMOTION','722standardrootPASS/0FAIL/1deprecationwarning; v6.2 originalquote expectationsPASS while sealedv6.1 historicalred behavior retained.45targeted testsPASS incl43processor/2adjudication; finaltimestampedannotationexport2testsPASS,24ownerdecisions/reviewer fieldsblank/nohumanreview. Frozen36commentchallenge v6.1→v6.2 Macro.731744→.911330,TP3→6,FP0→0,FN5→2,TN28→28,target1→6/8,repeated0→2/3,P1/R.667,evidence4/4correct and4/6coverage; two unseen metaphor/exclusion misses retained, no post-score edits. NOV10 Macro.694160→.719137,target0→2/22,repeated0→1/8,evidence2/2correct but2/21coverage; Fresh10/old890 unchanged. Source/reference/default/readiness1311SHA remain unchanged;6newseen challenge threads +NOV10 verified excluded by explicitversionedoverlay, defaultloader unchanged. No modeltraining/defaultactivation/deploy; T028/T029BLOCKED,T030–T033PARTIAL. All remaining FP/FN/ambiguous references/emitted target/evidence errors saved. Latest owner review artifact adjudication_v3/NOV10_ADJUDICATION.html.')
    print(json.dumps({'exclusion_checks':len(checks),'remaining_fp_fn':len(errors),'uncertain_references':len(uncertain),
        'emitted_target_errors':len(bad_targets),'emitted_evidence_errors':len(bad_evidence),'readiness':'PASS'}))
