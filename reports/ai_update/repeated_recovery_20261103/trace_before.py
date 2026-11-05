import json,sys,shutil
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
D=R/'datasets/synthetic_genz';OLD=R/'reports/ai_update/synthetic_experiment_r06_20261103/evaluation'
outputs=json.loads((OLD/'hybrid_outputs.json').read_text(encoding='utf-8'))['r06']
threads={t['thread_id']:t for t in [json.loads(line) for line in (D/'challenge_threads.jsonl').read_text(encoding='utf-8').splitlines()]}
traces=[]
for item in outputs:
    if item['split']!='synthetic_challenge':continue
    t=threads[item['output']['thread_id']];pairs=defaultdict(list)
    for c in t['comments']:
        if c['label']=='TOXIC' and c['is_directed_attack'] and c['directed_at_user_id']:pairs[(c['user_id'],c['directed_at_user_id'])].append(c)
    out={c['comment_id']:c for c in item['output']['comments']}
    for (actor,target),comments in pairs.items():
        if len({c['timestamp'] for c in comments})<2:continue
        trace={'thread_id':t['thread_id'],'actor':actor,'target':target,'reference_ids':[c['comment_id'] for c in comments],
            'observed':[{k:out[c['comment_id']][k] for k in ('comment_id','reply_to_user_id','directed_at_user_id','analysis_signals')} for c in comments]}
        traces.append(trace);print(t['thread_id'],actor,'->',target)
        for c in t['comments']:
            o=out[c['comment_id']];s=o['analysis_signals']
            print(c['comment_id'].split('_')[-1],c['user_id'].split('_')[-1],c['parent_id'],c['label'],c['text'],'|',s['context_tags'],s['attack_instance_candidate'],s['target_evidence']['method'],o['directed_at_user_id'])
if not (P/'before_lock.json').exists():
    snapshot=P/'before_sources';snapshot.mkdir(exist_ok=True)
    for name in ('context_signals.py','target_signals.py','signal_engine.py'):shutil.copyfile(R/'services/moderation-ai/app'/name,snapshot/name)
    atomic_json(P/'before_lock.json',{'sources':{name:file_sha(snapshot/name) for name in ('context_signals.py','target_signals.py','signal_engine.py')},
        'previous_outputs_sha256':file_sha(OLD/'hybrid_outputs.json'),'previous_predictions_sha256':file_sha(OLD/'predictions.json'),
        'frozen_dataset_manifest_sha256':file_sha(D/'dataset_manifest.json'),'T028_real':'BLOCKED','training_allowed':False})
    atomic_json(P/'five_events_before.json',traces)
assert len(traces)==5
