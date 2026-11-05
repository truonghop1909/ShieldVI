# Repeated recovery v5 — verified synthetic development

2026-11-03. Completed the requested safe development/evaluation/local integration work. No r07, no training, no model/default switch or deployment. Real T028 remains BLOCKED. This report supersedes stale status prose for current acceptance; historical DONE task lines remain history.

## Five reproduced failures and repair

Before editing runtime, five exact frozen r06 event tests FAILED (red_tests.log). Snapshot context-v4/target-v4/repeated-v4 and r06 prediction/output hashes are in before_lock.json. Reference text/labels/evidence IDs were not edited.

| Thread | Original cause | Repair | Expected and recovered evidence |
|---|---|---|---|
| SGZ500_0218 | Root attack C01 had no grounded addressee; C06 alone was insufficient | Bounded reciprocal exchange: U01 self-response C02 + later U02→U01 grounded C06 | C01,C06 |
| SGZ500_0255 | Voice-animal disparagement and contemptuous silencing absent from vocabulary | Bounded personal disparagement clauses, not generic mic advice | C02,C05 |
| SGZ500_0318 | Personal worthlessness construction not recognized | Clause-scoped denial of personal worth | C02,C05 |
| SGZ500_0349 | Contemptuous silencing and rejection of existence absent | Personal derogation with addressee and contempt cues | C02,C05 |
| SGZ500_0491 | Second indirect exclusion attack not recognized | Addressee-scoped social exclusion construction | C03,C06 |

Context-v5 handles the new constructions, reported/negated/quoted scope and a new attack after apology. The silencing rule requires contempt cues; a legitimate breathing instruction is a negative regression. Target-v5 adds retrospective root candidate only when a same-actor later grounded attack has one target, within30minutes/16comments, and that person directly answered the root with a self-correction/self-defense. An ordinary reply, intervention, no response, self-target, conflicting targets or ambiguity does not ground the root. This is heuristic review evidence, not a harassment verdict.

Repeated-v5 groups actual qualified attack instances by(actor,target), distinct UTC timestamps, and chronological evidence. Reply C02 can explain target resolution but is never attack evidence. Legacy raw scores, recipient heuristics, lexical fields and threshold0.41 remain byte/value invariant. No hardcoded thread/comment IDs in runtime. API contract stays2.0; only context/target version defaults updated, no new required field or enum. Need-human-review remains true; no visibility policy executed.

## Evaluation discipline

The original500threads/5115comments and all r06 splits remain frozen; no new500 generated. Rule hashes frozen before authoring12new distinct scenes/74comments (56CLEAN/18TOXIC), source synthetic_reference, human_gold=false. New content exact/near overlap with existing synthetic sources=0 at char5Jaccard0.85/min35characters. Metadata compiler does not generate utterances; semantic novelty/naturalness is not proven. New challenge authored by this same assistant, not author-blind or human gold.

Fresh challenge received actual local CPU inference from V1/r05/r06 once. Prior620scores reused from immutable r06 cache. All model hashes and fresh labels locked before scoring; all three runtime rule files still match pre-challenge hashes. No rules changed after fresh results. Fresh data is forbidden for training and registered in independent-real development exclusion sources. No independent test labels read or scored.

## Repeated and target before/after

| Scope | Before TP/FP/FN | After TP/FP/FN | After precision/recall | Evidence correct |
|---|---:|---:|---:|---:|
| synthetic_validation | 1/0/1 | 1/0/1 | 1.0000/0.5000 | 2/2 |
| synthetic_challenge | 0/0/5 | 5/0/0 | 1.0000/1.0000 | 10/10 |
| fresh_synthetic_challenge | 2/0/4 | 4/0/2 | 1.0000/0.6667 | 8/8 |

Broad890comment replay (886known labels): target 33/54→41/54; repeated TP2→8/10, FP0, FN2, evidence20/20correct. Three legacy threads lack target references and are omitted from grounding metrics, not silently scored as correct.

Prior AUTO_PROGRESS prose said34/54targets and3/10events. Recalculation matches archived metrics.json:33/54and2/10before this repair. Three event emissions existed, but DANCE lacks grounding reference coverage and cannot be counted as a validated TP. Historical files retained; current verified counts above take precedence.

Fresh target precision1.0/recall0.875 (14/16directed attacks with known target); two additional toxic root comments have unknown target and do not create invented pairs. Fresh remaining repeated misses:

