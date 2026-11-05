"""Seal verified follow-up evidence; no training, scoring or activation."""
import json,re,sys
from pathlib import Path
from collections import defaultdict
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
from synthetic_data.experiment import verify_view
from evaluate_synthetic_signals import target_truth
from progress_update import update

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def log(p):
    b=Path(p).read_bytes();return b.decode('utf-16' if b[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
assert '610 passed, 1 warning' in log(P/'root_tests_verified.log')
assert '177 passed' in log(P/'social_tests_fixed.log')
assert '1 passed' in (P/'e2e/browser-tests.txt').read_text(encoding='utf-8')
registry=read(P/'registry_smoke.json');assert registry['status']=='PASS' and not registry['production_changed']
assert read(P/'e2e/cleanup.json')['owned_processes_exited']
assert not read(P/'e2e/log-privacy.json')['sensitive_markers_found_in']
assert read(P/'e2e/metrics.json')['final_worker_stats']['retry_attempts']==2
lock=read(P/'frozen_rule_lock.json')
assert all(file_sha(R/'services/moderation-ai/app'/name)==h for name,h in lock['rule_sha256'].items())
verified={}
for name,h in read(R/'reports/ai_update/synthetic_experiment_r06_20261103/integrity.json')['protected_hashes'].items():
    assert file_sha(Path(name))==h,name;verified[name]=h
manifest,_,_=verify_view(R/'datasets/synthetic_genz',R/'datasets/synthetic_conversations/genz_v2')
for name,h in read(P/'before_lock.json')['sources'].items():assert file_sha(P/'before_sources'/name)==h
history=read(R/'reports/ai_update/independent_readiness_20261103/historical_task_states.json')
for record in history:
    match=re.search(r'(?:Status|Trạng thái):\*\*\s*(DONE|IN_PROGRESS|TODO|BLOCKED|WAITING_APPROVAL)',(R/record['file']).read_text(encoding='utf-8'),re.I)
    assert match and match.group(1)==record['historical_status']
evaluation=read(P/'evaluation/evaluation.json');outputs=read(P/'evaluation/outputs.json');development=read(P/'development_verified/metrics.json')
previous=read(R/'reports/ai_update/synthetic_experiment_r06_20261103/evaluation/comparison.json')
for model,results in previous['metrics'].items():
    for split in ('synthetic_validation','synthetic_challenge'):
        raw=evaluation['metrics'][model]['raw'][split]
        assert all(abs(raw[k]-results[split]['raw'][k])<1e-10 for k in ('macro_f1','tp','fp','tn','fn','toxic_precision','toxic_recall'))
truth=target_truth()
for path in (R/'datasets/fixtures/repeated_holdout_20261103').glob('REP_FRESH_*.json'):
    t=read(path)
    for c in t['comments']:
        a=c['annotation'];truth[(t['thread_id'],c['comment_id'])]={'label':a['label'],'actor':c['user_id'],'target':a['directed_at_user_id'],'time':c['timestamp'],'text':c['text']}
def missing_events(items):
    tids={x['output']['thread_id'] for x in items};pairs=defaultdict(set)
    for (tid,_),v in truth.items():
        if tid in tids and v['label']=='TOXIC' and v['target']:pairs[(tid,v['actor'],v['target'])].add(datetime.fromisoformat(v['time'].replace('Z','+00:00')).astimezone(timezone.utc))
    expected={k for k,times in pairs.items() if len(times)>=2}
    actual={(x['output']['thread_id'],e['actor_user_id'],e['target_user_id']) for x in items for e in x['output']['evidence']}
    return sorted(expected-actual)
fresh_after=[x for x in outputs['r06']['after'] if x['split']=='fresh_synthetic_challenge']
fresh_missing=missing_events(fresh_after);broad_missing=missing_events(read(P/'development_verified/after.json'))
assert len(fresh_missing)==2
changes={};errors={}
for name,variants in outputs.items():
    changes[name]=[];errors[name]=[]
    for before,after in zip(variants['before'],variants['after']):
        tid=after['output']['thread_id']
        # Build the exact frozen binary references for old/new datasets.
        if tid.startswith('REP_FRESH_'):t=read(R/'datasets/fixtures/repeated_holdout_20261103'/(tid+'.json'))
        else:t=read(R/'datasets/synthetic_genz/threads'/(tid+'.json'))
        refs={c['comment_id']:c.get('annotation',c)['label'] for c in t['comments']}
        texts={c['comment_id']:c['text'] for c in t['comments']}
        for a,b in zip(before['output']['comments'],after['output']['comments']):
            ref=refs[b['comment_id']];old=a['moderation_assessment']['label'];new=b['moderation_assessment']['label']
            row={'thread_id':tid,'comment_id':b['comment_id'],'reference':ref,'text':texts[b['comment_id']],
                'before':old,'after':new,'raw_score':b['toxicity_score'],'label_source':'synthetic_reference','human_gold':False}
            if old!=new:changes[name].append(row)
            if ref!='UNCERTAIN' and ref!=new:errors[name].append(row)
atomic_json(P/'error_analysis.json',{'changed_labels':changes,'remaining_errors':errors,'fresh_missing_events':fresh_missing,
    'broad_missing_events':broad_missing,'new_errors':{name:[r for r in rows if r['before']==r['reference'] and r['after']!=r['reference']] for name,rows in changes.items()},
    'historical_summary_correction':'Archived metrics and known-target coverage give target33/54 and repeated2/10; prior prose34/3 was stale. DANCE emission lacks target references, so excluded, not counted TP.'})
atomic_json(P/'integrity.json',{'status':'PASS','protected_hashes':verified,'hashes_verified':len(verified),'source_and_AI_labels_unchanged':True,
    'canonical_threads_verified':500,'derived_threads_verified':500,'historical_task_statuses_preserved':len(history),
    'checkpoint_V1_unchanged':True,'threshold':.41,'production_default_unchanged':True,'SQLite_unchanged':True,
    'no_post_challenge_rule_changes':True,'training_performed':False,'r07_created':False,'real_human_gold_threads':0})

lines=['# Repeated recovery v5 — verified synthetic development',
    '', '2026-11-03. Completed the requested safe development/evaluation/local integration work. No r07, no training, no model/default switch or deployment. Real T028 remains BLOCKED. This report supersedes stale status prose for current acceptance; historical DONE task lines remain history.',
    '', '## Five reproduced failures and repair',
    '', 'Before editing runtime, five exact frozen r06 event tests FAILED (red_tests.log). Snapshot context-v4/target-v4/repeated-v4 and r06 prediction/output hashes are in before_lock.json. Reference text/labels/evidence IDs were not edited.',
    '', '| Thread | Original cause | Repair | Expected and recovered evidence |','|---|---|---|---|',
    '| SGZ500_0218 | Root attack C01 had no grounded addressee; C06 alone was insufficient | Bounded reciprocal exchange: U01 self-response C02 + later U02→U01 grounded C06 | C01,C06 |',
    '| SGZ500_0255 | Voice-animal disparagement and contemptuous silencing absent from vocabulary | Bounded personal disparagement clauses, not generic mic advice | C02,C05 |',
    '| SGZ500_0318 | Personal worthlessness construction not recognized | Clause-scoped denial of personal worth | C02,C05 |',
    '| SGZ500_0349 | Contemptuous silencing and rejection of existence absent | Personal derogation with addressee and contempt cues | C02,C05 |',
    '| SGZ500_0491 | Second indirect exclusion attack not recognized | Addressee-scoped social exclusion construction | C03,C06 |',
    '', 'Context-v5 handles the new constructions, reported/negated/quoted scope and a new attack after apology. The silencing rule requires contempt cues; a legitimate breathing instruction is a negative regression. Target-v5 adds retrospective root candidate only when a same-actor later grounded attack has one target, within30minutes/16comments, and that person directly answered the root with a self-correction/self-defense. An ordinary reply, intervention, no response, self-target, conflicting targets or ambiguity does not ground the root. This is heuristic review evidence, not a harassment verdict.',
    '', 'Repeated-v5 groups actual qualified attack instances by(actor,target), distinct UTC timestamps, and chronological evidence. Reply C02 can explain target resolution but is never attack evidence. Legacy raw scores, recipient heuristics, lexical fields and threshold0.41 remain byte/value invariant. No hardcoded thread/comment IDs in runtime. API contract stays2.0; only context/target version defaults updated, no new required field or enum. Need-human-review remains true; no visibility policy executed.',
    '', '## Evaluation discipline',
    '', 'The original500threads/5115comments and all r06 splits remain frozen; no new500 generated. Rule hashes frozen before authoring12new distinct scenes/74comments (56CLEAN/18TOXIC), source synthetic_reference, human_gold=false. New content exact/near overlap with existing synthetic sources=0 at char5Jaccard0.85/min35characters. Metadata compiler does not generate utterances; semantic novelty/naturalness is not proven. New challenge authored by this same assistant, not author-blind or human gold.',
    '', 'Fresh challenge received actual local CPU inference from V1/r05/r06 once. Prior620scores reused from immutable r06 cache. All model hashes and fresh labels locked before scoring; all three runtime rule files still match pre-challenge hashes. No rules changed after fresh results. Fresh data is forbidden for training and registered in independent-real development exclusion sources. No independent test labels read or scored.',
    '', '## Repeated and target before/after',
    '', '| Scope | Before TP/FP/FN | After TP/FP/FN | After precision/recall | Evidence correct |','|---|---:|---:|---:|---:|']
for split in ('synthetic_validation','synthetic_challenge','fresh_synthetic_challenge'):
    b=evaluation['metrics']['r06']['before'][split]['grounding']['repeated'];a=evaluation['metrics']['r06']['after'][split]['grounding']['repeated']
    lines.append(f"| {split} | {b['tp']}/{b['fp']}/{b['fn']} | {a['tp']}/{a['fp']}/{a['fn']} | {a['precision']:.4f}/{a['recall']:.4f} | {a['evidence_correct']}/{a['evidence_total']} |")
b=development['grounding']['before'];a=development['grounding']['after']
lines+=['',f"Broad890comment replay (886known labels): target {b['target_correct']}/54→{a['target_correct']}/54; repeated TP{b['repeated']['tp']}→{a['repeated']['tp']}/10, FP{a['repeated']['fp']}, FN{a['repeated']['fn']}, evidence{a['repeated']['evidence_correct']}/{a['repeated']['evidence_total']}correct. Three legacy threads lack target references and are omitted from grounding metrics, not silently scored as correct.",
    '', 'Prior AUTO_PROGRESS prose said34/54targets and3/10events. Recalculation matches archived metrics.json:33/54and2/10before this repair. Three event emissions existed, but DANCE lacks grounding reference coverage and cannot be counted as a validated TP. Historical files retained; current verified counts above take precedence.',
    '', 'Fresh target precision1.0/recall0.875 (14/16directed attacks with known target); two additional toxic root comments have unknown target and do not create invented pairs. Fresh remaining repeated misses:',
    '', '- REP_FRESH_02 Khoa→Vy: novel “cục chì cả đội phải kéo” is outside bounded context vocabulary, leaving one qualified attack. Classifier toxicity alone does not manufacture an attack instance.',
    '- REP_FRESH_11 Tien→Phuong: root target resolution is deliberately limited to30minutes; later grounded attack occurs over an hour later. The root stays abstained, so event is missed.',
    '', f'Broad replay remaining pairs: {broad_missing}. These misses are disclosed, not patched using the fresh challenge. Precision/evidence correctness here mean agreement with AI references, not correctness on real social conversations.',
    '', '## T030 classifier comparison (raw0.41)',
    '', '| Split | Model | N | Accuracy | Macro-F1 | Toxic P | Toxic R | Toxic F1 | TN/FP/FN/TP |','|---|---|---:|---:|---:|---:|---:|---:|---|']
for split in ('synthetic_validation','synthetic_challenge','fresh_synthetic_challenge'):
    for name in ('V1','r05','r06'):
        m=evaluation['metrics'][name]['raw'][split]
        lines.append('| '+' | '.join([split,name,str(m['n'])]+[f'{m[k]:.6f}' for k in ('accuracy','macro_f1','toxic_precision','toxic_recall','toxic_f1')]+['/'.join(str(m[k]) for k in ('tn','fp','fn','tp'))])+' |')
lines+=['','Old raw metrics exactly match the completed r06 report. Rule work changes advisory/context/grounding only; no classifier improvement is claimed from changing rules. Full confusion matrices have rows referenceCLEAN/TOXIC, columns predictionCLEAN/TOXIC. UNCERTAIN references excluded with counts preserved; abstentions counted explicitly.',
    '', '## Component ablation (same model scores and references)',
    '', '| Split | Model | Variant | Advisory Macro-F1 | Toxic P/R | FP/FN | Repeated TP/FP/FN |','|---|---|---|---:|---:|---:|---:|']
for split in ('synthetic_validation','synthetic_challenge','fresh_synthetic_challenge'):
    for name in ('V1','r05','r06'):
        for variant in ('before','context_only','target_repeated_only','after'):
            m=evaluation['metrics'][name][variant][split]['classification'];g=evaluation['metrics'][name][variant][split]['grounding']['repeated']
            lines.append(f"| {split} | {name} | {variant} | {m['macro_f1']:.6f} | {m['toxic_precision']:.4f}/{m['toxic_recall']:.4f} | {m['fp']}/{m['fn']} | {g['tp']}/{g['fp']}/{g['fn']} |")
lines+=['','Context-only replays old engine/target with new context; target/repeated-only uses old context with new target and second pass; full-after enables both. Lexicon unchanged and held fixed; this is not a lexical or training recipe ablation. On the five old missed events, context-only recovers4, target/repeated-only1, full5. Rule ablations retain exact raw/legacy lexical fields for all models.',
    '', '## Paired errors and limits','']
for name,rows in changes.items():
    wins=sum(r['after']==r['reference'] and r['before']!=r['reference'] for r in rows);losses=sum(r['before']==r['reference'] and r['after']!=r['reference'] for r in rows)
    lines.append(f'- {name}, combined old620+fresh74: {wins}label repairs, {losses}new label errors. See error_analysis.json for all rows, including residual errors.')
cb=development['classification']['before'];ca=development['classification']['after']
lines+=['',f"Broad886known advisory labels: FP{cb['fp']}→{ca['fp']}, FN{cb['fn']}→{ca['fn']}, MacroF1{cb['macro_f1']:.6f}→{ca['macro_f1']:.6f}; new-label regressions={len(development['new_label_errors'])}. Fresh r06 advisory still FP3/FN1; raw r06 FP3/FN5. Old r06 challenge raw FP9/FN5 is unchanged; advisory FP6/FN1, not a new raw-model score.",
    '', '## T031 local registry, shadow and rollback',
    '', 'configs/model_registry.repeated_recovery.local.json is a separate opt-in SHA-bound registry with candidate_r06 approved_for_selection=false. Actual r06 and originalV1 loaded offline. Implicit candidate selection refused; injected candidate loader failure falls back to V1. New-process ASGI actual model API returns200→503→200; evidence[b,d]correct, intervention/apology[c,e]excluded. Default path before/after identical. This does not alter running demos/production or approve quality/promotion.',
    '', '## T032 integration evidence',
    '', '610root testsPASS/0FAIL/one Starlette-httpx deprecation warning;177Social testsPASS/0FAIL/one warning. Initial root test run had609PASS/1FAIL because the new artifact test used Windows cp1252 to read UTF-8; corrected the decoding only, references/rules unchanged, full610 rerunPASS. Earlier86focusedPASS; five red baseline failures retained. The initial Social invocation used rootvenv without Alembic and failed collection; correct existing servicevenv passed177 without installing dependencies.',
    '', 'Five-process browser E2E: SocialAPI, AI fixture, worker, SocialWeb, ModerationWeb. One browser testPASS; review→hide→appeal→restore/audit, AI outage/retry/recovery/manual race guards.2retry attempts,1resolved synthetic appeal; browsers never call AI directly. Disposable SQLite/accounts only; owned processes exited, no live migrations, logs privacyPASS. Browser E2E uses fixtureAI (real_model_inference=false); actual-model ASGI/API mechanics are the separate T031 tests above. No frontend source changed; npm build not run. No new real-user/production integration claim.',
    '', '## Current T028–T033 acceptance',
    '', '| Task | Current status | Verified portion / missing evidence |','|---|---|---|',
    '| T028 | BLOCKED | Real0/200, human gold0; rights/provenance, same-humanRound1/Round2 and independent lock missing. WikimediaPAUSED; old30/313NOT_FOUND per previous audit. |',
    '| T029 | BLOCKED formal | r06 experimental training already complete; no new training/r07. Full formal acceptance still depends on T028; no current training authorization. |',
    '| T030 | PARTIAL | Synthetic classifier/rule comparisons, matrices and ablations complete; independent human-gold evaluation missing. |',
    '| T031 | PARTIAL | Local registry/shadow/fallback/rollback verified; production selection/release not authorized, independent quality gate missing. |',
    '| T032 | PARTIAL | Safe backend/browser/worker/review/appeal/offline integration verified; full release validation depends on missing upstream acceptance. |',
    '| T033 | PARTIAL | This provisional report and artifacts complete; real-world conclusions and final acceptance unsupported. |',
    '', 'Historical DONE lines remain unchanged and are not current real-world acceptance. Current authority is tasks/CURRENT_AI_SCOPE.json; task order/progress updated. No task is made DONE merely because its synthetic subwork passed.',
    '', '## Files, reproduction and integrity',
    '', 'Runtime: context_signals.py, target_signals.py, signal_engine.py; additive contract version defaults. New tests: test_repeated_recovery.py and test_repeated_evaluation_artifacts.py. Reusable evaluation: scripts/evaluate_repeated_recovery.py. New12fixture JSONs+manifest/README, independent-real exclusion source registration, isolated local registry config; source task notes, TASK_ORDER/TASK_ORDER_AI/AUTO_PROGRESS and current scope. No model/training source/checkpoint changes.',
    '', f'Integrity PASS: {len(verified)}hash-bound protected artifacts, canonical500+derived500 checked,27historical task states preserved; originalV1/default/r03/r04/r05/r06/threshold/testsplit/SQLite/sourceAIlabels unchanged. New challenge references and rules remain frozen. Evidence paths and commands: [README](../../../reports/ai_update/repeated_recovery_20261103/README.md); ARTIFACTS.json records final file hashes. Repository has no Git metadata, so no commit/diff claim.',
    '', 'Next: review the two fresh repeated misses as documented limitations; do not tune against this now-seen challenge and call it blind. Future rule work needs a separate predeclared holdout. Real acceptance requires permitted source-verifiable conversations, privacy/leakage checks, same-humanRound1/Round2 and evaluation lock. No default model switch, r07 training, auto-hide or deploy authorized.', '']
report=R/'docs/ai-update/final-report/REPEATED_RECOVERY_V5.md';report.write_text('\n'.join(lines),encoding='utf-8')

scope=read(R/'tasks/CURRENT_AI_SCOPE.json');scope.update(authority='Latest repeated-recovery follow-up: safe rule/evaluation/local integration authorized; no training/r07/default change. Formal real acceptance missing.',remaining_ready_work='Requested safe follow-up verified. Fresh challenge consumed without tuning; independent real T028 and formal release acceptance remain BLOCKED.')
scope['current_tasks']['T025'].update(status='DONE',scope='Scoped v5 development repair of five known misses; fresh repeated4/6, two misses disclosed; not independent acceptance')
for name in ('T030','T031','T032','T033'):
    scope['current_tasks'][name].update(status='PARTIAL',formal_acceptance='BLOCKED_T028_REAL_HUMAN_GOLD',report='docs/ai-update/final-report/REPEATED_RECOVERY_V5.md')
scope['current_tasks']['T030']['development_status']='DONE_SYNTHETIC_ONLY'
scope['current_tasks']['T031']['local_registry_rollback_status']='DONE_LOCAL_ONLY'
scope['current_tasks']['T032'].update(safe_integration_status='DONE',scope='610root/177SocialPASS plus disposable5process browserE2E and actual model isolatedASGI')
scope['current_tasks']['T033']['provisional_report_status']='DONE_LIMITATIONS_EXPLICIT'
scope['T030']['development']='DONE_SYNTHETIC_ONLY';scope['T031']['local_registry_rollback']='DONE_R06_LOCAL_ONLY'
scope['current_tasks']['T029']['experimental_r06_training_already_completed']=True
scope['followup_repeated_v5']={'status':'COMPLETE_SAFE_SCOPE','training_performed':False,'old_challenge_repeated_tp':5,'fresh_repeated_tp':4,'fresh_repeated_fn':2,
    'root_tests_passed':610,'social_tests_passed':177,'browser_e2e':'PASS_FIXTURE_AI','actual_model_registry_ASGI':'PASS','production_changed':False}
assert scope['T028']['current_status']=='BLOCKED' and not scope['training_allowed_this_session'] and not scope['synthetic_experiment']['authorized']
atomic_json(R/'tasks/CURRENT_AI_SCOPE.json',scope)
note='''
## Current verified follow-up — repeated/context/target v5

T028 BLOCKED(real0/200,humanlabels0); T029 formalBLOCKED(r06 experimental already trained, no r07); T030/T031/T032/T033 PARTIAL (safe synthetic/local work verified; missing independent acceptance, no production authorization). Historical DONE preserved; current scope tasks/CURRENT_AI_SCOPE.json.

Five event regression red5FAIL before fix; old challenge repeated0/5→5/5, evidence10/10correct. Fresh post-freeze12threads/74comments:2/6→4/6, precision1/recall.6667, evidence8/8correct;2misses retained, no post-score rule changes. Canonical500/5115 unchanged. Broad890replay known886 FP18→18/FN6→4; repeated2/10→8/10,FP0,evidence20/20; no new label errors. Old prose34target/3events superseded by archived/recomputed33/54and2/10; DANCE lacks grounding refs and cannot count as TP.

Tests610rootPASS/177SocialPASS/browserfiveprocessE2EPASS; actual r06 shadow/fallbackV1/ASGI200→503→200PASS. Browser uses fixtureAI/disposableSQLite, actual models tested separately. Model/default/V1/0.41/test/SQLite/reference labels unchanged; no training/deploy. Runtime context_signals.py/target_signals.py/signal_engine.py+contract defaults; two new test files, reusable evaluate_repeated_recovery.py,12new fixture JSONs/manifest, isolated registry, real-cohort development exclusions, report/progress/task notes. Full file inventory/hashes in reports/ai_update/repeated_recovery_20261103/ARTIFACTS.json.

Report docs/ai-update/final-report/REPEATED_RECOVERY_V5.md; evidence/reproduction reports/ai_update/repeated_recovery_20261103/README.md. Next: real permitted source/human rounds for acceptance; new predeclared holdout before further rule tuning. Do not train r07, recreate500, change default or call synthetic human gold.
'''
for name in ('tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md'):
    p=R/name;content=p.read_text(encoding='utf-8')
    if '## Current verified follow-up — repeated/context/target v5' not in content:p.write_text(content+'\n'+note,encoding='utf-8')
for prefix in ('T025-','T028-','T029-','T030-','T031-','T032-','T033-'):
    p=next((R/'tasks/moderation-ai').glob(prefix+'*.md'));content=p.read_text(encoding='utf-8')
    banner='> CURRENT verified follow-up: T028/T029 formal BLOCKED; T030–T033 PARTIAL. Safe synthetic/local evidence verified, no real/human-gold acceptance or production activation. Historical DONE below is preserved. See [v5 report](../../docs/ai-update/final-report/REPEATED_RECOVERY_V5.md) and ../CURRENT_AI_SCOPE.json.\n\n'
    if not content.startswith(banner):p.write_text(banner+content+'\n'+note,encoding='utf-8')
(R/'datasets/fixtures/repeated_holdout_20261103/README.md').write_text('''# Frozen synthetic post-fix challenge

12distinct Codex-authored scenes/74comments after v5 rule lock, not500new threads.56CLEAN/18TOXIC, AI references only; no human gold. Evaluated once using actual V1/r05/r06. Repeated4/6events, precision1/recall2/3,evidence8/8correct; two misses deliberately retained after scoring. Root unknown target does not create a guessed pair. No text/label changes after lock, no further rule tuning on this set.

manifest.json binds all12JSONs and pre-authoring rule lock. Metadata/timestamps are deterministic synthetic values; utterances were authored individually, no paid API/template utterance generator. Exact/near overlap with prior synthetic sources0 under documented heuristic; semantic novelty and human correctness not established. This dataset is forbidden for training and registered as exposed development in real-cohort exclusion sources. It cannot become independent real-world evidence.

Report: docs/ai-update/final-report/REPEATED_RECOVERY_V5.md. Audit: reports/ai_update/repeated_recovery_20261103/fresh_audit.json. Preserve original manifest/thread hashes; subsequent experiments need a distinct holdout.
''',encoding='utf-8')
(P/'README.md').write_text('''# Completed repeated recovery v5 — safe reproduction

Report: [REPEATED_RECOVERY_V5.md](../../../docs/ai-update/final-report/REPEATED_RECOVERY_V5.md). Current acceptance: tasks/CURRENT_AI_SCOPE.json. T028real/T029formalBLOCKED; T030–T033PARTIAL, safe development/local mechanics verified. No r07/training/production changes.

## Commands actually executed (repository root)

```powershell
.\\.venv\\Scripts\\python.exe -m pytest -q --basetemp reports/ai_update/test_tmp/repeated_final_utf8
```

610rootPASS; use a new unique --basetemp for a rerun. The original red five-event test results are red_tests.log; final root log root_tests_verified.log. tests/test_repeated_recovery.py freezes the five original reference events and negative controls; test_repeated_evaluation_artifacts.py checks locked labels/populations/evidence accounting, not a forced performance target.

Social suite was run from services/social-api with its own .venv/Scripts/python.exe -m pytest -q --basetemp ../../reports/ai_update/test_tmp/repeated_social_own (177PASS). The rootvenv lacks Alembic, so do not use it for Social. No packages installed. Services/DBs in five-process browser E2E are temporary/owned; runner run_e2e.py reused the existing run_fullstack with isolated artifact and temp paths, invoked using services/social-api/.venv/Scripts/python.exe. Browser1PASS,2retry attempts,1resolved synthetic appeal, cleanup/privacyPASS; AI is a fixture there. Actual r06/V1 model API shadow/rollback is separately registry_smoke.json.

## Immutable experiment evidence

before_sources/ contains exact v4source snapshots, before_lock.json binds archived r06 outputs. five_events_before.json records root causes. frozen_rule_lock.json was written before fresh challenge authoring; fresh_audit.json checks no later rule edits and exact/near overlap0. datasets/fixtures/repeated_holdout_20261103 has12new scenes, never training/human gold. Canonical500 and r06 model/splits remain unchanged.

Actual comparison command: .venv/Scripts/python.exe -X utf8 scripts/evaluate_repeated_recovery.py --output reports/ai_update/repeated_recovery_20261103/evaluation. The evaluator refuses a completed output, uses actual three-model fresh scores once, and immutable r06 score cache for old620comments. Do not repeat inference to tune against this now-seen challenge. evaluation/evaluation.json stores raw metrics, matrices and before/context-only/target-repeated-only/after ablation; outputs.json retains separate raw/context/lexicon/target/policy/advisory fields. fresh_scores.json records actual model SHAs. error_analysis.json includes remaining errors and pairs. Full890cached replay is development_verified/metrics.json (no new model inference).

registry_smoke.py created configs/model_registry.repeated_recovery.local.json only, with candidate_r06 unapproved; actual load/fallback/isolated API200→503→200 succeeded. It refuses overwriting that registry; do not rerun it or change default to replay evidence. No running server was reconfigured. Current checkpoints and threshold0.41 are unchanged.

Historical summaries overcounted a target/event relative to coverage; archived/recomputed validated baseline33/54targets and2/10events is used, DANCE emission excluded because no target reference exists. Synthetic metrics never substitute for T028. See integrity.json/ARTIFACTS.json for protected artifacts and final file hashes. No Git metadata exists.

Next work requires a fresh predeclared holdout for new rule tuning, or permitted real sources and same-human two-round review for independent acceptance. No automatic new training, model switch, auto-hide or deploy.
''',encoding='utf-8')
update('COMPLETE_SAFE_SCOPE',note)
paths=list(P.rglob('*'))+list((R/'datasets/fixtures/repeated_holdout_20261103').glob('*'))
changed=['services/moderation-ai/app/context_signals.py','services/moderation-ai/app/target_signals.py','services/moderation-ai/app/signal_engine.py','contracts/analysis_response_v2.schema.json',
    'scripts/evaluate_repeated_recovery.py','tests/test_repeated_recovery.py','tests/test_repeated_evaluation_artifacts.py','configs/model_registry.repeated_recovery.local.json',
    'datasets/real_conversations/manifests/development_exclusions.json','tasks/CURRENT_AI_SCOPE.json','tasks/AUTO_PROGRESS.md','tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md','docs/ai-update/final-report/REPEATED_RECOVERY_V5.md']
changed += [next((R/'tasks/moderation-ai').glob(prefix+'*.md')).relative_to(R).as_posix() for prefix in ('T025-','T028-','T029-','T030-','T031-','T032-','T033-')]
paths += [R/name for name in changed]
index={p.relative_to(R).as_posix():file_sha(p) for p in paths if p.is_file() and p!=P/'ARTIFACTS.json' and '__pycache__' not in str(p)}
atomic_json(P/'ARTIFACTS.json',{'status':'VERIFIED_SAFE_SCOPE_COMPLETE','sha256':index,'files':len(index),'changed_project_files':changed,
    'historical_statuses_preserved':True,'formal_tasks':{'T028':'BLOCKED','T029':'BLOCKED','T030':'PARTIAL','T031':'PARTIAL','T032':'PARTIAL','T033':'PARTIAL'}})
print(json.dumps({'status':'COMPLETE_SAFE_SCOPE','rootPASS':610,'socialPASS':177,'browser':'PASS_FIXTURE','actual_registry':'PASS','old_events':'0to5/5','fresh_events':'2to4/6','protected_hashes_verified':len(verified),'artifacts':len(index)}))
