
## CURRENT AUTHORITY — real evaluation criteria restored, historical DONE preserved

Latest PartsA/B/C + follow-up override earlier synthetic-only/CPU permission for new work. **T028 real-evaluation criteria: BLOCKED** until permitted200real threads, the same human's manual Round1/Round2, privacy/leakage checks and evaluation lock. Earlier synthetic T028 DONE is historical scope evidence, not real completion. All other confirmed DONE records are retained. Current machine-readable criteria: `tasks/CURRENT_AI_SCOPE.json`; evidence: `reports/ai_update/independent_readiness_20261103/`.

Wikimedia collector PAUSED by user; no further contact/path questions in this session, no fake identity or browser impersonation. Research other public licenses; do not ingest unclear rights. Continue independent synthetic development, preparation/local registry/integration/reporting. New training and production changes are not authorized. Distinguish preparation/development DONE from blocked real-world acceptance; dependencies remain visible.

# Thứ tự toàn dự án ShieldVI

Tasks, docs và runtime cùng root dự án `ShieldVI_V3_Hybrid_Review/`. File task là nguồn trạng thái và giới hạn nghiệm thu; bảng này chỉ tổng hợp, không xác nhận lại DONE. Lần gộp tài liệu đã kết thúc; xem [phiên tự động 02/11/2026](AUTO_PROGRESS.md) để tiếp tục đúng trạng thái.

## Các task hiện có

| Task | Nhóm | Phụ thuộc đã ghi | Trạng thái trong file |
|---|---|---|---|
| [T007](./integration/T007-repo-blueprint.md) | integration | — | DONE — giữ nguyên phạm vi/bằng chứng trong file |
| [T012](./integration/T012-moderation-jobs.md) | integration | T009, T011 | DONE — giữ nguyên phạm vi/bằng chứng trong file |
| [T014](./integration/T014-e2e-security.md) | integration | T010, T012, T013 | DONE — giữ nguyên phạm vi/bằng chứng trong file |
| [T015](./integration/T015-migrate-legacy.md) | integration | T014 | DONE — giữ nguyên phạm vi/bằng chứng trong file |
| [T016](./integration/T016-policy-design.md) | integration | T007 | DONE — giữ nguyên phạm vi/bằng chứng trong file |
| [T017](./integration/T017-durable-worker-and-offline.md) | integration | T009, T011, T012 | DONE — giữ nguyên phạm vi/bằng chứng trong file |
| [T019](./integration/T019-evaluation-and-privacy.md) | integration | T012, T013 | DONE — giữ nguyên phạm vi/bằng chứng trong file |
| [T011](./moderation-ai/T011-moderation-adapter.md) | moderation-ai | T007 | DONE — giữ nguyên phạm vi/bằng chứng trong file |
| [T013](./moderation-web/T013-admin-review.md) | moderation-web | T012 | DONE — giữ nguyên phạm vi/bằng chứng trong file |
| [T018](./moderation-web/T018-admin-appeals-audit.md) | moderation-web | T013, T016 | DONE — giữ nguyên phạm vi/bằng chứng trong file |
| [T008](./social-api/T008-auth-database.md) | social-api | T007 | DONE — giữ nguyên phạm vi/bằng chứng trong file |
| [T009](./social-api/T009-social-content.md) | social-api | T008 | DONE — giữ nguyên phạm vi/bằng chứng trong file |
| [T010](./social-web/T010-social-frontend.md) | social-web | T009 | DONE — giữ nguyên phạm vi/bằng chứng trong file |

T001–T006 được README_SOCIAL nhắc tới nhưng không có file trong workspace đã kiểm kê; không tạo lại hoặc đoán trạng thái. Giữ ưu tiên lịch sử T007 → T016 rồi theo dependency; không áp thứ tự số học thay cho dependency.

## Nhóm AI Update T020–T033

Nguồn thứ tự/trạng thái chi tiết: [TASK_ORDER_AI](moderation-ai/TASK_ORDER_AI.md). Cột phụ thuộc liên nhóm dưới đây là yêu cầu đối chiếu/tích hợp, không sửa dependency trong task nguồn và không thay đổi trạng thái Social.

