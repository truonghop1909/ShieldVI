"""Check real evidence and close the bounded follow-up, keeping negative history."""
import hashlib,json,re,sys
from pathlib import Path
from urllib.parse import unquote
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from refine_model import file_hash
from synthetic_data.pipeline import atomic_json

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def matches(paths):return all(Path(path).is_file() and file_hash(path)==sha for path,sha in paths.items())
cfg=read(R/'configs/t029_genz500_cpu_head_r04.json');model=Path(cfg['output_dir'])
training=read(model/'training_report.json');review=read(P/'validation_review.json')
b=(P/'root_tests.log').read_bytes();log=b.decode('utf-16' if b[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
passes=re.search(r'(\d+) passed',log)
assert passes and int(passes[1])>=448 and ' failed' not in log and ' errors' not in log
assert training['training_performed'] and training['optimizer_steps']>0 and training['encoder_unchanged'] and training['baseline_unchanged'] and training['source_hashes_unchanged']
assert file_hash(model/'model.safetensors')==training['candidate_sha256'] and review['training_report_sha256']==file_hash(model/'training_report.json')
assert not review['test_scored'] and not review['promotion_allowed'] and not review['production_changed']

protected=read(R/'reports/ai_update/final/session_verification.json')['protected_hashes_unchanged']
assert matches(protected)
legacy=R/'datasets/synthetic_conversations';m=read(legacy/'manifest.json')
assert matches({legacy/'threads'/(tid+'.json'):sha for tid,sha in m['thread_checksums'].items()})
assert matches({legacy/name:sha for name,sha in m['csv_checksums'].items()})
genz=legacy/'genz_v2';m=read(genz/'dataset_manifest.json');lock=read(genz/'development_lock.json')
assert file_hash(genz/'dataset_manifest.json')==lock['dataset_manifest_sha256'] and file_hash(genz/'development_threads.jsonl')==lock['development_sha256']
assert matches({genz/'threads'/(tid+'.json'):sha for tid,sha in m['thread_sha256'].items()})
assert matches({genz/name:sha for name,sha in m['output_sha256'].items()})
recovery=R/'datasets/fixtures/context_recovery_v1';m=read(recovery/'manifest.json');before=read(R/'reports/ai_update/context_recovery_20261103/before_lock.json')
assert file_hash(recovery/'manifest.json')==before['new_dataset_manifest_sha256']
assert file_hash(recovery/'game_rank_30_reference.json')==m['user_reference_sha256']
assert matches({recovery/name:sha for name,sha in m['file_sha256'].items()})
prepared=read(P/'prepared/manifest.json')
assert matches({source['path']:source['sha256'] for source in prepared['sources'].values()})
history=read(R/'reports/ai_update/all_tasks_cpu_20261103/ARTIFACTS.json')['files']
intentional={'tasks/moderation-ai/T029-optional-train-candidate-visobert-on-colab.md','tasks/moderation-ai/T031-optional-model-registry-shadow-and-rollbac.md',
 'tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md','tasks/AUTO_PROGRESS.md','docs/ai-update/05_RELEASE_GATES.md'}
assert matches({R/name:entry['sha256'] for name,entry in history.items() if name not in intentional})
prior_cfg=read(R/'configs/t029_genz500_cpu_head.json');prior_model=Path(prior_cfg['output_dir'])
prior_training=read(prior_model/'training_report.json')
assert file_hash(prior_model/'model.safetensors')==prior_training['candidate_sha256']
decl=read(P/'predeclared_experiment.json')
for key,path in {
 'config_sha256':R/'configs/t029_genz500_cpu_head_r04.json','prepared_manifest_sha256':P/'prepared/manifest.json',
 'original_protocol_sha256':R/'reports/ai_update/all_tasks_cpu_20261103/evaluation_protocol.json',
 'validation_references_sha256':P/'validation_references.json','training_implementation_sha256':R/'scripts/t029_cpu_head.py',
 'review_implementation_sha256':R/'scripts/review_t029_validation.py'}.items():assert file_hash(path)==decl[key]

integrity={'status':'PASS','protected_original_hashes':len(protected),'legacy200_and_GenZ500_unchanged':True,
 'context_recovery12_and_user_reference_unchanged':True,'original_validation_test_and_SQLite_unchanged':True,
 'source_and_encoder_unchanged':True,'original_gates_unchanged':True,'predeclared_recipe_unchanged':True,'production_changed':False,
 'r03_candidate_and_negative_evidence_unchanged':True,'historical_artifact_files_unchanged':len(history)-len(intentional),
 'intentional_historical_document_updates':sorted(intentional)}
atomic_json(P/'integrity_audit.json',integrity)
refs=review['reference_validation'];metrics=review['candidate_validation']
verdict=review['decision'];tests=int(passes[1])
report_path=R/'docs/ai-update/final-report/CANDIDATE_REVISION_R04.md'
lines=['# Rework after candidate rejection — r04','',
 '## Scope and decision','',
 'The previous task review completed, but r03 promotion was rejected. This follow-up revises the research recipe, not the acceptance gates or labels. The renewed user request authorizes continued local work; one bounded CPU classifier-head experiment was actually executed. Full encoder, paid GPU and production activation remain outside this execution.',
 '',f'**Decision: {verdict}.** Promotion remains disabled even if validation screening passes. Historical test was already inspected in r03; it was not rescored here. This is exploratory validation reuse, not new blind evidence.',
 '', '## Executed changes','',
 '- Lower synthetic sample weight0.5→0.1; lower learning rate3e-5→1e-5; increase original-head distillation0.5→1.0. No example-specific rule or annotation change.',
 '- Preserve11340trainingrows (6942ViCTSD+4398AI references) and2000validationrows. Weighted synthetic share of supervised loss is approximately24%→6%; physical data share stays38.78%. AI labels remain synthetic references.',
 f"- Actual {training['optimizer_steps']}optimizersteps, {len(training['epochs'])}epochs, {training['elapsed_seconds']:.2f}seconds; max4CPUthreads/900seconds/cost0. Encoder unchanged, reload probe error {training['reload_probe_max_error']}. Selected epoch {training['selected']['epoch']} by validation only.",
 '- Added reusable validation-only screening with both baseline comparisons, integrity checks, output overwrite refusal and no promotion permission. Corrected two stale REAL200/BLOCKED document banners while retaining their historical text.',
 '', '## Validation only — fixed threshold0.41','',
 '| Model | MacroF1 | Toxic precision | Toxic recall | TP/FP/TN/FN |',
 '|---|---:|---:|---:|---|']
for name,value in [*refs.items(),('r03_prior_candidate',read(R/'reports/ai_update/all_tasks_cpu_20261103/candidate_evaluation.json')['metrics']['ViCTSD_validation']['candidate_head_CPU']),('r04_candidate',metrics)]:
 lines.append(f"| {name} | {value['macro_f1']:.6f} | {value['toxic_precision']:.6f} | {value['toxic_recall']:.6f} | {value['tp']}/{value['fp']}/{value['tn']}/{value['fn']} |")
lines+=['', 'Unchanged screen: MacroF1 must improve by≥0.005 and toxic precision/recall must not fall, against both originalV1 and defaultV1.1. The existing no-new-synthetic-error gate is also retained; it was not reassessed for this recipe. Test/regression inference, API shadow and production rollout were not performed for r04. The prior r03 local smoke remains historical evidence, not r04 evidence.',
 '', '## Verification and files','',f'- Full root regression: **{tests}passed**, one known Starlette deprecation warning. Preflight40passed; initial sandbox temp-directory write failed, elevated rerun succeeded. No automatic approval rejection remained.',
 '- Integrity:31protectedhashes;200legacy+500GenZthreads, frozen development split,12contextthreads/userreference, original validation/test/checkpoints/default/SQLite unchanged. No train on test or new uploads/downloads.',
 '- Source: [validation reviewer](../../../scripts/review_t029_validation.py), [tests](../../../tests/test_t029_validation_review.py), [r04 config](../../../configs/t029_genz500_cpu_head_r04.json).',
 '- Evidence: [predeclared protocol](../../../reports/ai_update/candidate_revision_20261103/predeclared_experiment.json), [training report](../../../models/candidates/T029_genz500_head_cpu_20261103_r04/training_report.json), [validation review](../../../reports/ai_update/candidate_revision_20261103/validation_review.json), [integrity audit](../../../reports/ai_update/candidate_revision_20261103/integrity_audit.json).',
 '- Tracking: T029/T031 task files, TASK_ORDER_AI.md, TASK_ORDER.md and AUTO_PROGRESS.md updated with follow-up evidence. The27previously completed task states remain preserved.',
 '', '## Next action','',review['next_action'],
 'A quality failure is not resolved by rewriting release gates. Keep the approved default for the demo. Additional model research requires a separately declared experiment; paid/full-encoder GPU work and production activation require their existing approval.']
report_path.write_text('\n'.join(lines)+'\n',encoding='utf-8')
note=f'''\n\n## CURRENT FOLLOW-UP r04 — COMPLETE, promotion disabled\n\nActual bounded CPU follow-up completed: {training['optimizer_steps']}optimizersteps/{len(training['epochs'])}epochs/{training['elapsed_seconds']:.2f}s, encoderfrozen, newcheckpoint r04. ValidationMacroF1 original{refs['original_V1']['macro_f1']:.6f}/r03.753042/r04{metrics['macro_f1']:.6f}; toxicP{metrics['toxic_precision']:.6f}/R{metrics['toxic_recall']:.6f}. Decision **{verdict}**, unchanged original gates. No new test/challenge inference or promotion; historical evaluation is not freshblind. Prior27task DONE states preserved. Follow-up status COMPLETE for execution/review, not model acceptance.\n\nRoot{tests}PASS/1warning;40preflightPASS.31protectedhashes+all200/500source datasets+12contextfixtures/userreference/validation/test/SQLite/defaultV1.1 unchanged. No paidGPU/fullencodertraining/upload/download/push/deploy. Files: scripts/review_t029_validation.py, tests/test_t029_validation_review.py, configs/t029_genz500_cpu_head_r04.json; task/index/progress and3AI docs updated; newcandidate/reports separate.\n\nCurrent evidence reports/ai_update/candidate_revision_20261103/; report docs/ai-update/final-report/CANDIDATE_REVISION_R04.md. Resume from this section, not historical IN_PROGRESS/BLOCKED notes above. No remaining task ready in the27existing files; next: {review['next_action']}\n'''
tracking=['tasks/moderation-ai/T029-optional-train-candidate-visobert-on-colab.md','tasks/moderation-ai/T031-optional-model-registry-shadow-and-rollbac.md','tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md','tasks/AUTO_PROGRESS.md']
for name in tracking:
 with (R/name).open('a',encoding='utf-8') as f:f.write(note)
rows=[]
for path in sorted((R/'tasks').rglob('T[0-9][0-9][0-9]-*.md')):
 match=re.search(r'(?:Status|Trạng thái):\*\*\s*(DONE|IN_PROGRESS|TODO|BLOCKED|WAITING_APPROVAL|SKIPPED_APPROVED)',path.read_text(encoding='utf-8'),re.I)
 assert match,str(path)
 rows.append({'file':path.relative_to(R).as_posix(),'status':match[1]})
assert len(rows)==27 and all(v['status']=='DONE' for v in rows)
atomic_json(P/'task_inventory.json',rows)
atomic_json(P/'progress.json',{'status':'COMPLETE_BOUNDED_FOLLOWUP','existing_tasks':{'DONE':27,'BLOCKED':0,'WAITING_APPROVAL':0},
 'followup_execution':'COMPLETE','promotion_decision':verdict,'production_activation_allowed':False,
 'optimizer_steps':training['optimizer_steps'],'candidate_validation_macro_f1':metrics['macro_f1'],'test_scored':False,'root_tests_passed':tests,
 'next':review['next_action'],'report':report_path.relative_to(R).as_posix()})

files=[report_path,R/'scripts/review_t029_validation.py',R/'tests/test_t029_validation_review.py',R/'configs/t029_genz500_cpu_head_r04.json']
files += [R/name for name in tracking]+[R/'docs/ai-update'/name for name in ('02_ANNOTATION_GUIDE.md','03_EXPERIMENT_PLAN.md','05_RELEASE_GATES.md')]
files += [path for path in P.rglob('*') if path.is_file() and path.name!='ARTIFACTS.json']+[model/'training_report.json',model/'threshold_config.json']
broken=[]
for path in files:
 if path.suffix!='.md':continue
 for raw in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
  raw=raw.strip('<>').split('#',1)[0]
  if raw and not raw.startswith(('http:','https:','mailto:')) and not (path.parent/unquote(raw)).resolve().exists():broken.append((str(path),raw))
assert not broken,broken
atomic_json(P/'ARTIFACTS.json',{'models_not_packaged':True,'candidate_weights_sha256':training['candidate_sha256'],'broken_links':broken,
 'files':{path.relative_to(R).as_posix():{'sha256':file_hash(path),'bytes':path.stat().st_size} for path in sorted(set(files))}})
print(json.dumps({'status':'COMPLETE','decision':verdict,'root_passed':tests,'validation_macro_f1':metrics['macro_f1'],'protected_hashes':len(protected),'tasks_DONE':27}))
