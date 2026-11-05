> CURRENT verified follow-up: T028/T029 formal BLOCKED; T030–T033 PARTIAL. Safe synthetic/local evidence verified, no real/human-gold acceptance or production activation. Historical DONE below is preserved. See [v5 report](../../docs/ai-update/final-report/REPEATED_RECOVERY_V5.md) and ../CURRENT_AI_SCOPE.json.

# T031 — Local candidate registry, shadow and rollback decision

- **Status:** DONE
- **Priority:** P2
- **Dependencies:** T030 and actual T029 candidate

## Current authorized scope

Evaluate new candidate in isolated local shadow, verify hashes/schema/fallback/rollback, record allow-shadow/reject decision from validation and final test audit. No deployment/default switch; production activation is outside this revised task.

User explicitly requested running all tasks and revising blocked tasks. This revision removes hardware-specific/deploy prerequisites, not evidence or source-integrity checks. No task becomes DONE from documentation alone. Preserve original0.41/weights/test/SQLite and keep AI labels separate from gold.

## Acceptance

Real baseline/candidate comparison, SHA256-bound local registry inventory, explicit research decision, opt-in shadow, V1 fallback and rollback smoke with actual candidate. Production/default unchanged. Candidate may be rejected; rejection with evidence completes review, not deployment.

<details>
<summary>Earlier GPU/deployment-oriented scope and evidence — preserved history</summary>

# T031 — OPTIONAL — Model registry, shadow and rollback

- **Status:** BLOCKED
- **Priority:** P2 / approval required
- **Dependencies:** T030 + USER APPROVAL
- **Owner:** Codex đề xuất code, người dùng duyệt
- **Scope:** cập nhật AI ShieldVI, không phải tự động bật xử phạt

## Mục tiêu

Thiết kế chuyển checkpoint candidate có kiểm soát, không overwrite model V1 hoặc tự deploy.

## Các bước triển khai

1. Tạo manifest version của model/rules/dataset/threshold/sha256/git commit (không chứa secret).
2. Có flag/select MODEL_PATH candidate chạy shadow, fallback V1; không thay default đang chạy trước khi người dùng duyệt.
3. Smoke inference thật (model_loaded, compare score schema), API contract, timeout, failure recovery; rollback test.
4. Chốt review cải thiện và tradeoffs FP/FN; người dùng phê duyệt rõ và giữ release notes.
5. Không tự bật HIGH auto-hold, không auto-ban và không xóa lịch sử kiểm duyệt.
6. Nếu candidate tệ hơn hoặc khó tái lập → REJECT, giữ V1.

## Phạm vi file

- Codex **phải xác minh** service thực tế ở `app/` legacy hoặc `services/moderation-ai/`; chỉ tạo/sửa file hợp lý trong đó.
- Test và tài liệu trong `tests/`, `docs/ai-update/`, `datasets/` hoặc service-scoped equivalents.
- Không sửa Social DB, baseline checkpoint, train/test split hay nội dung fixture trừ khi task nêu rõ và người dùng duyệt.

## Kiểm thử / bằng chứng

Test model V1 + candidate isolation, rollback recover, integration smoke with service restart and audit; if no GPU/real model, mark blocked.

## Acceptance criteria (Definition of Done)

Không đè V1, có quyết định approve/reject và rollback, production unchanged nếu chưa duyệt.

## Chặn rủi ro / stop conditions

- Nếu thiếu dữ liệu, license, nhãn người kiểm duyệt, checkpoint, GPU hoặc quyền phù hợp: ghi `BLOCKED` + lý do, không giả lập thành PASS.
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

### Autonomous REAL + GenZ500 — 03/11/2026

Local preparation COMPLETE: configs/model_registry.local.json, opt-in app/model_registry.py; validates artifact hashes/.41, explicit shadow and V1 fallback. Not imported by production main or default selector. Real V1 fallback/API smoke PASS after deliberately injected primary-load failure;503->200 recovery, legacy/v2 raw equal. Candidate absent, no candidate-versus-baseline tradeoff/release decision; activation remains unapproved. Local registry proof reports/ai_update/autonomous_20261103/local_registry_smoke.json.