| Task | Dependency trong nhóm AI | Liên hệ Social / điều kiện bổ sung | Trạng thái nguồn |
|---|---|---|---|
| [T020](moderation-ai/T020-audit-ai-snapshot-baseline.md) | none | Audit đã lưu [baseline](../docs/ai-update/T020_BASELINE_REPORT.md); default/checkpoint giữ nguyên. | DONE |
| [T021](moderation-ai/T021-regression-fixtures-provisional-annotation.md) | T020 | Fixtures riêng; không đổi test Social đã chốt. | DONE |
| [T022](moderation-ai/T022-context-signals-apology-quote-defense-inte.md) | T021 | Giữ contract T011 và prediction raw. | DONE |
| [T023](moderation-ai/T023-lexicon-vi-en-teencode-expansion.md) | T021 | Không tự thay policy T016. | DONE |
| [T024](moderation-ai/T024-target-detection-v3-explicit-and-abstain.md) | T021,T022 | Giữ boundary Social T011/T016. | DONE |
| [T025](moderation-ai/T025-repeated-harassment-v3-evidence-aware.md) | T022,T024 | Bằng chứng phục vụ policy T016, không tự quyết visibility. | DONE |
| [T026](moderation-ai/T026-api-schema-dashboard-signals-policy-bounda.md) | T022,T023,T024,T025 | Đối chiếu T011/T016; nếu thay UI/adapter phải chốt scope với T010/T013/T018. | DONE |
| [T027](moderation-ai/T027-data-ingestion-provenance-for-hard-cases.md) | T021,T023 | Giữ quy tắc dữ liệu/privacy T019; không thay holdout cũ. | DONE |
| [T028](moderation-ai/T028-independent-evaluation-solo-review-protoco.md) | T021,T027 | Synthetic-only;512syntheticthreads total; GAMEcontext regression verified | DONE |
| [T029](moderation-ai/T029-optional-train-candidate-visobert-on-colab.md) | T027,T028 + bounded localCPU authorization | ActualCPUhead534steps/400.94s; encoderfrozen; fullGPU notrun | DONE |
| [T030](moderation-ai/T030-paired-offline-evaluation-ablation.md) | T026,T028 (+T029 optional) | Development V1/Hybrid and original B0–B3 replay complete; REAL/candidate separate | DONE |
| [T031](moderation-ai/T031-optional-model-registry-shadow-and-rollbac.md) | T029,T030 (local review) | Actual local review/reject; shadow/fallback/rollbackPASS; default unchanged | DONE |
| [T032](moderation-ai/T032-social-ai-integration-offline-safety-e2e.md) | T026,T030 (+T031 optional) | Social177PASS + browser E2E1PASS + builds3PASS; DB tạm | DONE |
| [T033](moderation-ai/T033-technical-report-thesis-handoff.md) | T030,T032 | Handoff có bằng chứng và giới hạn; không chứng nhận release mới | DONE |

T029/T031 chỉ SKIPPED_APPROVED khi có quyết định người dùng. Không coi lần train thử trước đây hoặc lần gộp tài liệu này là thực hiện/hoàn thành task AI Update.

## Điểm dừng phiên tự động 02/11/2026

T021–T027 DONE; T028 V2 BLOCKED: 0/200, collector chờ operator contact Wikimedia; nhãn người và kiểm nguồn/riêng tư/đầy đủ chưa có. Công cụ đã qua 299 test + Chrome E2E. T029–T033 chưa đủ dependency; không tự chạy hoặc bypass gate. T020 và task Social giữ DONE có sẵn. Xem [AUTO_PROGRESS](AUTO_PROGRESS.md).

## Cập nhật phạm vi 03/11/2026

T028 chuyển thành AI-authored synthetic/G2-S theo yêu cầu người dùng, trạng thái TODO để xác minh acceptance mới; sử dụng bộ 200 hiện có. Điểm dừng real-world 02/11 phía trên là lịch sử. T029 vẫn BLOCKED do code readiness chưa đồng bộ/G3/resource; không chạy train hoặc thay trạng thái task Social.

## Active autonomous request — 03/11/2026

Latest attachment supersedes previous synthetic-only scope and one-task stop: T028=REAL200, remainsBLOCKED(0); datasetB synthetic500/5115 complete. Independent T029–T033 work authorized. T029 prepared/nottrained; T030 development evidence with failures/full-ablation blockers; T031 local registry only; T032 verificationDONE; T033handoff inprogress. Social task states unchanged. Current details in TASK_ORDER_AI/AUTO_PROGRESS.

T030 supplement03/11: scoped archive supplied original T020 captures; actual B0–B3 replay on5unchanged fixtures complete (cached real V1, old per-input lexical results, byte-identical legacy engine). T030 DONE for declared synthetic-development report. New60-thread challenge failures remain; no real/candidate improvement claimed.

