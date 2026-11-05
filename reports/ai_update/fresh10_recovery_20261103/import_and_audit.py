"""Import user-run Fresh10 verbatim and trace v5 causes before experimental edits."""
import csv,json,shutil,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent;D=R/'datasets/fixtures/fresh10_regression_v1'
SOURCE=Path('C:/Users/admin/Downloads/ShieldVI_Fresh10_r06_v5_TestPack/ShieldVI_Fresh10_r06_v5_TestPack')
sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(R/'services/moderation-ai'))
from synthetic_data.pipeline import atomic_json,file_sha
from verify_ai_readiness_lock import verify_lock
from app.schemas import AnalyzeRequest,AnalyzeResponseV2
from app import context_signals as ctx
from app.signal_engine import analyze_thread_v2
from evaluate_synthetic_signals import classification,grounding_metrics

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def progress(stage,text):
    path=P/'progress.json';state=read(path) if path.exists() else {'scope':'Fresh10 synthetic development only','milestones':[],'training_performed':False}
    state['current']=stage
    if not any(x['stage']==stage for x in state['milestones']):
        state['milestones'].append({'stage':stage,'detail':text})
        with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as f:f.write('\n\n## Fresh10 recovery — '+stage+'\n\n'+text+'\n')
    atomic_json(path,state)

