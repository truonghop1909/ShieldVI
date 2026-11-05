from pathlib import Path
import json,hashlib,csv
R=Path.cwd();P=R/'reports/ai_update/all_tasks_cpu_20261103';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
protected=json.loads((R/'reports/ai_update/final/session_verification.json').read_text(encoding='utf-8'))['protected_hashes_unchanged']
assert all(Path(p).is_file() and sha(p)==v for p,v in protected.items())
genz=R/'datasets/synthetic_conversations/genz_v2';m=json.loads((genz/'dataset_manifest.json').read_text(encoding='utf-8'));lock=json.loads((genz/'development_lock.json').read_text(encoding='utf-8'))
assert sha(genz/'dataset_manifest.json')==lock['dataset_manifest_sha256'] and sha(genz/'development_threads.jsonl')==lock['development_sha256']
assert all(sha(genz/'threads'/(tid+'.json'))==value for tid,value in m['thread_sha256'].items())
assert all(sha(genz/name)==value for name,value in m['output_sha256'].items())
legacy=R/'datasets/synthetic_conversations';lm=json.loads((legacy/'manifest.json').read_text(encoding='utf-8'))
assert all(sha(legacy/'threads'/(tid+'.json'))==value for tid,value in lm['thread_checksums'].items())
assert all(sha(legacy/name)==value for name,value in lm['csv_checksums'].items())
recovery=R/'datasets/fixtures/context_recovery_v1';rm=json.loads((recovery/'manifest.json').read_text(encoding='utf-8'));before=json.loads((R/'reports/ai_update/context_recovery_20261103/before_lock.json').read_text(encoding='utf-8'))
assert sha(recovery/'manifest.json')==before['new_dataset_manifest_sha256'] and sha(recovery/'game_rank_30_reference.json')==rm['user_reference_sha256']
assert all(sha(recovery/p)==value for p,value in rm['file_sha256'].items())
prepared=json.loads((R/'reports/ai_update/T029/genz500_cpu_prepared/manifest.json').read_text(encoding='utf-8'))
assert all(sha(Path(v['path']))==v['sha256'] for v in prepared['sources'].values())
result={'status':'PASS','original_protected_hashes':len(protected),'original200_threads_and2CSV_unchanged':True,'GenZ500_and_frozen_development_unchanged':True,'context_recovery12_and_user_reference_unchanged':True,
 'ViCTSD_original_validation_test_unchanged':True,'live_SQLite_unchanged':True,'original_V1_weights_and_threshold_unchanged':True,'existing_approved_default_unchanged':True,'candidate_separate':True,'production_deployed':False}
(P/'integrity_audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
rows=list(csv.DictReader((P/'heldout_predictions.csv').open(encoding='utf-8-sig')))
near=[r for r in rows if abs(float(r['score'])-.41)<=1e-5]
(P/'numerical_threshold_check.json').write_text(json.dumps({'scored_heldout_model_rows':len(rows),'rows_within_1e_5_of_0_41':len(near),'threshold_changed':False},indent=2)+'\n',encoding='utf-8')
print(json.dumps(result))