## Handoff cuối03/11/2026

T030/T032/T033 DONE theo scope nghiên cứu/tích hợp/báo cáo được giao; T028/T029/T031 BLOCKED. REAL0/200, synthetic500/5115,AIlabels5115,human0;358root+177Social testsPASS,browser1PASS,3buildsPASS. CandidateNOT_TRAINED; không production/default/threshold/test/DB changes. Các mục scope cũ phía trên là lịch sử, xem TASK_ORDER_AI và final-report để tiếp tục.

## Active GAME_RANK_30 revision

Latest user request supersedes REAL requirement: T028 synthetic-only IN_PROGRESS. AI12newthreads/120comments generated before rule edits; original GenZ500/test intact;30user-reference labels frozen separately from gold. Work on context/assessment/reply-target/repeated plus before-after regression; no training/deploy. Earlier REAL blockers/handoff are historical.

## Current GAME_RANK_30 handoff

T028synthetic-only DONE, REAL/contact không còn bắt buộc. AI12newthread/120comments +30userreference riêng;500GenZ bất biến. Root417/Social177PASS,browser2checks/buildPASS, actualV1afterPASS. T029/T031 BLOCKED về GPU/candidate, không phải dữ liệu thật. Không tự train hoặc deploy; các mục scopeREAL trước đó là lịch sử. Xem taskAI/AUTO_PROGRESS và CONTEXT_RECOVERY_GAME_RANK_30 report.

## ACTIVE — run remaining tasks with feasible scope

Latest user authorizes all-task execution and task-scope revision. RemainingT029/T031: boundedlocalCPU frozen-encoder head experiment, then actual candidate local shadow/rollback review. No paid services/GPU/fullfine-tune/production activation authorized by this interpretation. Preserve old DONE states and all data/model invariants. See AUTO_PROGRESS and reports/ai_update/all_tasks_cpu_20261103/progress.json.

## CURRENT — remaining tasks completed under revised feasible scope

T029CPUhead experimentDONE(534steps,encoderfrozen),T031localcandidate reviewDONE(rejectpromotion,actualshadow/fallback/rollback). All27existingtaskfilesDONE; old blockers/REAL/GPU-only notes above are historical. FullencoderGPU/production remain NOT_RUN, not falsely claimed complete. Root434PASS; V1/default0.41/data/test/DB unchanged. Current source: tasks/AUTO_PROGRESS.md and docs/ai-update/final-report/CPU_HEAD_COMPLETION.md.


## Follow-up r04 — revise refused work and continue

**Follow-up status: IN_PROGRESS.** Prior task DONE and r03 rejection are preserved. One additional bounded CPU head-only research attempt:4threads/900seconds/cost0. New config lowers synthetic loss .5→.1 and LR3e-5→1e-5, increases distillation .5→1.0. Encoder/data/0.41 stay fixed. Historical validation-only selection; no test rescore or example-specific tuning. This exploratory follow-up after the old test was inspected is not fresh independent evaluation. Original quality gates remain frozen; no production promotion.

Evidence: `reports/ai_update/candidate_revision_20261103/predeclared_experiment.json`; current progress in `tasks/AUTO_PROGRESS.md`. Completion requires actual optimizer/reload/integrity evidence and a validation verdict.


## CURRENT FOLLOW-UP r04 — COMPLETE, promotion disabled

Actual bounded CPU follow-up completed: 356optimizersteps/2epochs/431.84s, encoderfrozen, newcheckpoint r04. ValidationMacroF1 original0.763701/r03.753042/r040.756865; toxicP0.613065/R0.525862. Decision **REJECT_PROMOTION_KEEP_EXISTING_DEFAULT**, unchanged original gates. No new test/challenge inference or promotion; historical evaluation is not freshblind. Prior27task DONE states preserved. Follow-up status COMPLETE for execution/review, not model acceptance.

Root448PASS/1warning;40preflightPASS.31protectedhashes+all200/500source datasets+12contextfixtures/userreference/validation/test/SQLite/defaultV1.1 unchanged. No paidGPU/fullencodertraining/upload/download/push/deploy. Files: scripts/review_t029_validation.py, tests/test_t029_validation_review.py, configs/t029_genz500_cpu_head_r04.json; task/index/progress and3AI docs updated; newcandidate/reports separate.

Current evidence reports/ai_update/candidate_revision_20261103/; report docs/ai-update/final-report/CANDIDATE_REVISION_R04.md. Resume from this section, not historical IN_PROGRESS/BLOCKED notes above. No remaining task ready in the27existing files; next: Stop this recipe; retain default and negative result. Do not relax gates or rescore test.


