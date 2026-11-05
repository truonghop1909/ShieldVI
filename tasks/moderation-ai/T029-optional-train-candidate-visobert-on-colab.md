> CURRENT verified follow-up: T028/T029 formal BLOCKED; T030–T033 PARTIAL. Safe synthetic/local evidence verified, no real/human-gold acceptance or production activation. Historical DONE below is preserved. See [v5 report](../../docs/ai-update/final-report/REPEATED_RECOVERY_V5.md) and ../CURRENT_AI_SCOPE.json.

# T029 — Bounded local CPU head-training candidate

- **Status:** DONE
- **Priority:** P2
- **Dependencies:** T027,T028

## Current authorized scope

Train only classifier head with frozen V1 encoder using prepared GenZ500+ViCTSD. Max4CPUthreads/900seconds, no paid/API/GPU resource, one new candidate. Full encoder fine-tune GPU remains NOT_RUN, not claimed achieved.

User explicitly requested running all tasks and revising blocked tasks. This revision removes hardware-specific/deploy prerequisites, not evidence or source-integrity checks. No task becomes DONE from documentation alone. Preserve original0.41/weights/test/SQLite and keep AI labels separate from gold.

## Acceptance

Actual optimizer steps on head only; encoder hash unchanged; reproducible bounded config/seed/source hashes, validation selection, new checkpoint/tokenizer/config reload and real inference. Record metrics even if candidate is worse; fullGPU mode remains separate.

<details>
<summary>Earlier GPU/deployment-oriented scope and evidence — preserved history</summary>

# T029 — OPTIONAL — Train candidate ViSoBERT on Colab

- **Status:** BLOCKED
- **Priority:** P2 / approval required
- **Dependencies:** T027,T028 + USER APPROVAL
- **Owner:** Codex đề xuất code, người dùng duyệt
- **Scope:** cập nhật AI ShieldVI, không phải tự động bật xử phạt

## Mục tiêu

Chỉ sau khi người dùng duyệt, tạo và chạy **ứng viên mới** fine-tune với hard cases, không đè V1.

## Các bước triển khai

1. Trước tiên chỉ tạo notebook/script + config và yêu cầu người dùng duyệt dataset version, GPU cost, epochs, batch size, LR, seed, checkpoint output, tiêu chí stopping.
2. Pin môi trường compatible V1 (`transformers==4.57.3`, hub 0.36.2), restart Colab và verify imports; xác minh checkpoint gốc + threshold 0.41.
3. Train theo protocol G2-S của T028 với augmentation ratio/thí nghiệm có kiểm soát; validate trên ViCTSD validation tách khỏi train, early stopping theo validation, không dựa test. Benchmark hội thoại thật G2-R là mở rộng tùy chọn.
4. Lưu model candidate mới `/content/drive/MyDrive/shieldvi_candidates/<run_id>/` + config/tokenizer/threshold manifest; model baseline read-only.
5. Dataset synthetic training luôn ghi provenance và không đại diện đánh giá thật.
6. Không tự chạy train nếu thiếu GPU/approval; không hứa candidate cải thiện.

## Phạm vi file

- Codex **phải xác minh** service thực tế ở `app/` legacy hoặc `services/moderation-ai/`; chỉ tạo/sửa file hợp lý trong đó.
- Test và tài liệu trong `tests/`, `docs/ai-update/`, `datasets/` hoặc service-scoped equivalents.
- Không sửa Social DB, baseline checkpoint, train/test split hay nội dung fixture trừ khi task nêu rõ và người dùng duyệt.

## Kiểm thử / bằng chứng

Training run log có seed/config/versions, checkpoint candidate load thử và inference thật. Nếu chỉ viết notebook: `PREPARED_NOT_TRAINED`, không đánh DONE như đã train.

## Acceptance criteria (Definition of Done)

Candidate mới không đụng baseline, validation report có số liệu, không phát sinh test leakage.

## Chặn rủi ro / stop conditions

- Nếu thiếu dữ liệu/provenance theo protocol đã chọn, checkpoint, GPU hoặc quyền phù hợp: ghi `BLOCKED` + lý do, không giả lập thành PASS.
- Nếu xuất hiện breaking change hoặc metric xấu đi rõ ràng: báo tác động, rollback và xin duyệt.
- Task chỉ `DONE` sau khi có evidence đúng; công việc chưa chạy cần ghi `CHƯA CHẠY`.

## Nhật ký thực hiện (Codex cập nhật)

- Ngày/commit:
- Các file đã sửa:
- Test/command thực tế:
- Kết quả PASS/FAIL/CHƯA CHẠY:
- Metric/số case thay đổi (nếu áp dụng):
- Blocker / rủi ro:
- Task đề xuất tiếp theo:

### 03/11/2026 — user yêu cầu làm theo task

