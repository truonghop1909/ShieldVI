> CURRENT verified follow-up: T028/T029 formal BLOCKED; T030–T033 PARTIAL. Safe synthetic/local evidence verified, no real/human-gold acceptance or production activation. Historical DONE below is preserved. See [v5 report](../../docs/ai-update/final-report/REPEATED_RECOVERY_V5.md) and ../CURRENT_AI_SCOPE.json.

# T025 — Repeated Harassment v3: evidence-aware

- **Status:** DONE
- **Priority:** P0
- **Dependencies:** T022,T024
- **Owner:** Codex đề xuất code, người dùng duyệt
- **Scope:** cập nhật AI ShieldVI, không phải tự động bật xử phạt

## Mục tiêu

Phát hiện chuỗi công kích có bằng chứng, không đếm lời xin lỗi/phản đối/can ngăn thành công kích mới.

## Các bước triển khai

1. Kiểm tra logic `toxic_for_repeated_rule` và `repeated_rule_threshold` ở profile conservative/research_synthetic; 0.03 chỉ nghiên cứu.
2. Tạo attack-instance candidate riêng từ raw ViSoBERT + context + lexicon + target confidence, tránh dựa trên score duy nhất; nếu thiếu nhãn thì `needs_review`.
3. Gom theo (actor,target) trên các comment khác thời điểm; bằng chứng phải reference comment IDs thực tế.
4. Nhận diện chuỗi game c08/c11/c15/c18 U02→U03, giữ evidence sau lời xin lỗi c23; c24 không là attack mới.
5. Counterexamples: cùng author nhắc lại từ chửi trong lời xin lỗi; 2 lần trích dẫn; target không chắc; timestamp trùng; user reply nhiều người.
6. Chỉ gợi ý repeated, không tự khẳng định tội danh/hình phạt; không bật auto hold.

## Phạm vi file

- Codex **phải xác minh** service thực tế ở `app/` legacy hoặc `services/moderation-ai/`; chỉ tạo/sửa file hợp lý trong đó.
- Test và tài liệu trong `tests/`, `docs/ai-update/`, `datasets/` hoặc service-scoped equivalents.
- Không sửa Social DB, baseline checkpoint, train/test split hay nội dung fixture trừ khi task nêu rõ và người dùng duyệt.

## Kiểm thử / bằng chứng

Integration tests evidence IDs and pair correctness; no repeated for quote-only/apology-only; no regression for conservative policy.

## Acceptance criteria (Definition of Done)

Evidence list đúng actor→target, distinct timestamps và không có apology/comment vô tội; missing evidence => no automatic repeated accusation.

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

### Autonomous session 02/11/2026

- Status: DONE
- Versioned v2 engine qualifies evidence using context + grounded recipient + profile model threshold; 0.03 stays research-only. Legacy v1 behavior kept for compatibility. Recovery-only turns excluded; previous genuine attacks remain.
- Files: services/moderation-ai/app/signal_engine.py, services/moderation-ai/app/context_signals.py, services/moderation-ai/app/target_signals.py, tests/test_signal_engine.py
- Tests: signal/target/context/internal legacy regression: 60 passed, 1 warning

### User-authorized GAME_RANK_30 follow-up

Confirmed DONE status preserved. Context-v2/ACKNOWLEDGEMENT + clause scope, additive reply/attacktarget/assessment/policy fields, exact4attack GAMEevidence and localDashboardV2 updated. Root417PASS,Social177PASS,2browser checks/build/realV1smokePASS; residual GenZ repeated0/7 disclosed. Details: docs/ai-update/CONTEXT_RECOVERY_GAME_RANK_30.md and AUTO_PROGRESS. No labels/checkpoint/0.41/test changes or production deploy.


## CURRENT camping context follow-up — COMPLETE

Pastedcamping30reproduced at actual V1.1:8020/r05:8021; frozen existing AI references, not human gold. General clause patterns + abuse-endorsement disambiguation + APOLOGY_ACCEPTANCE distinguish accepting apology from self-blame. Contextv3/repeatedv4 qualifies grounded context attacks independently of raw0.41, additive attack_instance_basis. Existing target-v3/legacyengine/lexicon unchanged. Actual after:30/30reference labels bothmodels; exact U04→U03evidence[c09,c12,c15,c18], no apology/recovery added; c18notDEFENSE,c25acceptsapology. All rawscores/legacyfields unchanged.

Full540PASS/1warning, UIbuildPASS, servednewUI/actuallegacy+V2API200. Paired890originalV1cachedscores:1improvement/0newlabelerrors/1eventchange/no newCLEAN-reference evidence. Existing developmenterrors remain documented; no freshblind claim.31protected hashes+all datasets/test/SQLite/V1/V1.1/candidates unchanged. No train/promotion/deploy/auto-hide. Prior DONE and r03/r04/r05promotion rejections preserved.

Current report docs/ai-update/final-report/CAMPING_CONTEXT_RECOVERY.md. Evidence reports/ai_update/camping_context_20261103/; currentownedPIDs in demo_after_server_state.json, older demo PID files superseded. RefreshCtrl+F5 at8020or8021 and reanalyze. No other task started.


## Latest independent-readiness criteria

Historical status/evidence above preserved. Current scoped status: **DONE** — Repeated-evidence regression; missing targets still abstain, no promised perfect recall. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/INDEPENDENT_READINESS.md. New criteria never turn missing real/human evidence into DONE. Evidence:574root/177Social/E2E/UI/registry/live smoke PASS; valid real0, no new training.


## Current verified follow-up — repeated/context/target v5

T028 BLOCKED(real0/200,humanlabels0); T029 formalBLOCKED(r06 experimental already trained, no r07); T030/T031/T032/T033 PARTIAL (safe synthetic/local work verified; missing independent acceptance, no production authorization). Historical DONE preserved; current scope tasks/CURRENT_AI_SCOPE.json.

Five event regression red5FAIL before fix; old challenge repeated0/5→5/5, evidence10/10correct. Fresh post-freeze12threads/74comments:2/6→4/6, precision1/recall.6667, evidence8/8correct;2misses retained, no post-score rule changes. Canonical500/5115 unchanged. Broad890replay known886 FP18→18/FN6→4; repeated2/10→8/10,FP0,evidence20/20; no new label errors. Old prose34target/3events superseded by archived/recomputed33/54and2/10; DANCE lacks grounding refs and cannot count as TP.

Tests610rootPASS/177SocialPASS/browserfiveprocessE2EPASS; actual r06 shadow/fallbackV1/ASGI200→503→200PASS. Browser uses fixtureAI/disposableSQLite, actual models tested separately. Model/default/V1/0.41/test/SQLite/reference labels unchanged; no training/deploy. Runtime context_signals.py/target_signals.py/signal_engine.py+contract defaults; two new test files, reusable evaluate_repeated_recovery.py,12new fixture JSONs/manifest, isolated registry, real-cohort development exclusions, report/progress/task notes. Full file inventory/hashes in reports/ai_update/repeated_recovery_20261103/ARTIFACTS.json.

Report docs/ai-update/final-report/REPEATED_RECOVERY_V5.md; evidence/reproduction reports/ai_update/repeated_recovery_20261103/README.md. Next: real permitted source/human rounds for acceptance; new predeclared holdout before further rule tuning. Do not train r07, recreate500, change default or call synthetic human gold.