## CURRENT requested training r05 — IN_PROGRESS

User explicitly asks to load new dataset and train: “hãy nạp dataset mới để train mô hình đi”. One bounded local CPU classifier-head continuation from approved V1.1, encoder frozen; max4threads/900s/cost0. DatasetGenZ500 train split +ViCTSD original; keep development/test/labels/default unchanged. Newrun T029_genz500_head_cpu_20261103_r05; evidence reports/ai_update/train_genz500_r05_20261103/. Previous DONE states and r03/r04 negative decisions are preserved. No GPU/full-encoder training or promotion.


## CURRENT requested training r05 — COMPLETE

Explicit latest train request executed: new GenZ500 dataset,11340rows=6942ViCTSD+4398AI references; warmstart approvedV1.1 classifier, frozenV1-compatibleencoder. Actual 534steps/3epochs/474.17s; selectedepoch2; config5e-6/synweight.1/distill1/max4CPUthreads900s/cost0. Saved models/candidates/T029_genz500_head_cpu_20261103_r05; reloadedprobeerror0.0. No fullencoder/GPU training.

ValidationMacroF1 original0.763701/default0.760205/r050.755418; candidateP0.646067/R0.495690. DecisionREJECT_PROMOTION_KEEP_EXISTING_DEFAULT; gates unchanged, no test/challenge scoring and no freshblind claim. Training completion doesnot imply promotion; defaultV1.1 remains active. Prior taskDONE and negative r03/r04 evidence preserved.

42relatedpytestPASS/1warning; actualposttrainreload/source/data/integritychecksPASS;31protected artifacts +200legacy/500GenZ/contextreference/validation/test/SQLite unchanged. No externalAPI/download/paidGPU/reset/push/deploy. Follow-upstatusCOMPLETE. Current report docs/ai-update/final-report/GENZ500_TRAIN_R05.md; resume evidence reports/ai_update/train_genz500_r05_20261103/progress.json. Next: keep default, review measured validation and remaining release evidence before any model adoption.


## CURRENT camping regression follow-up — IN_PROGRESS

User pasted camping30 demo. Existing synthetic references and actual V1.1/r05 API before outputs are frozen in reports/ai_update/camping_context_20261103/. Fix context/target/repeated with general rules; no training, checkpoint/threshold/data changes. Prior DONE states preserved; completion requires paired regression and actual local demo smoke.


## CURRENT camping context follow-up — COMPLETE

Pastedcamping30reproduced at actual V1.1:8020/r05:8021; frozen existing AI references, not human gold. General clause patterns + abuse-endorsement disambiguation + APOLOGY_ACCEPTANCE distinguish accepting apology from self-blame. Contextv3/repeatedv4 qualifies grounded context attacks independently of raw0.41, additive attack_instance_basis. Existing target-v3/legacyengine/lexicon unchanged. Actual after:30/30reference labels bothmodels; exact U04→U03evidence[c09,c12,c15,c18], no apology/recovery added; c18notDEFENSE,c25acceptsapology. All rawscores/legacyfields unchanged.

Full540PASS/1warning, UIbuildPASS, servednewUI/actuallegacy+V2API200. Paired890originalV1cachedscores:1improvement/0newlabelerrors/1eventchange/no newCLEAN-reference evidence. Existing developmenterrors remain documented; no freshblind claim.31protected hashes+all datasets/test/SQLite/V1/V1.1/candidates unchanged. No train/promotion/deploy/auto-hide. Prior DONE and r03/r04/r05promotion rejections preserved.

Current report docs/ai-update/final-report/CAMPING_CONTEXT_RECOVERY.md. Evidence reports/ai_update/camping_context_20261103/; currentownedPIDs in demo_after_server_state.json, older demo PID files superseded. RefreshCtrl+F5 at8020or8021 and reanalyze. No other task started.


## CURRENT independent-readiness session — safe scopes complete, real criteria BLOCKED

Current task criteria (historical DONE status lines remain untouched):

| Task | Scoped status |
|---|---|
| T022 | DONE — Indirect attack/context development on frozen synthetic references |
| T024 | DONE — Target inference from actual attack clauses and available participant metadata |
| T025 | DONE — Repeated-evidence regression; missing targets still abstain, no promised perfect recall |
| T027 | DONE — Source/inventory audit, paused collector guard, anonymized quarantine and human review preparation |
| T028 | BLOCKED — Independent real200 cohort |
| T029 | BLOCKED — New training |
| T030 | DONE — Synthetic development evaluation tooling and before/after |
| T031 | DONE — Actual local registry/shadow/fallback/rollback mechanics using existing candidate |
| T032 | DONE — 574root/177Social regressions and isolated5process integration E2E |
| T033 | DONE — Provisional technical report with missing evidence explicit |

