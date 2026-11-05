> CURRENT verified follow-up: T028/T029 formal BLOCKED; T030–T033 PARTIAL. Safe synthetic/local evidence verified, no real/human-gold acceptance or production activation. Historical DONE below is preserved. See [v5 report](../../docs/ai-update/final-report/REPEATED_RECOVERY_V5.md) and ../CURRENT_AI_SCOPE.json.

# T032 — Social AI integration & offline safety E2E

- **Status:** DONE
- **Priority:** P2
- **Dependencies:** T026,T030 (+T031 optional)
- **Owner:** Codex đề xuất code, người dùng duyệt
- **Scope:** cập nhật AI ShieldVI, không phải tự động bật xử phạt

## Mục tiêu

Bảo đảm phiên bản AI mới tương thích Social API worker/UI, Admin quyết định visibility, retry khi offline.

## Các bước triển khai

1. Xác định contract hiện hành giữa `social-api` và `moderation-ai`; schema version/signal optional/backward compatible.
2. Test user đăng bình luận benign → social visible; toxic → signal review, không auto-hide khi HIGH chưa được duyệt.
3. Tắt AI rồi đăng nội dung → social lưu job UNKNOWN/PENDING và retry; bật AI → job hoàn thành, không mất content.
4. Test duplicate job/idempotency, race admin review vs model updated, appeal, audit; không cho AI ghi Social DB.
5. Frontend hiển thị raw AI, lexicon, context, evidence, policy risk và visibility rõ ràng.
6. Kiểm tra không rò PII trong logs/metrics; hạ cấp gracefully khi model unavailable.

## Phạm vi file

- Codex **phải xác minh** service thực tế ở `app/` legacy hoặc `services/moderation-ai/`; chỉ tạo/sửa file hợp lý trong đó.
- Test và tài liệu trong `tests/`, `docs/ai-update/`, `datasets/` hoặc service-scoped equivalents.
- Không sửa Social DB, baseline checkpoint, train/test split hay nội dung fixture trừ khi task nêu rõ và người dùng duyệt.

## Kiểm thử / bằng chứng

Integration tests và E2E A/B/C/D nếu project có; build web; smoke localhost. Không claim live DB test nếu chỉ isolated mock.

## Acceptance criteria (Definition of Done)

Contract đúng, không mất bình luận lúc AI offline, admin review/appeal hoạt động, auto-hold vẫn gated.

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

Authorized independent integration verification complete for existing runtime/contracts, not a new candidate release. Social177PASS on disposable migrated SQLite. Five-process Playwright E2E1PASS: create/moderation/outage/retry/manual review/appeal/recovery; browser sends0directAI requests, logs5files no private synthetic markers, all owned processes exited. AI predictions in fullstack are explicit fixture scores; separate registry smoke uses real V1 legacy/v2 API and503->200 recovery. Three web buildsPASS isolated outputs. No live DB migration or HIGH auto-hide activation. Evidence reports/ai_update/autonomous_20261103/e2e_v2 and *_tests/build_*.txt.

Root suite355PASS plus24 targeted gate testsPASS (overlapping tests, do not sum); Social177PASS; frontend builds3PASS; real-model development/fallback smokePASS. Threshold/checkpoint/independent test unchanged. Current scope overrides prior single-task/synthetic-only notes; preserve older logs as history.

### Current CPU candidate completion supplement

Actual head-only CPUcandidate trained534steps, encoderfrozen. T030candidate comparison now has validation/final-test/synthetic reports; T031localshadow/fallback/rollbackcomplete and promotionREJECTED. Current candidate legacy/V2/internalSocialcontractAPI200 verified in isolation, no production/default/DB change; no new full-stack-live-candidate deployment is claimed.434rootPASS. Earlier evidence remains historical; current report docs/ai-update/final-report/CPU_HEAD_COMPLETION.md.


## Latest independent-readiness criteria

Historical status/evidence above preserved. Current scoped status: **DONE** — 574root/177Social regressions and isolated5process integration E2E. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/INDEPENDENT_READINESS.md. New criteria never turn missing real/human evidence into DONE. Evidence:574root/177Social/E2E/UI/registry/live smoke PASS; valid real0, no new training.


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
