from pathlib import Path
import json,re,hashlib,csv
from urllib.parse import unquote
R=Path.cwd();out=R/'reports/ai_update/autonomous_20261103';D=R/'docs/ai-update/final-report';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
# Report actual commands, environment corrections and previously failed attempts.
verification={'status':'PASS','root_tests':{'command':'.venv/Scripts/python.exe -X utf8 -m pytest tests -q -p no:cacheprovider --basetemp reports/ai_update/test_tmp/autonomous500_handoff','passed':358,'warnings':1,'evidence':'handoff_root_tests.txt'},
 'social_tests':{'command':'services/social-api/.venv/Scripts/python.exe -m pytest tests (cwd services/social-api; PYTHONPATH=src; isolated basetemp)','passed':177,'warnings':1,'evidence':'social_tests_service.txt'},
 'browser_e2e':{'passed':1,'command':'services/social-api/.venv/Scripts/python.exe -X utf8 scripts/run_ai_update_e2e.py','AI':'explicit fixture scores, not model inference','evidence':'e2e_runner_release.txt'},
 'frontend_builds':{'social':'PASS','moderation':'PASS','legacy_dashboard':'PASS','production_static_overwritten':False},
 'real_model_inference':{'V1_development_comments':620,'threshold':.41,'candidate':None,'registry_fallback_smoke':'PASS','API_recovery':'503 then200','optimizer_steps':0},
 'regression_ablation':{'comments':150,'source':'T020 cached real V1 on original inputs; B0-B3 offline replay','new_forward_claimed':False,'baseline_input_sha_bound':True},
 'quality':'PASS technical; semantic naturalness and AI labels unverified by humans',
 'resolved_attempts':['GenZ450 duplicate sentence rejected and rewritten before export; checks not relaxed.','Social tests initially used root venv without Alembic; rerun with service venv passed.','Initial E2E TEMP did not propagate; fixed TEMP/TMP for children, no fixture guard bypass.','Integrity script initially omitted .json suffix for legacy IDs; fixed audit path only; data never changed.'],
 'unresolved_failures':['GenZ Hybrid repeated recall0/7; no improvement claim.','REAL0/200, human0.','Candidate not trained: no CUDA/matching resource receipt.'],
 'test_privacy':json.loads((out/'e2e_v2/log-privacy.json').read_text(encoding='utf-8')),
 'cleanup':json.loads((out/'e2e_v2/cleanup.json').read_text(encoding='utf-8'))}
assert verification['cleanup']['owned_processes_exited'] and not verification['test_privacy']['sensitive_markers_found_in']
(out/'session_verification.json').write_text(json.dumps(verification,indent=2)+'\n',encoding='utf-8')
# Inventory before concluding T033, allowing reference validation on real existing files.
paths=[R/'AGENTS.md',R/'.agents/skills/shieldvi-ai-upgrade/SKILL.md',R/'tasks/TASK_ORDER.md',R/'tasks/moderation-ai/TASK_ORDER_AI.md',R/'tasks/AUTO_PROGRESS.md',
 R/'scripts/synthetic_data/genz.py',R/'scripts/synthetic_data/pipeline.py',R/'scripts/generate_genz_dataset.py',R/'scripts/prepare_t029_training.py',R/'scripts/train_t029_candidate.py',R/'scripts/evaluate_genz_development.py',R/'scripts/evaluate_regression_ablation.py',R/'scripts/run_ai_update_e2e.py',R/'tests/test_genz_v2.py',R/'tests/test_upgrade_workflow.py',R/'services/moderation-ai/app/model_registry.py',R/'apps/moderation-web/tests/seed_demo.py',R/'notebooks/T029_Train_Candidate_Prepared.ipynb',R/'configs/t029_genz500_candidate.json',R/'configs/model_registry.local.json',
 R/'datasets/synthetic_conversations/genz_v2/dataset_manifest.json',R/'datasets/synthetic_conversations/genz_v2/development_lock.json',R/'datasets/synthetic_conversations/genz_v2/README.md',R/'datasets/synthetic_conversations/genz_v2/quality_report.md',R/'reports/ai_update/T029/genz500_prepared/manifest.json',R/'reports/ai_update/T029/genz500_preflight.json',out/'local_registry_smoke.json',out/'integrity_audit.json',out/'session_verification.json']