- REP_FRESH_02 Khoa→Vy: novel “cục chì cả đội phải kéo” is outside bounded context vocabulary, leaving one qualified attack. Classifier toxicity alone does not manufacture an attack instance.
- REP_FRESH_11 Tien→Phuong: root target resolution is deliberately limited to30minutes; later grounded attack occurs over an hour later. The root stays abstained, so event is missed.

Broad replay remaining pairs: [('CTX_RECOVERY_V1_05', 'CTX_RECOVERY_V1_05_U02', 'CTX_RECOVERY_V1_05_U01'), ('SGZ500_0498', 'SGZ500_0498_U02', 'SGZ500_0498_U01')]. These misses are disclosed, not patched using the fresh challenge. Precision/evidence correctness here mean agreement with AI references, not correctness on real social conversations.

## T030 classifier comparison (raw0.41)

| Split | Model | N | Accuracy | Macro-F1 | Toxic P | Toxic R | Toxic F1 | TN/FP/FN/TP |
|---|---|---:|---:|---:|---:|---:|---:|---|
| synthetic_validation | V1 | 306 | 0.934641 | 0.688581 | 0.368421 | 0.466667 | 0.411765 | 279/12/8/7 |
| synthetic_validation | r05 | 306 | 0.934641 | 0.670259 | 0.352941 | 0.400000 | 0.375000 | 280/11/9/6 |
| synthetic_validation | r06 | 306 | 0.964052 | 0.823834 | 0.611111 | 0.733333 | 0.666667 | 284/7/4/11 |
| synthetic_challenge | V1 | 311 | 0.942122 | 0.779884 | 0.541667 | 0.650000 | 0.590909 | 280/11/7/13 |
| synthetic_challenge | r05 | 311 | 0.945338 | 0.787645 | 0.565217 | 0.650000 | 0.604651 | 281/10/7/13 |
| synthetic_challenge | r06 | 311 | 0.954984 | 0.828798 | 0.625000 | 0.750000 | 0.681818 | 282/9/5/15 |
| fresh_synthetic_challenge | V1 | 74 | 0.878378 | 0.824506 | 0.800000 | 0.666667 | 0.727273 | 53/3/6/12 |
| fresh_synthetic_challenge | r05 | 74 | 0.878378 | 0.824506 | 0.800000 | 0.666667 | 0.727273 | 53/3/6/12 |
| fresh_synthetic_challenge | r06 | 74 | 0.891892 | 0.847265 | 0.812500 | 0.722222 | 0.764706 | 53/3/5/13 |

Old raw metrics exactly match the completed r06 report. Rule work changes advisory/context/grounding only; no classifier improvement is claimed from changing rules. Full confusion matrices have rows referenceCLEAN/TOXIC, columns predictionCLEAN/TOXIC. UNCERTAIN references excluded with counts preserved; abstentions counted explicitly.

## Component ablation (same model scores and references)

