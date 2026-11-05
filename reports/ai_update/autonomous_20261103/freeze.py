from pathlib import Path
import json,hashlib
R=Path.cwd();out=R/'reports/ai_update/autonomous_20261103';data=R/'datasets/synthetic_conversations/genz_v2'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
m=json.loads((data/'dataset_manifest.json').read_text(encoding='utf-8'))
threads=[json.loads(line) for line in (data/'development_threads.jsonl').read_text(encoding='utf-8').splitlines()]
lock={'protocol':'synthetic_development_only','seed':20261103,'threshold':.41,'human_gold':False,'dataset_manifest_sha256':sha(data/'dataset_manifest.json'),'development_sha256':sha(data/'development_threads.jsonl'),'thread_ids':[t['thread_id'] for t in threads],'threads':len(threads),'comments':sum(len(t['comments']) for t in threads),'training_forbidden_thread_ids':[t['thread_id'] for t in threads]}
p=data/'development_lock.json'
if p.exists():assert json.loads(p.read_text(encoding='utf-8'))==lock
else:p.write_text(json.dumps(lock,indent=2)+'\n',encoding='utf-8')
state=json.loads((out/'progress.json').read_text(encoding='utf-8'));state['tasks'].update(synthetic_generation='DONE',T029='BLOCKED',T030='IN_PROGRESS',T031='IN_PROGRESS',T032='IN_PROGRESS');state.update(next_action='Real V1 development inference; local registry; integration checks',synthetic_comments=5115);(out/'progress.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as f:f.write('\nGenZ500 complete: 500 threads /5115 comments, 200 imported+300 new; 11 batch manifests. AIlabels4667 CLEAN/369 TOXIC/79 UNCERTAIN, human0. Train440threads4398 eligible rows; development60threads isolated by family. New preparation11340 rows (6942 ViCTSD+4398 synthetic), ratio38.78%, no exact/near held-out/challenge overlap. T029 BLOCKED: no CUDA/exact resource approval, optimizer0. Root350PASS, Social177PASS in service venv (root venv initially lacked Alembic); all3frontend buildsPASS. Proceed independent T030/T031/T032/T033 per latest user authorization.\n')
models={}
for mid,path,role in [('v1',Path('C:/Users/admin/Downloads/visobert_toxic_final'),'baseline'),('v1_1',R/'models/visobert_head_refined','active_existing'),('v2_previous',R/'models/visobert_v2_synthetic_experiment','experimental')]:
    cfg=json.loads((path/'threshold_config.json').read_text(encoding='utf-8'))
    models[mid]={'path':str(path),'role':role,'threshold':.41,'approved_for_selection':role!='experimental','sha256':{n:sha(path/n) for n in ('model.safetensors','config.json','threshold_config.json','tokenizer_config.json','tokenizer.json','sentencepiece.bpe.model','special_tokens_map.json') if (path/n).exists()},'model_version':cfg.get('model_version','original V1')}
registry={'schema_version':1,'mode':'local_opt_in_only','production_default_changed':False,'existing_default':'v1_1','fallback':'v1','candidate_available':False,'candidate_run_id':'T029_genz500_20261103_r02','models':models,'dataset_sha256':sha(data/'dataset_manifest.json'),'development_lock_sha256':sha(p),'threshold':.41,'rule_sha256':{str(q.relative_to(R)):sha(q) for q in [R/'services/moderation-ai/app/signal_engine.py',R/'services/moderation-ai/app/context_signals.py',R/'services/moderation-ai/app/target_signals.py',R/'services/moderation-ai/app/data/lexicon/active.json']},'git_commit':None,'git_note':'Workspace has no git metadata; hashes identify this local snapshot'}
(R/'configs/model_registry.local.json').write_text(json.dumps(registry,indent=2)+'\n',encoding='utf-8')
print('Dataset locked; registry inventory generated; no runtime selection changed')

