"""Evidence-bound closure of independent safe scopes; real acceptance stays blocked."""
import json,re,sqlite3,sys,urllib.request
from pathlib import Path
from urllib.parse import unquote
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def log(p):
    b=Path(p).read_bytes();return b.decode('utf-16' if b[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
def unchanged(items):return all(Path(path).is_file() and file_sha(path)==sha for path,sha in items.items())
assert '574 passed' in log(P/'root_tests.log') and '177 passed' in log(P/'social_tests.log')
assert ' failed' not in log(P/'root_tests.log') and ' failed' not in log(P/'social_tests.log')
assert 'EXIT_CODE=0' in (P/'e2e/browser-tests.txt').read_text(encoding='utf-8')
assert read(P/'e2e/cleanup.json')['owned_processes_exited'] and read(P/'e2e/cleanup.json')['temporary_db_only']
assert not read(P/'e2e/log-privacy.json')['sensitive_markers_found_in']
assert read(P/'registry_exit.json')['native_exit_code']==0
registry=read(P/'registry_smoke.json');assert registry['status']=='PASS' and registry['default_before']==registry['default_after'] and registry['rollback_API']==200
assert read(P/'review_browser.json')['status']=='PASS' and read(P/'review_browser.json')['no_labels_submitted']
assert read(P/'live_verification.json')['status']=='PASS' and read(P/'live_verification.json')['raw_invariant']
metrics=read(P/'development_final/metrics.json');assert metrics['comments']==890 and not metrics['new_label_errors'] and metrics['raw_invariant']
lock=read(P/'before_lock.json');assert file_sha(P/'before.json')==lock['before_sha256']
assert unchanged({R/name:sha for name,sha in lock['reference_hashes'].items()})
assert file_sha(R/'reports/ai_update/context_recovery_20261103/score_cache.json')==lock['score_cache_sha256']
protected=read(R/'reports/ai_update/final/session_verification.json')['protected_hashes_unchanged'];assert unchanged(protected)
genz=R/'datasets/synthetic_conversations/genz_v2';m=read(genz/'dataset_manifest.json');frozen=read(genz/'development_lock.json')
assert unchanged({genz/'threads'/(tid+'.json'):sha for tid,sha in m['thread_sha256'].items()})
assert unchanged({genz/name:sha for name,sha in m['output_sha256'].items()})
assert file_sha(genz/'dataset_manifest.json')==frozen['dataset_manifest_sha256'] and file_sha(genz/'development_threads.jsonl')==frozen['development_sha256']
legacy=R/'datasets/synthetic_conversations';m=read(legacy/'manifest.json')
assert unchanged({legacy/'threads'/(tid+'.json'):sha for tid,sha in m['thread_checksums'].items()}) and unchanged({legacy/name:sha for name,sha in m['csv_checksums'].items()})
ctx=R/'datasets/fixtures/context_recovery_v1';m=read(ctx/'manifest.json')
assert unchanged({ctx/name:sha for name,sha in m['file_sha256'].items()}) and file_sha(ctx/'game_rank_30_reference.json')==m['user_reference_sha256']
for run in ('r03','r04','r05'):
    model=R/('models/candidates/T029_genz500_head_cpu_20261103_'+run)
    assert file_sha(model/'model.safetensors')==read(model/'training_report.json')['candidate_sha256']
for name in ('engine.py','predictor.py'):
    baseline=R/'reports/ai_update/camping_context_20261103/before_sources'/name
    if baseline.exists():assert file_sha(R/'services/moderation-ai/app'/name)==file_sha(baseline)
history=read(P/'historical_task_states.json')
for record in history:
    match=re.search(r'(?:Status|Trạng thái):\*\*\s*(DONE|IN_PROGRESS|TODO|BLOCKED|WAITING_APPROVAL)',(R/record['file']).read_text(encoding='utf-8'),re.I)
    assert match and match[1]==record['historical_status']
quality=read(P/'real_quality.json');assert quality['actual_threads']==0 and not quality['t028_real_acceptance_ready']
assert read(P/'collector_guard.json')['network_requests']==0 and read(P/'old_30_audit.json')['old_30_threads_313_comments']=='NOT_FOUND'
real=R/'datasets/real_conversations';db=real/'annotations/reviews.sqlite3'
if db.exists():
    with sqlite3.connect(db.resolve().as_uri()+'?mode=ro',uri=True) as connection:assert connection.execute('SELECT COUNT(*) FROM reviews').fetchone()[0]==0
preflight=read(P/'T029_preflight_current.json');assert preflight['status']=='BLOCKED' and not preflight['training_performed']
assert any('preparation only' in x for x in preflight['blockers'])
with urllib.request.urlopen('http://127.0.0.1:8010/api/readiness',timeout=5) as response:ready=json.load(response)
assert ready['candidate_threads']==0 and ready['manual_intake_pending']==0 and ready['collection_paused'] and not ready['model_predictions_enabled']
atomic_json(P/'integrity_audit.json',{'status':'PASS','original_protected_artifacts':len(protected),'historical_task_statuses_preserved':len(history),
 'V1_default_and_all_candidates_unchanged':True,'threshold':.41,'frozen_synthetic_text_and_labels_unchanged':True,
 'original_test_validation_and_live_SQLite_unchanged':True,'real_threads':0,'human_labels':0,'collector_network_requests':0,
 'training_performed':False,'production_changed':False,'manual_intake_not_counted_as_gold':True})

scope=read(R/'tasks/CURRENT_AI_SCOPE.json')
tasks={
 'T022':{'status':'DONE','scope':'Indirect attack/context development on frozen synthetic references'},
 'T024':{'status':'DONE','scope':'Target inference from actual attack clauses and available participant metadata'},
 'T025':{'status':'DONE','scope':'Repeated-evidence regression; missing targets still abstain, no promised perfect recall'},
 'T027':{'status':'DONE','scope':'Source/inventory audit, paused collector guard, anonymized quarantine and human review preparation'},
 'T028':{'status':'BLOCKED','scope':'Independent real200 cohort','historical_synthetic_status':'DONE','real_threads':0,'human_labels':0,
    'missing':['200 permitted/source-verifiable real threads','manual Round1/Round2 by same human','privacy/leakage checks and locked snapshot']},
 'T029':{'status':'BLOCKED','scope':'New training','preparation_status':'DONE','prepared_rows':11340,'training_performed':False,
    'dependencies':['T028 real criteria','new explicit matching resource/config approval'],'blockers':preflight['blockers']},
 'T030':{'status':'DONE','scope':'Synthetic development evaluation tooling and before/after','real_world_metrics':'BLOCKED'},
 'T031':{'status':'DONE','scope':'Actual local registry/shadow/fallback/rollback mechanics using existing candidate','promotion':'NOT_AUTHORIZED'},
 'T032':{'status':'DONE','scope':'574root/177Social regressions and isolated5process integration E2E'},
 'T033':{'status':'DONE','scope':'Provisional technical report with missing evidence explicit','real_world_conclusions':'BLOCKED'}}
scope.update(current_tasks=tasks,training_allowed_this_session=False,real_world_metrics_available=False,remaining_ready_work='No new ready task in requested scope; real data/labels and training approval remain unmet.')
scope['T029'].update(preparation='DONE',new_training='BLOCKED')
scope['T030'].update(development='DONE',real_world_metrics='BLOCKED');scope['T031']['local_registry_rollback']='DONE'
scope['T032']['safe_integration_tests']='DONE';scope['T033']['provisional_report']='DONE'
atomic_json(R/'tasks/CURRENT_AI_SCOPE.json',scope)

report=R/'docs/ai-update/final-report/INDEPENDENT_READINESS.md'
a,b=metrics['classification']['before'],metrics['classification']['after'];ga,gb=metrics['grounding']['before'],metrics['grounding']['after']
lines=['# Independent readiness — safe development and real-data blockers','',
 '## Current authority and task scopes','',
 'Latest PartsA/B/C and follow-up restore real200/human-review criteria for T028. Historical27task DONE records, including the earlier synthetic-only T028 and bounded CPU experiments, are preserved; they do not fulfill the newly requested real acceptance. Current criteria are machine-readable in [CURRENT_AI_SCOPE](../../../tasks/CURRENT_AI_SCOPE.json). No new training, source scraping, model promotion or production deployment was performed.',
 '', '| Task | Current requested scope | Status |','|---|---|---|']
for tid,value in tasks.items():lines.append(f"| {tid} | {value['scope']} | {value['status']} |")
lines+=['', 'Eight safe task scopes completed; T028real and T029training remain BLOCKED. T029preparation is complete separately. T030real-world metrics and T033real-world conclusions remain unavailable. Local T031 mechanics use the already-existing r05 artifact, not a newly trained candidate; that model remains rejected for promotion.',
 '', '## Part A — paired synthetic development','',
 'Rules now recognize bounded indirect capability/body/voice disparagement, while checking negation, quotations, reporting and fresh attacks after apology. Available participant IDs help recognize a named addressee only when present in an attack clause. Target-v4 excludes background names from the target set and retains abstention for root attacks without addressee metadata. No target is invented from later participants or every reply.',
 '', 'One shipping reference gains a supported two-turn actor→target chain after its earlier personal insult is recognized; GAME/camping exact4attack chains and recovery/apology exclusions remain intact. Repeated-v4 stays advisory and policy is never executed.',
 '', 'Inputs:890already-viewed synthetic/development comments,886known binary references;4UNCERTAIN references excluded and disclosed. Aggregate scores reuse the identical actual original-V1 CPU cache. New code was selected on development, not a blind benchmark. No real-world metric or human-gold claim.',
 '', '| Metric | Before | After |','|---|---:|---:|',
 f"| FP / FN | {a['fp']} / {a['fn']} | {b['fp']} / {b['fn']} |",
 f"| Macro-F1 | {a['macro_f1']:.6f} | {b['macro_f1']:.6f} |",
 f"| Toxic precision / recall | {a['toxic_precision']:.4f} / {a['toxic_recall']:.4f} | {b['toxic_precision']:.4f} / {b['toxic_recall']:.4f} |",
 f"| Grounded targets correct / reference attacks | {ga['target_correct']} / {ga['reference_attacks']} | {gb['target_correct']} / {gb['reference_attacks']} |",
 f"| Target precision / recall | {ga['target_precision']:.4f} / {ga['target_recall']:.4f} | {gb['target_precision']:.4f} / {gb['target_recall']:.4f} |",
 f"| Repeated TP / FP / FN | {ga['repeated']['tp']} / {ga['repeated']['fp']} / {ga['repeated']['fn']} | {gb['repeated']['tp']} / {gb['repeated']['fp']} / {gb['repeated']['fn']} |",
 f"| Repeated F1 | {ga['repeated']['f1']:.6f} | {gb['repeated']['f1']:.6f} |",
 '', 'Zero new label regressions. Remaining18FP/6FN,20target abstentions on reference attacks and7missed repeated events are preserved in the output; no expected labels were changed. Grounding references cover797known comments, omitting three legacy threads without target truth. Abstention counts as a miss in class F1, not silently dropped. Distinct event timestamps are normalized to UTC.',
 '', '[Full before/after, groups and remaining errors](../../../reports/ai_update/independent_readiness_20261103/development_final/metrics.json) · [Unit regression](../../../tests/test_indirect_scope_regression.py).',
 '', '## Part B — real inventory, rights and collection','',
 'Old30threads/313comments: **NOT_FOUND** in the current repository inventory across datasets/, fixtures/if present, tests/, docs/ and related manifests. Documentary mentions of a Wikipedia pilot are not corpus evidence. Known100/200/500synthetic sets and5regression fixtures are not reclassified as real. Inventory1478structured files is retained; relevant collection/manifest structures were checked, flat classification files were not combined into invented conversations.',
 '', 'Actual admitted real threads: **0/200**, comments0, manual human labels0. Six source candidates were researched using primary metadata/docs; none was admitted. No corpus download or live collector request was made. Wikimedia is explicitly PAUSED by user, enforced before network-client creation even if a stale contact variable exists. No fake email/account/URL or browser User-Agent was used; no further contact/path question is required this session.',
 '', '| Source | Observation and current disposition |','|---|---|',
 '| Wikimedia | Existing CC-BY-SA metadata does not override the user pause; collector must recheck rights receipt before any future content acquisition. [API etiquette](https://www.mediawiki.org/wiki/API:Etiquette), [official User-Agent policy](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy/en). |',
 '| ViHOS | [Official repository](https://github.com/phusroyal/ViHOS) and [MIT repository license](https://raw.githubusercontent.com/phusroyal/ViHOS/master/LICENSE) inspected. Flat span/comment data is not a source-verified multi-party cohort; repository software licensing is not assumed to resolve every underlying comment right. |',
 '| ViHSD | [Official repository](https://github.com/sonlam1102/vihsd) describes comment classification; no clear dataset-use grant was located in inspected pages. Hold for rights and thread/provenance requirements. |',
 '| ViCTSD | [Official repository](https://github.com/tarudesu/ViCTSD) plus local manifest: existing user-copy license not reverified; already a supervised classification source, not a new independent thread cohort. |',
 '| ViLexNorm | [Official repository](https://github.com/ngxtnhi/ViLexNorm), local README/license hashes and CC-BY-NC-SA metadata. Normalization pairs already used in development do not provide the requested source thread graph. |',
 '| mDIA | [Original repository](https://github.com/DoctorDream/mDIA) and [SEACrowd card](https://huggingface.co/datasets/SEACrowd/mdia/blob/main/README.md). Wrapper CC-BY declaration/paper citation do not establish an inspected upstream grant plus complete10–30turn provenance; parent-response pairs were not stitched into invented threads. |',
 '', 'These are acquisition eligibility findings, not a legal assurance. [Inventory/audit](../../../reports/ai_update/independent_readiness_20261103/old_30_audit.json) · [Source research metadata](../../../reports/ai_update/independent_readiness_20261103/source_candidates.json).',
 '', '### Future human intake and review','',
 'The blind UI is running at http://127.0.0.1:8010/. The new JSON intake stores an anonymized, unverified local quarantine with source URL/license claim/evidence URL, source timestamp/null and parent graph. It preserves missing metadata rather than inventing it, rejects preloaded labels, and never counts a staged item as real/evaluation/training eligible. A verified source adapter/rights receipt, privacy and leakage checks are still needed before admission; a user-uploaded license claim is not verification.',
 '', 'Reviewer entry and JSON input were checked in Chrome; no labels/data were submitted to the actual dataset. Existing labeling supports the same human across Round1/Round2 with revision history; stale Round2 returns to the queue after Round1 changes. This is not inter-annotator agreement. No second reviewer is simulated. The evaluation lock remains unavailable for the empty cohort.',
 '', 'Leakage exclusion now binds GenZ500train/development and12context fixtures as well as prior references/ViCTSD; source hashes and whole-thread near checks remain mandatory. Metadata changed, frozen text/labels did not. Exact comment hashes use>=80characters and do not certify absence of all paraphrases. [Manual intake template](../../../templates/T028_MANUAL_INTAKE.example.json) · [Real-data instructions](../../../datasets/real_conversations/README.md).',
 '', '## Part C — preparation and safe integration','',
 '- T029: new unapproved real-protocol config and11340preparedrows exist. Actual preflight blocks on current no-training scope, missing real verified cohort, matching approval and CUDA. Gate also requires real acceptance with>=200threads; preparation did not create a checkpoint or optimizer.',
 '- T030: reproducible synthetic metric CLI, frozen before state, per-group FP/FN/MacroF1 and target/repeated support. No historical classification test or real-cohort metric was scored.',
 '- T031: actual existingr05 shadow load, implicit-selection refusal, deliberate candidate-loader fault with actual V1fallback, isolated ASGI200→503→200rollback; default path unchanged. Scores are mechanics probes, not a performance claim.',
 '- T032:574root and177Social testsPASS; existing5process E2E/browserPASS with fixture AI and disposable SQLite/accounts. Fixture integration is explicitly not real model accuracy. Owned test processes exited; five logs had no sensitive markers. Separate live V1.1/r05 smoke on5syntheticthreads/90comments each confirmed raw/legacy invariants and indirect targets/shipping/GAME/camping chains after local code reload. No production model switch.',
 '- T033: this provisional report and current scope ledger preserve missing evidence rather than marking real acceptance DONE.',
 '', '## Validation, blockers and handoff','',
 'Final:574rootPASS/177SocialPASS/E2EbrowserPASS/reviewUIbrowserPASS/registryPASS/live-smokePASS. Initial new-regression red failures were retained; one named-target test required the participant metadata supplied in the real pipeline, without changing its expected target. Browser smoke initially lacked the bundled browser and was rerun with installed Chrome, without download. Registry warning on PowerShell stderr was resolved by recording the actual Python exit0; warning logs retained.',
 '', '31protected originals, V1/defaultV1.1/r03/r04/r05 checkpoints, frozen200/500synthetic data/labels/splits, context/user references, original validation/test and live SQLite unchanged. All27historical task status lines unchanged. No training, paid/external upload, destructive migration, push, production deployment or auto-hide.',
 '', 'Next: when actual permitted source material is available, use the local intake and verification workflow, then personally perform Round1 and Round2. T028real remains BLOCKED until the cohort/rights/human-review/lock criteria pass; T029new training additionally needs explicit approval. Do not ask again for the declined Wikimedia contact or missing old path in this session.',
 '', '[Current progress](../../../tasks/AUTO_PROGRESS.md) · [Current scope](../../../tasks/CURRENT_AI_SCOPE.json) · [Evidence](../../../reports/ai_update/independent_readiness_20261103/progress.json).']
report.write_text('\n'.join(lines)+'\n',encoding='utf-8')

data_notice='''# Current T028 real-data readiness — BLOCKED

Latest user request restores independent real200/same-human two-round criteria. Valid real threads0/200, human labels0. Earlier synthetic DONE is preserved historical scope, not completion of these criteria. Wikimedia collector is PAUSED by explicit user request; do not run the historical collection commands below or ask for contact/path again this session.

## Local manual preparation

Open http://127.0.0.1:8010/ for blind human review. “Nhập JSON nguồn” uses [this incomplete template](../../templates/T028_MANUAL_INTAKE.example.json): fill actual source URL/license evidence and unchanged comments/source IDs/parents/timestamps; leave genuinely missing metadata null. It is deliberately rejected until required blank fields are filled. Do not fill invented source/user/time values or attach synthetic labels.

Import only creates an anonymized UNVERIFIED quarantine under anonymized/manual_inbox/. It does not create source permission, human gold, valid real thread counts or training/evaluation eligibility. A supported source adapter with verified rights/source receipt, privacy and leakage checks must admit a thread before labeling. Future accepted threads can be manually labeled Round1 and Round2 by the same reviewer ID; changes have revision history and stale second rounds require re-confirmation. No model predictions or second reviewer are involved.

Current blockers and test evidence: [independent readiness report](../../docs/ai-update/final-report/INDEPENDENT_READINESS.md). No new training or production change is authorized. The previous instructions below are historical/reference details; collection remains paused until an explicit future policy change.

---

'''
path=real/'README.md';path.write_text(data_notice+path.read_text(encoding='utf-8'),encoding='utf-8')
for rel in ('docs/ai-update/02_ANNOTATION_GUIDE.md','docs/ai-update/03_EXPERIMENT_PLAN.md','docs/ai-update/05_RELEASE_GATES.md'):
    path=R/rel;path.write_text('> CURRENT authority: latest PartsA/B/C restore T028-real200 + same human Round1/Round2, currently BLOCKED. Historical synthetic/CPU DONE is preserved, not real acceptance. Wikimedia paused/no more contact questions. No new training or production activation. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/INDEPENDENT_READINESS.md; older scope notices below are historical.\n\n'+path.read_text(encoding='utf-8'),encoding='utf-8')
with (R/'docs/ai-update/04_API_VERSIONING.md').open('a',encoding='utf-8') as f:
    f.write('\n\n## context-v4 / target-v4 — additive clause grounding\n\nContextSignals.attack_clause_spans is optional for older responses and uses half-open coordinates in normalized folded context text, not original text offsets. Participant metadata only grounds names literally present in an asserted attack clause; background/quoted names do not automatically become targets. Missing addressee metadata still abstains. Raw fields, legacy API and Social policy semantics are unchanged.\n')
summary='\n\n## CURRENT independent-readiness session — safe scopes complete, real criteria BLOCKED\n\n'
summary+='Current task criteria (historical DONE status lines remain untouched):\n\n| Task | Scoped status |\n|---|---|\n'
for tid,value in tasks.items():summary+=f"| {tid} | {value['status']} — {value['scope']} |\n"
summary+='\n8safe scopesDONE; T028real/T029trainingBLOCKED. T029preparationDONE, no training. Existing synthetic T028DONE and completed CPU runs remain historical, not real evidence. Data valid0/200/human labels0; old30/313NOT_FOUND;6source options audited/no corpus admitted; collectorPAUSED/0networkrequests/no more contact/path questions.\n\n'
summary+='Synthetic890/known886 only: FP20→18,FN9→6,MacroF1.889700→.909296; target30→34/54correct(P1.0,R.5556→.6296); repeatedTP2→3/10,FP0,FN8→7. No new label errors;18FP/6FN/20targetabstentions/7repeatedmisses remain. No human-gold/real-world claims.\n\n'
summary+='574rootPASS/177SocialPASS,5processfixtureE2E/browserPASS(tempSQLite/cleanup/privacy), real-reviewChromePASS(no submissions), actualregistryshadow/fallback/rollbackPASS(nativeexit0), actualV1.1/r05live5threads/90comments each rawinvariantPASS. Current codecontext-v4/target-v4/repeated-v4; default/V1/0.41/checkpoints/source labels/test/liveDB unchanged.\n\n'
summary+='Files: context_signals.py,target_signals.py,signal_engine.py,contractschema; real_dataset collector/core/store/intake/leakage/review_app/validation/UI; reusable evaluate_synthetic_signals.py, training preflight guards/config, local registry/config, tests/template/docs. Evidence reports/ai_update/independent_readiness_20261103/; report docs/ai-update/final-report/INDEPENDENT_READINESS.md. Current criteria tasks/CURRENT_AI_SCOPE.json. Human UI8010; demo8020V1.1/8021experimentalr05 reloaded code only. Current PID states in this evidence directory; prior PID files superseded.\n\n'
summary+='Next only when real permitted material exists: source/privacy/leakage verification and supported adapter, then same-human Round1/Round2 and evaluation lock. No new training without all prerequisites and explicit approval. No push/deploy/production changes; no other ready requested task remains.\n'
for rel in ('tasks/AUTO_PROGRESS.md','tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md'):
    with (R/rel).open('a',encoding='utf-8') as f:f.write(summary)
for tid in tasks:
    path=next((R/'tasks/moderation-ai').glob(tid+'-*.md'))
    with path.open('a',encoding='utf-8') as f:f.write('\n\n## Latest independent-readiness criteria\n\nHistorical status/evidence above preserved. Current scoped status: **'+tasks[tid]['status']+'** — '+tasks[tid]['scope']+'. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/INDEPENDENT_READINESS.md. New criteria never turn missing real/human evidence into DONE. Evidence:574root/177Social/E2E/UI/registry/live smoke PASS; valid real0, no new training.\n')
readme=R/'docs/ai-update/final-report/README.md';readme.write_text('Current authoritative follow-up: [Independent readiness and real blockers](INDEPENDENT_READINESS.md). Older completion reports below retain their historical scopes.\n\n'+readme.read_text(encoding='utf-8'),encoding='utf-8')
for name in ('demo_server_state.json','review_server_state.json'):
    path=P/name;value=read(path);rows=value if isinstance(value,list) else [value]
    for row in rows:
        row['status']='READY'
        if 'stderr' in row:
            m=re.search(r'Started server process \[(\d+)\]',Path(row['stderr']).read_text(encoding='utf-8',errors='replace'))
            if m:row['server_process_id']=int(m[1])
    atomic_json(path,rows if isinstance(value,list) else rows[0])
atomic_json(P/'progress.json',{'status':'COMPLETE_SAFE_SCOPES_REAL_BLOCKED','completed_task_scopes':8,'blocked_current_tasks':['T028 real acceptance','T029 new training'],
 'historical_task_statuses_preserved':len(history),'root_tests_passed':574,'social_tests_passed':177,'integration_browser_pass':True,'review_browser_pass':True,
 'synthetic_metrics':metrics['classification'],'grounding_metrics':metrics['grounding'],'real_valid_threads':0,'human_labels':0,'old30_313':'NOT_FOUND',
 'training_performed':False,'production_changed':False,'collector_paused':True,'report':report.relative_to(R).as_posix(),
 'next':'Real source/permission/privacy verification, same-human2rounds, lock; training remains gated. No more contact/path questions this session.'})
files=[report,R/'tasks/CURRENT_AI_SCOPE.json',R/'AGENTS.md',real/'README.md',real/'manifests/collection_policy.json',real/'manifests/development_exclusions.json',R/'templates/T028_MANUAL_INTAKE.example.json',R/'contracts/analysis_response_v2.schema.json']
files += [R/'services/moderation-ai/app'/name for name in ('context_signals.py','target_signals.py','signal_engine.py')]
files += [R/'scripts/real_dataset'/name for name in ('collector.py','core.py','store.py','intake.py','leakage.py','review_app.py','validation.py','review_ui/index.html','review_ui/app.js')]
files += [R/'scripts'/name for name in ('train_t029_candidate.py','evaluate_synthetic_signals.py')]
files += [R/'tests'/name for name in ('test_indirect_scope_regression.py','test_real_intake_readiness.py','test_synthetic_signal_metrics.py')]
files += [R/'configs'/name for name in ('t029_real_independent_preparation.json','model_registry.independent_readiness.local.json')]
files += [p for p in P.rglob('*') if p.is_file() and p.name!='ARTIFACTS.json' and not any(part in ('temporary','__pycache__') for part in p.relative_to(P).parts)]
broken=[]
for path in (report,real/'README.md'):
    for raw in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
        raw=raw.strip('<>').split('#',1)[0]
        if raw and not raw.startswith(('http:','https:','mailto:')) and not (path.parent/unquote(raw)).resolve().exists():broken.append((str(path),raw))
assert not broken,broken
atomic_json(P/'ARTIFACTS.json',{'models_not_packaged':True,'broken_links':broken,'files':{path.relative_to(R).as_posix():{'sha256':file_sha(path),'bytes':path.stat().st_size} for path in sorted(set(files))}})
print(json.dumps({'status':'COMPLETE_SAFE_SCOPES_REAL_BLOCKED','DONE_scopes':8,'BLOCKED':['T028','T029 training'],'root_PASS':574,'social_PASS':177,
 'real_valid_threads':0,'human_labels':0,'old30':'NOT_FOUND','training_performed':False}))
