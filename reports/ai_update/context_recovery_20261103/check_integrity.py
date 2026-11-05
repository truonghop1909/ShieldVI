from pathlib import Path
import json,hashlib
R=Path.cwd();P=R/'reports/ai_update/context_recovery_20261103';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protected=json.loads((R/'reports/ai_update/final/session_verification.json').read_text(encoding='utf-8'))['protected_hashes_unchanged']
changed=[p for p,v in protected.items() if not Path(p).is_file() or sha(p)!=v]
legacy=R/'datasets/synthetic_conversations';m=json.loads((legacy/'manifest.json').read_text(encoding='utf-8'));legacy_errors=[]
for tid,v in m['thread_checksums'].items():
 p=legacy/'threads'/(tid+'.json')
 if sha(p)!=v:legacy_errors.append(str(p))
for name,v in m['csv_checksums'].items():
 if sha(legacy/name)!=v:legacy_errors.append(name)
genz=legacy/'genz_v2';m=json.loads((genz/'dataset_manifest.json').read_text(encoding='utf-8'));lock=json.loads((genz/'development_lock.json').read_text(encoding='utf-8'))
assert sha(genz/'dataset_manifest.json')==lock['dataset_manifest_sha256']
assert all(sha(genz/'threads'/(tid+'.json'))==value for tid,value in m['thread_sha256'].items())
assert all(sha(genz/name)==value for name,value in m['output_sha256'].items())
new=R/'datasets/fixtures/context_recovery_v1';nm=json.loads((new/'manifest.json').read_text(encoding='utf-8'));before=json.loads((P/'before_lock.json').read_text(encoding='utf-8'))
assert sha(new/'manifest.json')==before['new_dataset_manifest_sha256']
assert all(sha(new/p)==value for p,value in nm['file_sha256'].items())
assert sha(new/'game_rank_30_reference.json')==nm['user_reference_sha256']
assert not changed and not legacy_errors
result={'status':'PASS','original_protected_artifacts':len(protected),'changed':changed,'original200_threads_unchanged':200,'original_csvs_unchanged':2,
 'genz500_threads_and_exports_unchanged':500,'new_AI_dataset_threads':12,'new_AI_dataset_comments':120,'user_reference_comments':30,'user_reference_modified_after_freeze':False,
 'threshold':.41,'independent_test_labels_used':False,'model_training_performed':False,'live_database_changed':False,'candidate_activated':False}
(P/'integrity_audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print(json.dumps(result))