| Split | Model | Variant | Advisory Macro-F1 | Toxic P/R | FP/FN | Repeated TP/FP/FN |
|---|---|---|---:|---:|---:|---:|
| synthetic_validation | V1 | before | 0.833325 | 0.6000/0.8000 | 8/3 | 1/0/1 |
| synthetic_validation | V1 | context_only | 0.833325 | 0.6000/0.8000 | 8/3 | 1/0/1 |
| synthetic_validation | V1 | target_repeated_only | 0.833325 | 0.6000/0.8000 | 8/3 | 1/0/1 |
| synthetic_validation | V1 | after | 0.833325 | 0.6000/0.8000 | 8/3 | 1/0/1 |
| synthetic_validation | r05 | before | 0.813149 | 0.5789/0.7333 | 8/4 | 1/0/1 |
| synthetic_validation | r05 | context_only | 0.813149 | 0.5789/0.7333 | 8/4 | 1/0/1 |
| synthetic_validation | r05 | target_repeated_only | 0.813149 | 0.5789/0.7333 | 8/4 | 1/0/1 |
| synthetic_validation | r05 | after | 0.813149 | 0.5789/0.7333 | 8/4 | 1/0/1 |
| synthetic_validation | r06 | before | 0.906574 | 0.7368/0.9333 | 5/1 | 1/0/1 |
| synthetic_validation | r06 | context_only | 0.906574 | 0.7368/0.9333 | 5/1 | 1/0/1 |
| synthetic_validation | r06 | target_repeated_only | 0.906574 | 0.7368/0.9333 | 5/1 | 1/0/1 |
| synthetic_validation | r06 | after | 0.906574 | 0.7368/0.9333 | 5/1 | 1/0/1 |
| synthetic_challenge | V1 | before | 0.868246 | 0.6800/0.8500 | 8/3 | 0/0/5 |
| synthetic_challenge | V1 | context_only | 0.896429 | 0.7037/0.9500 | 8/1 | 4/0/1 |
| synthetic_challenge | V1 | target_repeated_only | 0.868246 | 0.6800/0.8500 | 8/3 | 1/0/4 |
| synthetic_challenge | V1 | after | 0.896429 | 0.7037/0.9500 | 8/1 | 5/0/0 |
| synthetic_challenge | r05 | before | 0.877713 | 0.7083/0.8500 | 7/3 | 0/0/5 |
| synthetic_challenge | r05 | context_only | 0.906099 | 0.7308/0.9500 | 7/1 | 4/0/1 |
| synthetic_challenge | r05 | target_repeated_only | 0.877713 | 0.7083/0.8500 | 7/3 | 1/0/4 |
| synthetic_challenge | r05 | after | 0.906099 | 0.7308/0.9500 | 7/1 | 5/0/0 |
| synthetic_challenge | r06 | before | 0.887577 | 0.7391/0.8500 | 6/3 | 0/0/5 |
| synthetic_challenge | r06 | context_only | 0.916156 | 0.7600/0.9500 | 6/1 | 4/0/1 |
| synthetic_challenge | r06 | target_repeated_only | 0.887577 | 0.7391/0.8500 | 6/3 | 1/0/4 |
| synthetic_challenge | r06 | after | 0.916156 | 0.7600/0.9500 | 6/1 | 5/0/0 |
| fresh_synthetic_challenge | V1 | before | 0.889881 | 0.8333/0.8333 | 3/3 | 2/0/4 |
| fresh_synthetic_challenge | V1 | context_only | 0.929187 | 0.8500/0.9444 | 3/1 | 3/0/3 |
| fresh_synthetic_challenge | V1 | target_repeated_only | 0.889881 | 0.8333/0.8333 | 3/3 | 3/0/3 |
| fresh_synthetic_challenge | V1 | after | 0.929187 | 0.8500/0.9444 | 3/1 | 4/0/2 |
| fresh_synthetic_challenge | r05 | before | 0.889881 | 0.8333/0.8333 | 3/3 | 2/0/4 |
| fresh_synthetic_challenge | r05 | context_only | 0.929187 | 0.8500/0.9444 | 3/1 | 3/0/3 |
| fresh_synthetic_challenge | r05 | target_repeated_only | 0.889881 | 0.8333/0.8333 | 3/3 | 3/0/3 |
| fresh_synthetic_challenge | r05 | after | 0.929187 | 0.8500/0.9444 | 3/1 | 4/0/2 |
| fresh_synthetic_challenge | r06 | before | 0.889881 | 0.8333/0.8333 | 3/3 | 2/0/4 |
| fresh_synthetic_challenge | r06 | context_only | 0.929187 | 0.8500/0.9444 | 3/1 | 3/0/3 |
| fresh_synthetic_challenge | r06 | target_repeated_only | 0.889881 | 0.8333/0.8333 | 3/3 | 3/0/3 |
| fresh_synthetic_challenge | r06 | after | 0.929187 | 0.8500/0.9444 | 3/1 | 4/0/2 |

Context-only replays old engine/target with new context; target/repeated-only uses old context with new target and second pass; full-after enables both. Lexicon unchanged and held fixed; this is not a lexical or training recipe ablation. On the five old missed events, context-only recovers4, target/repeated-only1, full5. Rule ablations retain exact raw/legacy lexical fields for all models.

## Paired errors and limits

- V1, combined old620+fresh74: 4label repairs, 0new label errors. See error_analysis.json for all rows, including residual errors.
- r05, combined old620+fresh74: 4label repairs, 0new label errors. See error_analysis.json for all rows, including residual errors.
- r06, combined old620+fresh74: 4label repairs, 0new label errors. See error_analysis.json for all rows, including residual errors.