Root suite355PASS plus24 targeted gate testsPASS (overlapping tests, do not sum); Social177PASS; frontend builds3PASS; real-model development/fallback smokePASS. Threshold/checkpoint/independent test unchanged. Current scope overrides prior single-task/synthetic-only notes; preserve older logs as history.

</details>

## Actual local review complete — DONE

Actual candidate and baseline/default loaded, frozen validation/final-test audit and890synthetic diagnostics complete. Decision REJECT_PROMOTION_KEEP_EXISTING_DEFAULT: validation MacroF1original.763701→candidate.753042, plus1newGenZfalsepositive. TestMacroF1.738958→.748633 does not override validation/regression gates. GAME30and exact4attackevidencepass. Explicit shadow loads; implicit selection rejected; deliberate loaderfault falls back to verified realV1, rollbackASGI503→200; legacy/V2/internalSocialcontract200 and rawscoreidentityverified. No production/default/policy/DB change.

434rootPASS/1warning; source/encoder/checkpoint/data/test hashes unchanged. New registry configs/model_registry.cpu_r03.local.json; candidate/review/data/gate hashes in reports/ai_update/all_tasks_cpu_20261103. FullGPU/deployment not claimed; local review/rejection meets revised task acceptance. See docs/ai-update/final-report/CPU_HEAD_COMPLETION.md.


## Follow-up r04 — revise refused work and continue

**Follow-up status: IN_PROGRESS.** Prior task DONE and r03 rejection are preserved. One additional bounded CPU head-only research attempt:4threads/900seconds/cost0. New config lowers synthetic loss .5→.1 and LR3e-5→1e-5, increases distillation .5→1.0. Encoder/data/0.41 stay fixed. Historical validation-only selection; no test rescore or example-specific tuning. This exploratory follow-up after the old test was inspected is not fresh independent evaluation. Original quality gates remain frozen; no production promotion.

Evidence: `reports/ai_update/candidate_revision_20261103/predeclared_experiment.json`; current progress in `tasks/AUTO_PROGRESS.md`. Completion requires actual optimizer/reload/integrity evidence and a validation verdict.


## CURRENT FOLLOW-UP r04 — COMPLETE, promotion disabled

Actual bounded CPU follow-up completed: 356optimizersteps/2epochs/431.84s, encoderfrozen, newcheckpoint r04. ValidationMacroF1 original0.763701/r03.753042/r040.756865; toxicP0.613065/R0.525862. Decision **REJECT_PROMOTION_KEEP_EXISTING_DEFAULT**, unchanged original gates. No new test/challenge inference or promotion; historical evaluation is not freshblind. Prior27task DONE states preserved. Follow-up status COMPLETE for execution/review, not model acceptance.

Root448PASS/1warning;40preflightPASS.31protectedhashes+all200/500source datasets+12contextfixtures/userreference/validation/test/SQLite/defaultV1.1 unchanged. No paidGPU/fullencodertraining/upload/download/push/deploy. Files: scripts/review_t029_validation.py, tests/test_t029_validation_review.py, configs/t029_genz500_cpu_head_r04.json; task/index/progress and3AI docs updated; newcandidate/reports separate.

Current evidence reports/ai_update/candidate_revision_20261103/; report docs/ai-update/final-report/CANDIDATE_REVISION_R04.md. Resume from this section, not historical IN_PROGRESS/BLOCKED notes above. No remaining task ready in the27existing files; next: Stop this recipe; retain default and negative result. Do not relax gates or rescore test.


## Latest independent-readiness criteria

Historical status/evidence above preserved. Current scoped status: **DONE** — Actual local registry/shadow/fallback/rollback mechanics using existing candidate. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/INDEPENDENT_READINESS.md. New criteria never turn missing real/human evidence into DONE. Evidence:574root/177Social/E2E/UI/registry/live smoke PASS; valid real0, no new training.


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
