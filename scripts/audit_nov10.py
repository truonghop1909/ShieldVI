"""Trace imported synthetic NOV10 exports against frozen v6.1; never tune rules."""
import argparse,csv,json,re,shutil,sys,unicodedata
from collections import Counter
from datetime import datetime
from pathlib import Path
R=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(R/'services/moderation-ai'));sys.path.insert(0,str(R/'scripts'))
from app.schemas import AnalyzeRequest,AnalyzeResponseV2
from app.experiments import fresh10_v6 as exp
from app.target_signals import infer_target
from synthetic_data.pipeline import atomic_json,file_sha
from evaluate_synthetic_signals import classification,grounding_metrics
from evaluate_fresh10_recovery import evidence_metrics
from verify_ai_readiness_lock import verify_lock
D=R/'datasets/fixtures/nov10_regression_v1';P=R/'reports/ai_update/nov10_audit_20261104'

def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def save_progress(stage,detail):
    path=P/'progress.json';state=read(path) if path.exists() else {'scope':'NOV10 root-cause audit','training_performed':False,'rules_modified':False,'milestones':[]}
    state['current']=stage
    if not any(x['stage']==stage for x in state['milestones']):
        state['milestones'].append({'stage':stage,'detail':detail})
        with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as stream:stream.write('\n\n## NOV10 audit — '+stage+'\n\n'+detail+'\n')
    atomic_json(path,state)

def import_pack(source):
    if (D/'manifest.json').exists():return
    files={}
    for old,new in [('threads','inputs'),('results','analysis')]:
        paths=sorted((source/old).glob('*.json'));assert len(paths)==10
        (D/new).mkdir(parents=True,exist_ok=True)
        for path in paths:
            dest=D/new/path.name;shutil.copyfile(path,dest);files[str(dest.relative_to(D)).replace('\\','/')]=file_sha(dest)
    (D/'source_metadata').mkdir(exist_ok=True)
    for name in ('expected_reference_labels.csv','expected_repeated_events.csv','README.md','test_manifest.json'):
        dest=D/name if name.endswith('.csv') else D/'source_metadata'/name
        shutil.copyfile(source/name,dest);files[str(dest.relative_to(D)).replace('\\','/')]=file_sha(dest)
    for record in read(source/'test_manifest.json')['threads']:assert file_sha(source/record['file'])==record['sha256']
    # No evaluation file accompanied the pack. Preserve the user-supplied
    # aggregate separately from independently recomputed metrics.
    atomic_json(D/'source_metadata/user_reported_evaluation.json',{'source':'User message; no separate evaluation file found in supplied pack',
        'binary':199,'raw_macro_f1':.6861,'final_macro_f1':.6942,'tp':7,'fp':3,'fn':15,'tn':174,
        'target_correct':0,'target_reference':22,'repeated_tp':0,'repeated_reference':8,'human_gold':False})
    files['source_metadata/user_reported_evaluation.json']=file_sha(D/'source_metadata/user_reported_evaluation.json')
    atomic_json(D/'manifest.json',{'dataset_id':'nov10_regression_v1','threads':10,'comments':200,'origin':'synthetic',
        'label_source':'synthetic_reference','human_gold':False,'training_forbidden':True,'independent_real_world_eligible':False,
        'usage':'development_regression_after_root_cause_audit','files':files})
    save_progress('IMPORTED','NOV10:10inputs/10analysis JSONs, two original reference CSVs and source docs byte-preserved; user aggregate stored separately because no evaluation file was present. Synthetic development only; no reference/model/rule edits.')

def replay(payload,export):
    by_text={c['text']:row['toxicity_score'] for c,row in zip(payload['comments'],export['comments'])}
    class Cached:
        threshold=.41;name=export['model_name']
        def predict_scores(self,texts):return [by_text[text] for text in texts]
    internal=exp.analyze_thread_v6(AnalyzeRequest.model_validate(payload),Cached())
    wire=AnalyzeResponseV2.model_validate(internal).model_dump(mode='json')
    return internal,wire