paths+=list((R/'scripts/synthetic_data/genz_catalogue').glob('*.txt'))
paths+=list((R/'reports/ai_update/T030/genz500').glob('*.*'))+list((R/'reports/ai_update/T030/regression_ablation').glob('*.*'))
paths += [out/n for n in ('handoff_root_tests.txt','social_tests_service.txt','e2e_runner_release.txt','final_generation_idempotence.txt','build_social.txt','build_moderation.txt','build_dashboard.txt')]
paths += [out/'e2e_v2'/n for n in ('metrics.json','cleanup.json','log-privacy.json','process-health.json','browser-tests.txt')]
paths += list(D.glob('*.md'))
paths += [next((R/'tasks/moderation-ai').glob(tid+'-*.md')) for tid in ('T028','T029','T030','T031','T032','T033')]
def inventory():
 entries={str(p.relative_to(R)).replace('\\','/'):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(set(paths))}
 (D/'ARTIFACTS.json').write_text(json.dumps({'generated_for':'local handoff03Nov2026','self_hash_excluded':True,'model_weights_packaged':False,'files':entries,'dataset_thread_hashes':'datasets/synthetic_conversations/genz_v2/dataset_manifest.json','baseline_protected_hashes':'reports/ai_update/autonomous_20261103/integrity_audit.json'},indent=2)+'\n',encoding='utf-8')
inventory()
md_files=list(D.glob('*.md'))+[R/'AGENTS.md',R/'.agents/skills/shieldvi-ai-upgrade/SKILL.md',R/'tasks/TASK_ORDER.md',R/'tasks/moderation-ai/TASK_ORDER_AI.md']
md_files += [next((R/'tasks/moderation-ai').glob(tid+'-*.md')) for tid in ('T028','T029','T030','T031','T032','T033')]
missing=[];links=0
for p in md_files:
 for raw in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  target=raw.strip().split(' "',1)[0].strip('<>')
  if target.startswith(('http:','https:','mailto:','#')):continue
  target=unquote(target.split('#',1)[0]);links+=1
  if not (p.parent/target).resolve().exists():missing.append({'document':str(p.relative_to(R)),'target':target})