def run():
    if (D/'manifest.json').exists():raise FileExistsError('Never overwrite a versioned imported regression')
    baseline=verify_lock(R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json');assert baseline['status']=='PASS'
    atomic_json(P/'readiness_before.json',baseline)
    for old,new in [('threads','inputs'),('results','analysis')]:
        (D/new).mkdir(exist_ok=True)
        for source in (SOURCE/old).glob('*.json'):shutil.copyfile(source,D/new/source.name)
    for name in ('expected_reference_labels.csv','expected_repeated_events.csv','test_manifest.json','quality_report.json','README.md','test_plan.md'):
        if name in ('expected_reference_labels.csv','expected_repeated_events.csv'):target=D/name
        else:(D/'source_metadata').mkdir(exist_ok=True);target=D/'source_metadata'/name
        shutil.copyfile(SOURCE/name,target)
    threads={t['thread_id']:t for t in map(read,sorted((D/'inputs').glob('*.json')))}
    results={t['thread_id']:t for t in map(read,sorted((D/'analysis').glob('*.json')))}
    refs=list(csv.DictReader((D/'expected_reference_labels.csv').open(encoding='utf-8-sig',newline='')))
    labels={(x['thread_id'],x['comment_id']):x for x in refs};truth={};outputs=[];flat=[]
    assert len(threads)==len(results)==10 and len(refs)==200 and len(labels)==200
    for tid,t in threads.items():
        payload=AnalyzeRequest.model_validate(t);assert len(payload.comments)==20
        imported=results[tid];AnalyzeResponseV2.model_validate(imported)
        assert imported['source_model_threshold']==.41 and 'r06' in imported['checkpoint_id']
        assert imported['rule_versions']['context']=='context-v5'
        scores={c['comment_id']:c['toxicity_score'] for c in imported['comments']};bytext={c['text']:scores[c['comment_id']] for c in t['comments']}
        class Cached:
            threshold=.41;name=imported['checkpoint_id']
            def predict_scores(self,texts):return [bytext[text] for text in texts]
        replay=json.loads(json.dumps(analyze_thread_v2(payload,Cached())))
        for c,a,b in zip(t['comments'],imported['comments'],replay['comments']):
            reference=labels[(tid,c['comment_id'])]
            assert reference['text']==c['text'] and reference['user_id']==c['user_id']
            assert a['comment_id']==b['comment_id']==c['comment_id'] and a['user_id']==c['user_id']
            assert a['parent_id']==c.get('parent_id')
            if a['analysis_signals']!=b['analysis_signals'] or a['moderation_assessment']!=b['moderation_assessment']:
                raise ValueError(json.dumps({'thread':tid,'comment':c['comment_id'],'input_profile':t.get('profile'),'output_profile':imported['profile'],
                    'signals_diff':{key:[a['analysis_signals'][key],b['analysis_signals'][key]] for key in a['analysis_signals'] if a['analysis_signals'][key]!=b['analysis_signals'][key]},
                    'assessment':[a['moderation_assessment'],b['moderation_assessment']]},ensure_ascii=False))
            truth[(tid,c['comment_id'])]={'label':reference['expected_label'],'actor':c['user_id'],
                'target':reference['directed_at_user_id'] if reference['is_directed_attack']=='true' else None,'time':c['timestamp']}
            flat.append({'thread_id':tid,'comment_id':c['comment_id'],'reference':reference['expected_label'],'raw':'TOXIC' if a['toxic_for_moderation'] else 'CLEAN','final':a['moderation_assessment']['label']})
        assert imported['evidence']==replay['evidence'];outputs.append({'output':imported})
    baseline_metrics={'raw':classification([(r['reference'],r['raw']) for r in flat]),'final':classification([(r['reference'],r['final']) for r in flat]),'grounding':grounding_metrics(outputs,truth)}
    assert baseline_metrics['final']['tp']==15 and baseline_metrics['final']['fp']==6 and baseline_metrics['final']['fn']==7 and baseline_metrics['final']['tn']==167
    assert baseline_metrics['grounding']['target_correct']==5 and baseline_metrics['grounding']['repeated']['tp']==2
    atomic_json(P/'baseline_metrics.json',baseline_metrics)
    trace=[]
    for number,cid in [(9,'c17'),(10,'c14')]:
        tid=next(k for k in threads if k.startswith('SHIELDVI_FRESH10_'+str(number).zfill(2)+'_'));t=threads[tid]
        c=next(c for c in t['comments'] if c['comment_id']==cid);out=next(c for c in results[tid]['comments'] if c['comment_id']==cid)
        view=ctx.context_view(c['text']);matches=[]
        for name in ('ATTACK','DISPARAGEMENT','INDIRECT','DEFENSE','APOLOGY','NEW_PERSONAL_CLAUSE','BREAK'):
            pattern=getattr(ctx,name)
            matches += [{'rule':name,'pattern':pattern.pattern,'normalized_span':[m.start(),m.end()],'normalized_match':m.group()} for m in pattern.finditer(view)]
        trace.append({'thread_id':tid,'comment_id':cid,'text':c['text'],'normalized_context_view':view,'raw_score':out['toxicity_score'],
            'rule_matches':matches,'context':out['analysis_signals']['context'],'target':out['analysis_signals']['target_evidence'],
            'reply_to_user_id':out['reply_to_user_id'],'final':out['moderation_assessment'],
            'cause':'Bare causal connector matches DEFENSE; no attack vocabulary hit or unresolved-clause guard, so non_attack_context_confirmed overrides rawTOXIC.' if number==9 else 'Vietnamese accent folding maps the culinary word ngò to ngo, matching ATTACK. Addressed reply to U05 grounds a spurious attack.'})
    atomic_json(P/'priority_root_causes.json',trace)
    files={p.relative_to(D).as_posix():file_sha(p) for p in D.rglob('*') if p.is_file()}
    atomic_json(D/'manifest.json',{'schema_version':1,'dataset_id':'fresh10_regression_v1','source_archive_sha256':file_sha(SOURCE.parent.parent/'ShieldVI_Fresh10_r06_v5_TestPack.zip'),
        'origin':'synthetic','label_source':'synthetic_reference','human_gold':False,'threads':10,'comments':200,
        'labels':dict(Counter(r['expected_label'] for r in refs)),'usage':'development_regression_after_current_analysis',
        'training_forbidden':True,'independent_real_world_eligible':False,'user_analysis_scores':'Imported r06 exports; v5 context/evidence exact replay verified, no new model forward claimed',
        'readiness_lock_modified':False,'files':files})
    progress('IMPORTED_AND_PRIORITY_CAUSES_VERIFIED','Imported10input/10analysis JSONs and original two CSVs verbatim,200comments/195binary/5UNCERTAIN, synthetic_reference not human gold. Replayedv5 exactly: finalTP15/FP6/FN7/TN167,target5/22,repeated2/7. Test09c17 bare khong_co_nghia DEFENSE overrides rawTOXIC; Test10c14 ngò→ngo ATTACK, addressed replyU05. Baseline lockPASS. No code fix yet; proposed changes will be opt-in experiment, frozenv5/default unchanged.')
    print(json.dumps({'imported':len(files),'baseline':baseline_metrics,'priority_causes':[{'thread':x['thread_id'],'comment':x['comment_id'],'cause':x['cause']} for x in trace]},ensure_ascii=False))
if __name__=='__main__':run()