8safe scopesDONE; T028real/T029trainingBLOCKED. T029preparationDONE, no training. Existing synthetic T028DONE and completed CPU runs remain historical, not real evidence. Data valid0/200/human labels0; old30/313NOT_FOUND;6source options audited/no corpus admitted; collectorPAUSED/0networkrequests/no more contact/path questions.

Synthetic890/known886 only: FP20→18,FN9→6,MacroF1.889700→.909296; target30→34/54correct(P1.0,R.5556→.6296); repeatedTP2→3/10,FP0,FN8→7. No new label errors;18FP/6FN/20targetabstentions/7repeatedmisses remain. No human-gold/real-world claims.

574rootPASS/177SocialPASS,5processfixtureE2E/browserPASS(tempSQLite/cleanup/privacy), real-reviewChromePASS(no submissions), actualregistryshadow/fallback/rollbackPASS(nativeexit0), actualV1.1/r05live5threads/90comments each rawinvariantPASS. Current codecontext-v4/target-v4/repeated-v4; default/V1/0.41/checkpoints/source labels/test/liveDB unchanged.

Files: context_signals.py,target_signals.py,signal_engine.py,contractschema; real_dataset collector/core/store/intake/leakage/review_app/validation/UI; reusable evaluate_synthetic_signals.py, training preflight guards/config, local registry/config, tests/template/docs. Evidence reports/ai_update/independent_readiness_20261103/; report docs/ai-update/final-report/INDEPENDENT_READINESS.md. Current criteria tasks/CURRENT_AI_SCOPE.json. Human UI8010; demo8020V1.1/8021experimentalr05 reloaded code only. Current PID states in this evidence directory; prior PID files superseded.

Next only when real permitted material exists: source/privacy/leakage verification and supported adapter, then same-human Round1/Round2 and evaluation lock. No new training without all prerequisites and explicit approval. No push/deploy/production changes; no other ready requested task remains.


## Synthetic experiment r06 — historical execution timeline (completed below)

Latest attached request authorizes actual free-resource synthetic training separately from blocked real T028/T029 acceptance. Reuse canonical500 without changing original text/AI labels/splits; derive a three-way family view, no real training due unreverified local-copy rights. One new CPU frozen-encoder/full-classifier-head candidate, max4threads/900s/cost0. Different from r05: synthetic-only, class balancing, synthetic validation early stopping, originalV1 base. Real/general training remains disabled; exact r06 config/receipt is the only local exception. Evidence reports/ai_update/synthetic_experiment_r06_20261103/.


## r06 completed — EXPERIMENTAL, not independent acceptance

5experimental milestonesDONE: reuse/validate500threads(5115comments;CLEAN4667/TOXIC369/UNCERTAIN79), prepare4398synthetic-only rows, actual CPUhead training207steps/3epochs/79.75s, actual V1/r05/r06 comparison, checkpoint/report/progress. No new utterances generated. Encoder frozen; threshold0.41/V1/default/oldcheckpoints/test/SQLite preserved; one-run scope consumed.

Raw MacroF1 validation V1.688581/r05.670259/r06.823834; challenge V1.779884/r05.787645/r06.828798. Validation/challenge already viewed in rule research, synthetic_reference only, not human gold/real-world evidence. R06 challenge FP9/FN5; target9/20correct(P1,R.45), repeatedTP0/FP0/FN5. No claim these errors are solved; no production activation.

Tests: actual full root `python -m pytest -q --basetemp reports/ai_update/test_tmp/r06_final` →591PASS/0FAIL/one deprecation warning. Earlier notebook migration failure fixed and rerun; final_tests.log retains evidence. No changed expected labels. No frontend edits/build. Hash audit integrity.json preserves27historical task statuses and source/model/test hashes.

Files changed: scripts/prepare_t029_training.py, scripts/train_t029_candidate.py, new scripts/synthetic_data/experiment.py, scripts/evaluate_synthetic_candidate.py, tests/test_synthetic_experiment.py, configs/t029_synthetic_only_cpu_r06.json, notebooks/T029_Synthetic_Experimental_R06.ipynb; new datasets/synthetic_genz/ and models/candidates/T029_synthetic_only_head_cpu_20261103_r06/; reports/ai_update/synthetic_experiment_r06_20261103/; task/scope progress and docs/ai-update/final-report/SYNTHETIC_R06_EXPERIMENT.md. Existing runtime AI/backend/frontend unchanged in this experiment.

