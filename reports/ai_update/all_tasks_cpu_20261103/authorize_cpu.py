from pathlib import Path
import json,hashlib
R=Path.cwd();P=R/'reports/ai_update/all_tasks_cpu_20261103';state=json.loads((P/'progress.json').read_text(encoding='utf-8'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r={'authorization_type':'bounded_local_cpu_request_v1','authorized_local_task_execution':True,'source_user_request':state['user_request'],'source_user_request_sha256':state['user_request_sha256'],
 'authority_interpretation':state['authority_interpretation'],'user_approved_exact_hyperparameters':False,'paid_services_allowed':False,'production_changes_allowed':False,
 'config_sha256':sha(R/'configs/t029_genz500_cpu_head.json'),'prepared_manifest_sha256':sha(R/'reports/ai_update/T029/genz500_cpu_prepared/manifest.json'),
 'resource':'local_CPU','max_training_seconds':900,'max_cpu_threads':4,'maximum_external_cost':0}
(P/'cpu_authorization.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Local CPU authorization bound to current request, exact config/data; manual hyperparameter approval not claimed')