Broad886known advisory labels: FP18→18, FN6→4, MacroF10.909296→0.917892; new-label regressions=0. Fresh r06 advisory still FP3/FN1; raw r06 FP3/FN5. Old r06 challenge raw FP9/FN5 is unchanged; advisory FP6/FN1, not a new raw-model score.

## T031 local registry, shadow and rollback

configs/model_registry.repeated_recovery.local.json is a separate opt-in SHA-bound registry with candidate_r06 approved_for_selection=false. Actual r06 and originalV1 loaded offline. Implicit candidate selection refused; injected candidate loader failure falls back to V1. New-process ASGI actual model API returns200→503→200; evidence[b,d]correct, intervention/apology[c,e]excluded. Default path before/after identical. This does not alter running demos/production or approve quality/promotion.

## T032 integration evidence

610root testsPASS/0FAIL/one Starlette-httpx deprecation warning;177Social testsPASS/0FAIL/one warning. Initial root test run had609PASS/1FAIL because the new artifact test used Windows cp1252 to read UTF-8; corrected the decoding only, references/rules unchanged, full610 rerunPASS. Earlier86focusedPASS; five red baseline failures retained. The initial Social invocation used rootvenv without Alembic and failed collection; correct existing servicevenv passed177 without installing dependencies.

Five-process browser E2E: SocialAPI, AI fixture, worker, SocialWeb, ModerationWeb. One browser testPASS; review→hide→appeal→restore/audit, AI outage/retry/recovery/manual race guards.2retry attempts,1resolved synthetic appeal; browsers never call AI directly. Disposable SQLite/accounts only; owned processes exited, no live migrations, logs privacyPASS. Browser E2E uses fixtureAI (real_model_inference=false); actual-model ASGI/API mechanics are the separate T031 tests above. No frontend source changed; npm build not run. No new real-user/production integration claim.

## Current T028–T033 acceptance

| Task | Current status | Verified portion / missing evidence |
|---|---|---|
| T028 | BLOCKED | Real0/200, human gold0; rights/provenance, same-humanRound1/Round2 and independent lock missing. WikimediaPAUSED; old30/313NOT_FOUND per previous audit. |
| T029 | BLOCKED formal | r06 experimental training already complete; no new training/r07. Full formal acceptance still depends on T028; no current training authorization. |
| T030 | PARTIAL | Synthetic classifier/rule comparisons, matrices and ablations complete; independent human-gold evaluation missing. |
| T031 | PARTIAL | Local registry/shadow/fallback/rollback verified; production selection/release not authorized, independent quality gate missing. |
| T032 | PARTIAL | Safe backend/browser/worker/review/appeal/offline integration verified; full release validation depends on missing upstream acceptance. |
| T033 | PARTIAL | This provisional report and artifacts complete; real-world conclusions and final acceptance unsupported. |

Historical DONE lines remain unchanged and are not current real-world acceptance. Current authority is tasks/CURRENT_AI_SCOPE.json; task order/progress updated. No task is made DONE merely because its synthetic subwork passed.

## Files, reproduction and integrity

Runtime: context_signals.py, target_signals.py, signal_engine.py; additive contract version defaults. New tests: test_repeated_recovery.py and test_repeated_evaluation_artifacts.py. Reusable evaluation: scripts/evaluate_repeated_recovery.py. New12fixture JSONs+manifest/README, independent-real exclusion source registration, isolated local registry config; source task notes, TASK_ORDER/TASK_ORDER_AI/AUTO_PROGRESS and current scope. No model/training source/checkpoint changes.

Integrity PASS: 259hash-bound protected artifacts, canonical500+derived500 checked,27historical task states preserved; originalV1/default/r03/r04/r05/r06/threshold/testsplit/SQLite/sourceAIlabels unchanged. New challenge references and rules remain frozen. Evidence paths and commands: [README](../../../reports/ai_update/repeated_recovery_20261103/README.md); ARTIFACTS.json records final file hashes. Repository has no Git metadata, so no commit/diff claim.

Next: review the two fresh repeated misses as documented limitations; do not tune against this now-seen challenge and call it blind. Future rule work needs a separate predeclared holdout. Real acceptance requires permitted source-verifiable conversations, privacy/leakage checks, same-humanRound1/Round2 and evaluation lock. No default model switch, r07 training, auto-hide or deploy authorized.
