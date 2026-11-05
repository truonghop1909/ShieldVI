# T022 — Context Signals: apology, quote, defense, intervention

- **Status:** DONE
- **Priority:** P0
- **Dependencies:** T021
- **Owner:** Codex đề xuất code, người dùng duyệt
- **Scope:** cập nhật AI ShieldVI, không phải tự động bật xử phạt

## Mục tiêu

Tạo lớp tín hiệu ngữ cảnh có thể gắn nhiều tag, không phá raw ViSoBERT. Sửa câu xin lỗi/nhắc lại từ tục bị dùng làm evidence sai.

## Các bước triển khai

1. Tạo module `context_signals.py` tại đúng backend; schema typed cho tags/cues/confidence/negation. Không nối parent vào input model V1.
2. Phát hiện câu: APOLOGY, QUOTE/META, DEFENSE/SET_BOUNDARY, INTERVENTION, DIRECT_ATTACK, UNCERTAIN. Những tags có thể đồng thời.
3. Tách `attack_candidate` khỏi `toxic_for_moderation`; nếu detect xin lỗi + insult mới thì vẫn là attack candidate cần review.
4. Không dùng keyword override; kết hợp động từ xin lỗi, đối tượng, cấu trúc trích dẫn, ngữ nghĩa văn bản + vị trí từ tố cáo (và confidence).
5. Test game c12,c16,c23,c24; camping c17,c23,c24; dance c23; shop c23; fanart c24 + 10 counterexamples. Giữ raw score không đổi.
6. Tối ưu latency, log lý do ngắn không ghi nội dung PII.

## Phạm vi file

- Codex **phải xác minh** service thực tế ở `app/` legacy hoặc `services/moderation-ai/`; chỉ tạo/sửa file hợp lý trong đó.
- Test và tài liệu trong `tests/`, `docs/ai-update/`, `datasets/` hoặc service-scoped equivalents.
- Không sửa Social DB, baseline checkpoint, train/test split hay nội dung fixture trừ khi task nêu rõ và người dùng duyệt.

## Kiểm thử / bằng chứng

Unit tests context + contract tests raw score unchanged, minimal regression suite.

## Acceptance criteria (Definition of Done)

Có tags và tín hiệu attack_candidate giải thích được; không có blanket CLEAN cho “xin lỗi”; target/repeated chưa được thay riêng trong task này.

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
- Standalone typed multi-tag context signals, mixed apology+attack preserved; original fixture recovery cases and raw model invariance verified. Target/repeated integration remains T024/T025.
- Files: services/moderation-ai/app/context_signals.py, tests/test_context_signals.py
- Tests: Context/regression subset 32 tests passed inside 128-test combined run

### User-authorized GAME_RANK_30 follow-up

Confirmed DONE status preserved. Context-v2/ACKNOWLEDGEMENT + clause scope, additive reply/attacktarget/assessment/policy fields, exact4attack GAMEevidence and localDashboardV2 updated. Root417PASS,Social177PASS,2browser checks/build/realV1smokePASS; residual GenZ repeated0/7 disclosed. Details: docs/ai-update/CONTEXT_RECOVERY_GAME_RANK_30.md and AUTO_PROGRESS. No labels/checkpoint/0.41/test changes or production deploy.


## CURRENT camping context follow-up — COMPLETE

Pastedcamping30reproduced at actual V1.1:8020/r05:8021; frozen existing AI references, not human gold. General clause patterns + abuse-endorsement disambiguation + APOLOGY_ACCEPTANCE distinguish accepting apology from self-blame. Contextv3/repeatedv4 qualifies grounded context attacks independently of raw0.41, additive attack_instance_basis. Existing target-v3/legacyengine/lexicon unchanged. Actual after:30/30reference labels bothmodels; exact U04→U03evidence[c09,c12,c15,c18], no apology/recovery added; c18notDEFENSE,c25acceptsapology. All rawscores/legacyfields unchanged.

Full540PASS/1warning, UIbuildPASS, servednewUI/actuallegacy+V2API200. Paired890originalV1cachedscores:1improvement/0newlabelerrors/1eventchange/no newCLEAN-reference evidence. Existing developmenterrors remain documented; no freshblind claim.31protected hashes+all datasets/test/SQLite/V1/V1.1/candidates unchanged. No train/promotion/deploy/auto-hide. Prior DONE and r03/r04/r05promotion rejections preserved.

Current report docs/ai-update/final-report/CAMPING_CONTEXT_RECOVERY.md. Evidence reports/ai_update/camping_context_20261103/; currentownedPIDs in demo_after_server_state.json, older demo PID files superseded. RefreshCtrl+F5 at8020or8021 and reanalyze. No other task started.


## Latest independent-readiness criteria

Historical status/evidence above preserved. Current scoped status: **DONE** — Indirect attack/context development on frozen synthetic references. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/INDEPENDENT_READINESS.md. New criteria never turn missing real/human evidence into DONE. Evidence:574root/177Social/E2E/UI/registry/live smoke PASS; valid real0, no new training.