- **BLOCKED; preparation=PREPARED_NOT_TRAINED**. Không ghi DONE hoặc coi là đã train.
- Đã chuẩn bị loader và leakage audit cho 6.942 ViCTSD + 1.994 nhãn AI được người dùng chọn dùng = **8.936 train rows** (22,31% synthetic), 54 UNCERTAIN riêng; không exact/near overlap tại ngưỡng đã nêu, holdout gốc bất biến.
- Đã tạo `configs/t029_candidate.json`, `scripts/prepare_t029_training.py`, `scripts/train_t029_candidate.py`, notebook `notebooks/T029_Train_Candidate_Prepared.ipynb`, receipt đề xuất approved=false. Không chạy notebook/optimizer/GPU hoặc CPU train.
- Hyperparameters: V1 gốc, full fine-tune, max 3 epochs, batch 8 × accumulation 2, LR 2e-5, max_length 128, seed 20261103, patience 1, threshold 0.41, GPU Colab, 3.600 giây tối đa. Output candidate mới, không thay default.
- Test liên quan: `pytest tests/test_t029_preparation.py tests/test_synthetic_training_export.py -q -p no:cacheprovider --basetemp reports/ai_update/test_tmp/T029_prepared_tests` → **17 passed, 1 warning**, exit 0. Test không thực hiện train model; kiểm gate chặn trước optimizer, leakage và hash/artifact thật.
- Preflight thực tế BLOCKED: thiếu G2/T028, thiếu receipt G3 chính xác, CUDA unavailable (torch 2.15 CPU); transformers 4.57.3/hub 0.36.2 đúng. Không nới gate vì thiếu dữ liệu.
- Base smoke thật tách riêng: `reports/ai_update/T029/base_smoke.json`; forward CPU, không optimizer hoặc candidate training. Chưa có candidate mới/validation improvement/reload candidate để nghiệm thu.
- Xem [artifact và điều kiện tiếp tục](../../docs/ai-update/T029_TRAINING_PREPARATION.md). Việc tiếp theo: hoàn tất T028/G2 và duyệt cấu hình/resource G3, không yêu cầu gán lại synthetic hoặc tự làm T030.

Final verification: **344 passed, 1 warning**, exit0 (`reports/ai_update/T029/pytest_full_release.txt`); real V1 CPU forward smoke PASS, optimizer_steps=0; 31 protected hashes unchanged; `final_audit.json` PASS. Notebook unexecuted, approval receipt false, no candidate created. Status remains BLOCKED/PREPARED_NOT_TRAINED.

### Đồng bộ tài liệu 03/11/2026 — T028 chuyển synthetic

Dependency T028 nay là AI-authored synthetic/G2-S, không bắt buộc contact hoặc nhãn người. Quyền dùng nhãn AI đã có; G3 về config/resource vẫn cần duyệt. Status giữ BLOCKED vì readiness code chưa đồng bộ protocol, G3 chưa đạt và local không có CUDA; các log G2 real trước đây là lịch sử, không phải yêu cầu hiện hành. Không chạy train trong lần sửa tài liệu.

### Autonomous REAL + GenZ500 — 03/11/2026

GenZ research data PREPARED_NOT_TRAINED:11340 rows=6942 ViCTSD+4398 synthetic; synthetic38.78%, holdouts and challenge no exact/near overlap. New config configs/t029_genz500_candidate.json; prepared reports/ai_update/T029/genz500_prepared. Preflight actual blockers: matching G3 resource receipt absent; CUDA unavailable. G2-S eligibility passes without changing real evaluation gate. Original config/default real protocol preserved. No optimizer/candidate.

Root suite355PASS plus24 targeted gate testsPASS (overlapping tests, do not sum); Social177PASS; frontend builds3PASS; real-model development/fallback smokePASS. Threshold/checkpoint/independent test unchanged. Current scope overrides prior single-task/synthetic-only notes; preserve older logs as history.

Latest scope note — GAME_RANK_30: T028 synthetic-only DONE; REAL/contact is not a research-training prerequisite. T029 status remains BLOCKED because localCUDA/G3 resource receipt is missing. No fine-tune performed; latest prepared config remains t029_genz500_candidate.json.

</details>

## Current CPU experiment evidence — DONE

Actual head-only training completed:11340rows(6942ViCTSD+4398synthetic),3epochs,534optimizersteps,400.94seconds.96,975,360encoderparametersfrozen;592,130headparameterstrained; only classifier.* weights changed. Encoder hash/base/source hashes unchanged; original0.41 retained. Validation selectedepoch3: MacroF1=.75304166 vsV1=.76370125, worse; no improvement claim. New checkpoint/tokenizer/config reload error0. Output models/candidates/T029_genz500_head_cpu_20261103_r03, training_report.json. Fullencoder/GPUfine-tune NOT_RUN; earlier GPU-only scope remains historical. T031 now reviews actual candidate and may reject promotion.


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


## Latest independent-readiness criteria

Historical status/evidence above preserved. Current scoped status: **BLOCKED** — New training. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/INDEPENDENT_READINESS.md. New criteria never turn missing real/human evidence into DONE. Evidence:574root/177Social/E2E/UI/registry/live smoke PASS; valid real0, no new training.


## r06 synthetic-only experiment evidence

Latest explicit request completed a separate EXPERIMENTAL synthetic-only CPU head run:4398rows/207steps/79.75s;500reused threads, no independent human gold. Raw validation MacroF1 .823834/challenge .828798;591root testsPASS. OriginalV1/0.41/source/test/default untouched, no promotion. T028real0/200 and formal T029/T030 real acceptance remain BLOCKED; historical status above is preserved, not new real acceptance. See [report](../../docs/ai-update/final-report/SYNTHETIC_R06_EXPERIMENT.md), tasks/CURRENT_AI_SCOPE.json and AUTO_PROGRESS.md. One-run authority consumed; no further train authorized.


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