def audit():
    manifest=read(D/'manifest.json')
    for name,digest in manifest['files'].items():assert file_sha(D/name)==digest
    frozen=read(R/'reports/ai_update/fresh10_recovery_20261103/experiment_lock_v2.json')
    module=R/'services/moderation-ai/app/experiments/fresh10_v6.py'
    assert file_sha(module)==frozen['experimental_module_sha256']
    refs=list(csv.DictReader((D/'expected_reference_labels.csv').open(encoding='utf-8-sig',newline='')))
    labels={(x['thread_id'],x['comment_id']):x for x in refs};assert len(labels)==len(refs)==200
    truth={};imported=[];replayed=[];traces=[];rows=[];versions=Counter();hit_rules=Counter();decisions=Counter();contexts=Counter();forced=[]
    for path in sorted((D/'inputs').glob('*.json')):
        t=read(path);export=read(next((D/'analysis').glob(t['thread_id']+'_analysis.json')))
        assert export['source_model_threshold']==.41 and 'r06' in export['checkpoint_id']
        internal,wire=replay(t,export)
        assert wire==export,('Replay differs from export',t['thread_id'],[key for key in wire if wire[key]!=export.get(key)])
        imported.append({'output':export});replayed.append({'output':wire});versions[tuple(sorted(wire['rule_versions'].items()))]+=1
        payload=AnalyzeRequest.model_validate(t);by_id={c.comment_id:c for c in payload.comments};seen={};last=None
        for comment,row,raw in zip(payload.comments,wire['comments'],internal['comments']):
            assert comment.comment_id not in seen and (comment.parent_id is None or comment.parent_id in seen)
            assert last is None or comment.timestamp>last;seen[comment.comment_id]=True;last=comment.timestamp
            ref=labels[(t['thread_id'],comment.comment_id)];assert ref['text']==comment.text and ref['user_id']==comment.user_id
            assert (ref['parent_id'] or None)==comment.parent_id and ref['label_source']=='synthetic_reference' and ref['human_gold']=='false'
            truth[(t['thread_id'],comment.comment_id)]={'label':ref['expected_label'],'actor':comment.user_id,'target':ref['directed_at_user_id'] or None,'time':comment.timestamp.isoformat()}
            signals=raw['analysis_signals'];ctx=signals['context'];trace=signals['research_trace'];contexts.update(ctx['tags'])
            hit_rules.update(m['rule'] for m in trace['matches']);decisions.update(m['decision'] for m in trace['matches'])
            normalized=exp.base.context_view(exp.PLANTS.sub(lambda m:'z'*len(m.group()),unicodedata.normalize('NFC',comment.text)))
            pattern_hits={name:[{'span':[m.start(),m.end()],'match':m.group()} for m in pattern.finditer(normalized)]
                for name,pattern in {'v5_attack':exp.base.ATTACK,'v5_disparagement':exp.base.DISPARAGEMENT,'v5_indirect':exp.base.INDIRECT,**exp.RULES}.items()}
            gate={'attack_candidate':ctx['attack_candidate'],'confidence_ok':ctx['confidence'] in ('medium','high'),
                  'target_present':signals['target_candidate'] is not None,'target_confidence_ok':signals['target_evidence']['confidence'] in ('medium','high')}
            traces.append({'thread_id':t['thread_id'],'comment_id':comment.comment_id,'text':comment.text,'reference':ref['expected_label'],
                'normalized':normalized,'pattern_hits':pattern_hits,'research_trace':trace,'context':ctx,'qualification_gates':gate,
                'target_evidence':signals['target_evidence'],'raw_score':row['toxicity_score'],'assessment':row['moderation_assessment'],
                'reply_to_user_id':row['reply_to_user_id'],'legacy_recipient':row['target_user_id'],'directed_at_user_id':row['directed_at_user_id'],
                'attack_instance_candidate':signals['attack_instance_candidate']})
            rows.append({'thread_id':t['thread_id'],'comment_id':comment.comment_id,'reference':ref['expected_label'],
                         'raw':'TOXIC' if row['toxic_for_moderation'] else 'CLEAN','final':row['moderation_assessment']['label']})
            if ref['expected_label']=='TOXIC':
                # Oracle diagnostic ONLY, never used in predictions/metrics:
                # isolate target lookup from the failed context gate.
                context=exp.context_v6(comment.text,{c.user_id for c in payload.comments}-{comment.user_id})[0]
                context.attack_candidate=True;context.attack_clause_spans=[(0,len(exp.base.context_view(comment.text)))]
                target=infer_target(comment,by_id,context)
                forced.append({'thread_id':t['thread_id'],'comment_id':comment.comment_id,'diagnostic_only':True,
                               'reference_target':ref['directed_at_user_id'],'forced_context_target':target.model_dump()})
    events=list(csv.DictReader((D/'expected_repeated_events.csv').open(encoding='utf-8-sig',newline='')));event_audit=[]
    for event in events:
        ids=event['evidence_comment_ids'].split(';');matching=[x for x in traces if x['thread_id']==event['thread_id'] and x['comment_id'] in ids]
        assert len(matching)==len(ids)
        times=[datetime.fromisoformat(truth[(event['thread_id'],cid)]['time']) for cid in ids]
        for cid in ids:
            ref=truth[(event['thread_id'],cid)];assert ref['actor']==event['actor_user_id'] and ref['target']==event['target_user_id'] and ref['label']=='TOXIC'
        event_audit.append({**event,'span_minutes':(max(times)-min(times)).total_seconds()/60,'distinct_timestamps':len(set(times)),
            'qualified_instances':sum(c['attack_instance_candidate'] for c in matching),'first_failed_gate':'context.attack_candidate=false'})
    before={'classification':classification([(r['reference'],r['final']) for r in rows]),'grounding':grounding_metrics(imported,truth),
            'evidence':evidence_metrics(imported,events)}
    after={'classification':classification([(r['reference'],r['final']) for r in rows]),'grounding':grounding_metrics(replayed,truth),
           'evidence':evidence_metrics(replayed,events)}
    metrics={'raw':classification([(r['reference'],r['raw']) for r in rows]),'before':before,'after':after,'wire_exact_replay_threads':10,
        'comments':len(rows),'labels':dict(Counter(r['reference'] for r in rows)),'all_attack_candidates_false':all(not t['context']['attack_candidate'] for t in traces),
        'all_attack_instances_false':all(not t['attack_instance_candidate'] for t in traces),'pattern_hit_counts':dict(hit_rules),
        'predicate_decisions':dict(decisions),'context_tags':dict(contexts),'declared_layer_versions':dict(versions.most_common()[0][0]),
        'processor_sha256':file_sha(module),'rules_modified':False,'training_performed':False,'human_gold':False,
        'false_positives':[r for r in rows if r['reference']=='CLEAN' and r['final']=='TOXIC'],
        'missing_external_evaluation_file':True,'trace_wire_omission':'research_trace is not in AnalysisSignalsOut; response serialization omits it, while internal traces exist',
        'historical_process_hash_provenance':'Exports carry versions but no process/source hash; exact replay establishes consistency, not cryptographic identity of the original process.'}
    assert metrics['all_attack_candidates_false'] and metrics['all_attack_instances_false']
    for name,value in [('metrics',metrics),('comment_traces',traces),('event_audit',event_audit),('forced_target_diagnostic',forced),('replayed_outputs',replayed)]:atomic_json(P/(name+'.json'),value)
    ready=verify_lock(R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json');assert ready['status']=='PASS';atomic_json(P/'readiness_before.json',ready)
    save_progress('ROOT_CAUSE_REPLAYED','NOV10 v6.1 cached replay exactly matches all10wire exports/200comments, not a v5 assumption. Per-comment predicate/qualification traces and8event timelines saved. No rule changes. Target/event metrics remain0/22and0/8; detailed audit now available for distinguishing linguistic coverage from runtime problems.')
    print(json.dumps(metrics,ensure_ascii=False))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',type=Path);args=parser.parse_args()
    if args.source:import_pack(args.source)
    audit()