T028realBLOCKED0/200,humanlabels0; old30/313NOT_FOUND (previous audit). Formal T029/T030 real criteria still BLOCKED; historical DONE preserved. FullGPU notebook prepared/unexecuted. WikimediaPAUSED. Next: review saved results / target-repeated regression or permitted real data plus same-human Round1/Round2; no automatic new train or promotion. Resume context and safe validation commands: reports/ai_update/synthetic_experiment_r06_20261103/README.md; machine state progress.json; current authority tasks/CURRENT_AI_SCOPE.json.


## Current verified follow-up — repeated/context/target v5

T028 BLOCKED(real0/200,humanlabels0); T029 formalBLOCKED(r06 experimental already trained, no r07); T030/T031/T032/T033 PARTIAL (safe synthetic/local work verified; missing independent acceptance, no production authorization). Historical DONE preserved; current scope tasks/CURRENT_AI_SCOPE.json.

Five event regression red5FAIL before fix; old challenge repeated0/5→5/5, evidence10/10correct. Fresh post-freeze12threads/74comments:2/6→4/6, precision1/recall.6667, evidence8/8correct;2misses retained, no post-score rule changes. Canonical500/5115 unchanged. Broad890replay known886 FP18→18/FN6→4; repeated2/10→8/10,FP0,evidence20/20; no new label errors. Old prose34target/3events superseded by archived/recomputed33/54and2/10; DANCE lacks grounding refs and cannot count as TP.

Tests610rootPASS/177SocialPASS/browserfiveprocessE2EPASS; actual r06 shadow/fallbackV1/ASGI200→503→200PASS. Browser uses fixtureAI/disposableSQLite, actual models tested separately. Model/default/V1/0.41/test/SQLite/reference labels unchanged; no training/deploy. Runtime context_signals.py/target_signals.py/signal_engine.py+contract defaults; two new test files, reusable evaluate_repeated_recovery.py,12new fixture JSONs/manifest, isolated registry, real-cohort development exclusions, report/progress/task notes. Full file inventory/hashes in reports/ai_update/repeated_recovery_20261103/ARTIFACTS.json.

Report docs/ai-update/final-report/REPEATED_RECOVERY_V5.md; evidence/reproduction reports/ai_update/repeated_recovery_20261103/README.md. Next: real permitted source/human rounds for acceptance; new predeclared holdout before further rule tuning. Do not train r07, recreate500, change default or call synthetic human gold.


## Stabilization & Evaluation Readiness — DONE safe scope

Two residual repeated events audited: unseen cục_chì metaphor;66minute gap beyond30minute reciprocal window. No technical bug proven; no rule/label changes or re-inference to obtain6/6. Preserve old5/5/fresh4/6(P1,R.667,evidence8/8).

READINESS_LOCK_T028_v2.json seals1311files(model/rule versions, datasets/manifests/reference labels, raw/ablation/confusions/FPFN/target/repeated and integration evidence). Read-only verificationPASS; no resealing. Latest620rootPASS/0FAIL/1warning,48review protocolPASS included; Chrome empty-corpus UIPASS/0submissions/0AI. Prior177Social/browserE2E/actual shadow+rollback preserved and hash-verified, not rerun. Protected259artifacts/V1/default/0.41/test/SQLite unchanged.

T028/T029formalBLOCKED; T030/T031/T032/T033PARTIAL. Technical T032, frozen T030synthetic and provisional T033 handoffDONE; independent acceptance still absent. Real0/200/humanlabels0, collectorPAUSED. Manualintake/anonymization/CSRF/provenance checks and same-humanRound1/Round2 tested; manual inbox still needs verified receipt/supported adapter before source admission. StaleRound2 cannot lock after Round1 revision. Empty-source URL API500 reproduced, one-line min_length1 fix now422/no key/inbox writes; original lock preserved, tooling-v2 lock with SHA lineage. No labels requested/fabricated, no r07/train/deploy/default switch.