if missing:raise ValueError('Broken links: '+str(missing))
data=R/'datasets/synthetic_conversations/genz_v2';m=json.loads((data/'dataset_manifest.json').read_text(encoding='utf-8'));lock=json.loads((data/'development_lock.json').read_text(encoding='utf-8'))
assert sha(data/'dataset_manifest.json')==lock['dataset_manifest_sha256'] and sha(data/'development_threads.jsonl')==lock['development_sha256']
assert len(list((data/'threads').glob('*.json')))==500==len(list((data/'dashboard_threads').glob('*.json')))
assert all(sha(data/'threads'/(tid+'.json'))==expected for tid,expected in m['thread_sha256'].items())
assert all(sha(data/name)==expected for name,expected in m['output_sha256'].items())
# Completed batch manifests only; quality/rejected attempt files are not completed batches.
batches=[json.loads(p.read_text(encoding='utf-8')) for p in (data/'batches').glob('*.json') if p.stem.startswith(('import_','new_'))]
assert len(batches)==11 and sum(b['threads'] for b in batches)==500
assert len({tid for b in batches for tid in b['thread_ids']})==500
nb=json.loads((R/'notebooks/T029_Train_Candidate_Prepared.ipynb').read_text(encoding='utf-8'))
assert all(c.get('execution_count') is None and not c.get('outputs') for c in nb['cells'])
# Now evidence-only handoff meets its acceptance. Missing REAL/candidate are not marked complete.
p=next((R/'tasks/moderation-ai').glob('T033-*.md'));s=p.read_text(encoding='utf-8').replace('- **Status:** IN_PROGRESS','- **Status:** DONE',1)
s+='''\n### Evidence-only handoff completed03/11/2026\n\nDONE for the current user-authorized report of available evidence, not a declaration that REAL/train/release succeeded. `docs/ai-update/final-report/` includes19-part technical report, all data/provenance/AI-label limitations, architecture, true metrics/failures, error analysis, five synthetic demos, commands and hashed inventory. Local links and dataset/batch/hash/lock/notebook integrity verified. T030 research-evaluation and T032 verification complete independently; T028REAL, T029training and T031candidate activation remain BLOCKED.\n\nFinal root358PASS/1warning; Social177PASS/1warning; browser1PASS; webbuilds3PASS. RealV1 challenge and isolated registry/API fallback smokePASS; E2E fixture scores are explicitly distinguished. 31protected artifacts plus200legacythreads/2CSV unchanged, threshold0.41 unchanged, notebook unexecuted, candidateNOT_TRAINED/optimizer0. No production/default/DB/reset/push/deploy action. See reports/ai_update/autonomous_20261103/session_verification.json.\n''';p.write_text(s,encoding='utf-8')
state=json.loads((out/'progress.json').read_text(encoding='utf-8'));state['tasks'].update(synthetic_generation='DONE',T028='BLOCKED',T029='BLOCKED',T030='DONE',T031='BLOCKED',T032='DONE',T033='DONE')
state.update(next_action='No safe independent work remains in this request. Continue REAL only with legitimate source/contact/rights; train only with CUDA and matching resource/cost approval. Candidate activation follows measured evaluation and explicit release decision.',real_threads=0,synthetic_threads=500,synthetic_comments=5115,synthetic_batches=11,human_labels=0,synthetic_labels=5115,candidate='NOT_TRAINED',optimizer_steps=0,tests={'root_passed':358,'social_passed':177,'browser_passed':1,'builds_passed':3},handoff='docs/ai-update/final-report/README.md')
(out/'progress.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
for p in (R/'tasks/TASK_ORDER.md',R/'tasks/moderation-ai/TASK_ORDER_AI.md'):
 s=p.read_text(encoding='utf-8');lines=[]
 for line in s.splitlines():
  if line.startswith('| ') and ('**T033**' in line or '[T033](' in line):
   parts=line.split('|')
   if '**T033**' in line:parts[-3]=' DONE ';parts[-2]=' Evidence-only handoff,19phần/report/demo/hashes; REAL/candidate missing disclosed '
   else:parts[-2]=' DONE ';parts[-3]=' Handoff có bằng chứng và giới hạn; không chứng nhận release mới '
   line='|'.join(parts)
  lines.append(line)
 s='\n'.join(lines)+'\n'
 if 'TASK_ORDER_AI' in p.name:
  a=s.index('## Điểm tiếp tục hiện hành');s=s[:a]+'''## Điểm tiếp tục hiện hành —03/11/2026

REAL0/200, synthetic500/5115 (200legacy+300new), AIlabels5115/human0,11successfulbatch manifests. T030/T032/T033 DONE trong phạm vi nghiên cứu/tích hợp/bàn giao được giao. T028/T029/T031 BLOCKED: REAL/contact/rights/gold chưa có; CUDA/G3 chưa có; candidate chưa train/activation chưa duyệt. Không có task IN_PROGRESS còn dang dở trong chuỗi này.

Root358PASS, Social177PASS, browser1PASS,3webbuildsPASS, realV1 inference+API/fallback smokePASS. GenZ development MacroF1=.739974, target11/35coverage, repeated0/7; không claim cải thiện. B0–B3replay150fixture cũ riêng, không phải blindbenchmark. Baseline/default/0.41/heldouts/DB bất biến.

Việc cần để tiếp tục: nguồn REAL/contact hợp lệ và protocol nhãn thật; GPU/cost/config receipt cho candidate nếu muốn train. Không tự mở lại T021–T027 hay tune theo challenge đã xem. [Báo cáo](../../docs/ai-update/final-report/README.md), [tiến độ](../AUTO_PROGRESS.md).
'''
 else:
  s+='\n## Handoff cuối03/11/2026\n\nT030/T032/T033 DONE theo scope nghiên cứu/tích hợp/báo cáo được giao; T028/T029/T031 BLOCKED. REAL0/200, synthetic500/5115,AIlabels5115,human0;358root+177Social testsPASS,browser1PASS,3buildsPASS. CandidateNOT_TRAINED; không production/default/threshold/test/DB changes. Các mục scope cũ phía trên là lịch sử, xem TASK_ORDER_AI và final-report để tiếp tục.\n'
 p.write_text(s,encoding='utf-8')
with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as f:f.write('''\n## CURRENT HANDOFF —03/11/2026, request complete to safe execution limit\n\nDatasetB COMPLETE500threads/5115comments=200legacy2048+300new3067;11successfulbatch manifests; labels4667CLEAN/369TOXIC/79UNCERTAIN,5115AI/human0; technicalduplicates0, semantic/naturalness unverified. Train440threads4398binary rows (UNCERTAIN/reviewflags excluded), development60threads620comments; frozen lock intact. Preparation11340rows=6942ViCTSD+4398synthetic,38.78%; no exact/near held-out/challenge matches.\n\nT030/T032/T033 DONE (declared development evaluation, independent integration verification, evidence handoff). T028/T029/T031 BLOCKED (REAL0/contact/rights/gold; CUDA/G3; candidate nottrained/activation notapproved). No task IN_PROGRESS. No optimizer, external paidAPI, upload, checkpoint/threshold/test overwrite, liveDB/reset, push or deploy.31protected hashes and200legacythread/2CSV checksums unchanged.\n\nActual final tests: root358PASS/1warning (handoff_root_tests.txt); Social177PASS/1warning in servicevenv; browserE2E1PASS after canonical contract-path fix;3frontend buildsPASS isolated. RealV1 CPU development620commentsPASS at0.41; MacroF1=.739974 on617knownAI labels, target11/11emitted but24/35abstained; repeated0/7. B0–B3 replay150oldfixtures separate uses T020cachedrealV1, original per-textlex forB2 and byte-identical legacyengine; no fresh-gold claim. Fallback smoke realV1 and503→200PASS.\n\nResume root E:/lamDoAn/ShieldVI_V3_Hybrid_Review. Read reports/ai_update/autonomous_20261103/progress.json and docs/ai-update/final-report/README.md. Dataset datasets/synthetic_conversations/genz_v2; CLI scripts/generate_genz_dataset.py --through500 is idempotent. New config configs/t029_genz500_candidate.json, prepared reports/ai_update/T029/genz500_prepared; train runner default preflight refuses execution without exactGPU/cost receipt/CUDA. Notebook prepared for500 but unexecuted. Next requires legitimate REAL operator/source/rights and actual human protocol, or approved CUDA runtime for candidate. Do not substitute AI labels for realgold or alter frozen challenge after viewing errors.\n''')
# Rebuild hashes after final states are saved; inventory never hashes itself.
inventory()
validation={'status':'PASS','local_markdown_links_checked':links,'broken_links':missing,'thread_files':500,'dashboard_files':500,'successful_batch_manifests':11,'batch_thread_coverage':500,'frozen_dataset_and_challenge_unchanged':True,'original_notebook_execution_count':0,'task_states':state['tasks'],'human_labels':0,'real_threads':0,'synthetic_threads':500}
(out/'handoff_validation.json').write_text(json.dumps(validation,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','links_checked':links,'threads':500,'batches':11,'root_passed':358,'Social_passed':177,'DONE':['T030','T032','T033'],'BLOCKED':['T028','T029','T031']},ensure_ascii=True))