Report/checklist/architecture/dataset/training/comparison/error analysis/demo: docs/ai-update/final-report/FINAL_READINESS_REPORT.md. Evidence/reproduction: reports/ai_update/stabilization_20261103/README.md; lock READINESS_LOCK_T028_v2.json, latest-test/report binding READINESS_ATTESTATION.json. New code scripts/verify_ai_readiness_lock.py; scripts/real_dataset/intake.py(min_length1fix); new tests test_ai_readiness_lock.py/test_real_review_lock_readiness.py; AI/Social/frontend/model unchanged. Current authority tasks/CURRENT_AI_SCOPE.json. Next: permitted/source-verifiable real200, privacy/leakage, same-human two rounds and evaluation lock; then predeclared independent evaluation and formal sign-off. No automatic training.


## Fresh10 recovery — 04/11/2026, research only

648root tests PASS/0FAIL/1deprecation warning (28Fresh10 tests included). Imported10analysis JSONs/originalreference CSVs byte-preserved. Fresh10 development195binary: TP15→18,FP6→1,FN7→4,TN167→172,MacroF1.830105→.931861,target5→16/22,repeated2→6/7(P1/R.8571),evidence15/15correct,15/19coverage. Old890cached-V1 regression classification/target/repeated unchanged, no new errors.

Initial48comment post-freeze challenge exposed one new apology/report FP; original source/lock/outputs retained, then explicitly converted to development. Generic reporting-scope fix and v6.1 refreeze; another24comments first-scored after freeze: TP5/FP1/FN1/TN17,MacroF1.888889,target5/6,repeated1/2(P1/R.5),evidence2/2correct,2/4coverage. One metaphor FN/raw-score FP remain; no post-score tuning. All labels synthetic_reference, not human gold/independent real; no label edits.

Opt-in processor services/moderation-ai/app/experiments/fresh10_v6.py; evaluator scripts/evaluate_fresh10_recovery.py and evaluate_fresh10_challenge.py; tests/test_fresh10_recovery.py. API/Dashboard stillv5. V1/r06/default/0.41/readiness1311hashes unchanged; no training/deploy. New fixture exclusion extension prepared but NOT merged into locked runtime exclusions. T028/T029formalBLOCKED,T030–T033PARTIAL; historicalDONE preserved. Report docs/ai-update/final-report/FRESH10_RECOVERY.md, evidence reports/ai_update/fresh10_recovery_20261103/README.md, hashes ARTIFACTS.json. Continue only with separate future release/evaluation scope; no automatic activation or new training.


## NOV10 root-cause audit — 04/11/2026

Audit complete; rules/checkpoints/default unchanged. Imported10inputs/10v6.1analysis/200comments and original synthetic_reference CSVs. Exact wire replay10/10; 7attack predicate families have0matches before/after masking on all200comments, so context.attack_candidatefalse causes infer_target earlyreturn and0instances. Actual canonical ASGI r06 probe63comments PASS: contextcalled20times/thread forTest12/15/20, rawdiff0; positivecontrol repeatedPASS. Not a Dashboard-v5 assumption or global disable. Eight referencepairs10–20min have0qualifiedinstances, not time-window rejection.

NOV10 unchanged:199binary,TP7/FP3/FN15/TN174,MacroF1.694160,target0/22,repeated0/8. OldFresh10+890cachedregression unchanged.24adjudication candidates pending/no reference edits. Versioned development_exclusions.research_20261104.json registers NOV10/Fresh10/challenges;10/10NOV10 excluded via explicit overlay preflight, sealed defaultmanifest/loader unchanged.

Standardroot677PASS/0FAIL/1warning. Separate supplemental quote-scope red probes2FAIL/1PASS: new locked24comment challenge found narrative-quote attribution bug; NOT fixed or hidden. Challengev6.1:23binary TP6/FP1/FN0/TN16,Macro.946387,target5/6,repeated1/2(P1/R.5),evidence2/2correct/2of4referencecoverage. No post-inference tuning. Audit scope complete, quote fix/indirect coverage still OPEN; next revision needs red-before-fix and fresh challenge. Readiness1311SHA PASS; no train/deploy/DB/default edits. FormalT028/T029BLOCKED,T030–T033PARTIAL/historicalDONE preserved.

Report docs/ai-update/final-report/NOV10_ROOT_CAUSE_AUDIT.md; evidence/reproduction reports/ai_update/nov10_audit_20261104/README.md; labels-to-review adjudication_candidates.csv; source/hash inventory ARTIFACTS.json.


## Controlled v6.2 research — 04/11/2026, EXPERIMENTAL

Completed safe research cycle, no formal acceptance/promotion. New research_v62.py leaves sealedv6.1/default untouched. Two quote expectation RED→GREEN (same inputs/assertions; currentv6.2 replay, originalv6.1JSON/probes unchanged), outside assignment/attribution/cau noun/cau addressee/NFC spans handled; new outsidequote attacks preserved.43processor+2adjudication targetedPASS; full722rootPASS/0FAIL/1warning.24owner cases exported with full20commentcontexts and blank decisions; latest adjudication_v3/HTML+CSV, timestamped decision annotationversions, no humanreview/gold or originalreference edits.

Bounded indirect grammars with negativecontrols; weak sarcasm cues diagnostic-only pending adjudication. NOV10TP7→8,FP3→3,FN15→14,TN174→174,Macro.694160→.719137,target0→2/22,repeated0→1/8(P1/R.125),evidence2/2correct but2/21coverage/full0of8events. Fresh10/old890 no regression; all7developmentcohorts no newlabelerrors. Some viewedchallenge gains; do not call independent.

V62_LOCK before new6threads/36comment authoring/inputfreeze/inference. One actualr06CPUoffline scorecache, no post-score tuning. Challengev6.1→v6.2 Macro.731744→.911330,TP3→6,FP0→0,FN5→2,TN28→28,target1→6/8,repeated0→2/3(P1/R.667),evidence4/4correct/4of6coverage. Two unseen metaphor/exclusion misses remain unchanged.52remainingbinaryerrors/12UNCERTAIN across8cohorts saved; emittedtarget/evidenceerrors0 on groundedreferences. Newversionedexclusionoverlay verifies10NOV10+6newchallenge excluded; defaultloader unchanged.

V1/r06/default/.41/readiness1311SHA unchangedPASS; no Dashboard/default runtime/DB edits, trainingr07, deploy or promotion. T028/T029formalBLOCKED,T030–T033PARTIAL; historicalDONE preserved. Report docs/ai-update/final-report/CONTROLLED_V62_RESEARCH.md; progress/evidence/changelog/SHA/reproduction reports/ai_update/v62_research_20261104/. Next owner adjudication when convenient, future independent research revision only; no automatic activation.


## Local realtime/studio extension T034–T043

See [AI rollout order](moderation-ai/TASK_ORDER_AI.md), [execution state](moderation-ai/AUTO_EXECUTION_STATE.json), [dependencies](moderation-ai/TASK_DEPENDENCIES_T034_T043.md). New tasks do not change historical statuses or formalT028/T029 blockers.


### Verified local task status (04/11/2026)

| Task | Status | Evidence |
|---|---|---|
| T034 | DONE_VERIFIED | [T034-realtime-moderation-architecture.md](moderation-ai/T034-realtime-moderation-architecture.md) |
| T035 | DONE_VERIFIED | [T035-durable-live-messaging-ai-jobs.md](moderation-ai/T035-durable-live-messaging-ai-jobs.md) |
| T036 | DONE_VERIFIED | [T036-incremental-conversation-analysis.md](moderation-ai/T036-incremental-conversation-analysis.md) |
| T037 | DONE_VERIFIED | [T037-live-conversation-client.md](moderation-ai/T037-live-conversation-client.md) |
| T038 | DONE_VERIFIED | [T038-live-moderator-board.md](moderation-ai/T038-live-moderator-board.md) |
| T039 | DONE_VERIFIED | [T039-dataset-center.md](moderation-ai/T039-dataset-center.md) |
| T040 | DONE_VERIFIED | [T040-annotation-studio.md](moderation-ai/T040-annotation-studio.md) |
| T041 | DONE_VERIFIED | [T041-training-studio.md](moderation-ai/T041-training-studio.md) |
| T042 | DONE_VERIFIED | [T042-evaluation-studio-model-registry.md](moderation-ai/T042-evaluation-studio-model-registry.md) |
| T043 | DONE_VERIFIED | [T043-realtime-studio-e2e-handoff.md](moderation-ai/T043-realtime-studio-e2e-handoff.md) |

Formal T028/T029 remain BLOCKED; T030?T033 PARTIAL. The10new local tasks do not replace real human-gold acceptance. No further automatic training is pending. Final report: ../docs/ai-update/final-report/T034_T043_FINAL_REPORT.md.

## Social Feed v2 current acceptance

The new10per-file requirements are merged by ID. Current acceptance: [AI order](moderation-ai/TASK_ORDER_AI.md#social-feed-v2--current-acceptance), AUTO_EXECUTION_STATE.json/social_feed_v2. Historical statuses remain unchanged; formal T028/T029 BLOCKED and T030–T033 PARTIAL.
