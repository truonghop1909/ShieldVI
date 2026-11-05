# T026 — API schema / dashboard signals / policy boundary

- **Status:** DONE
- **Priority:** P1
- **Dependencies:** T022,T023,T024,T025
- **Owner:** Codex đề xuất code, người dùng duyệt
- **Scope:** cập nhật AI ShieldVI, không phải tự động bật xử phạt

## Mục tiêu

Mở rộng API V3/Social adapter để hiển thị raw score + context/lexicon/target/repeated riêng biệt, không phá frontend.

## Các bước triển khai

1. Đối chiếu `docs/ai-update/04_API_VERSIONING.md` và contract hiện hành.
2. Thêm schema additive và version; API `/api/analyze` legacy vẫn hoạt động.
3. Phần AI trả `analysis_signals`, evidence, version, không ghi Social DB hay đổi visibility.
4. UI phân biệt: “AI predicted toxic”, “ngữ cảnh xin lỗi”, “từ khóa” và “cảnh báo công kích lặp lại”; hiển thị lý do target có thể sai.
5. `risk_level` của engine không tự dùng làm `policy_risk=HIGH`, không bật auto-hold.
6. Tạo tests Pydantic/FastAPI contract cũ/mới và frontend build nếu sửa JSX/CSS.

## Phạm vi file

- Codex **phải xác minh** service thực tế ở `app/` legacy hoặc `services/moderation-ai/`; chỉ tạo/sửa file hợp lý trong đó.
- Test và tài liệu trong `tests/`, `docs/ai-update/`, `datasets/` hoặc service-scoped equivalents.
- Không sửa Social DB, baseline checkpoint, train/test split hay nội dung fixture trừ khi task nêu rõ và người dùng duyệt.

## Kiểm thử / bằng chứng

`python -m pytest -q` backend; `npm run build` frontend khi sửa UI; POST /api/analyze DEMO_A và 5 fixtures. Không có model thật => đánh dấu mock-only.

## Acceptance criteria (Definition of Done)

Old consumers hoạt động, new fields có version, model_score nguyên, SQLite review không bị mất, policy vẫn tách.

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
- Typed /api/v2/analyze and research UI show raw model/context/attack target/human authority separately. Legacy /api/analyze and Social internal 1.0 unchanged; Social v3 promotion remains T032-gated. UI build isolated, not deployed.
- Files: services/moderation-ai/app/main.py, services/moderation-ai/app/schemas.py, services/moderation-ai/app/signal_engine.py, apps/moderation-web/legacy-v3/src/App.jsx, tests/test_api_v2.py, contracts/analysis_response_v2.schema.json, docs/ai-update/V2_COMPATIBILITY.md, reports/ai_update/T026/real_smoke.json
- Tests: Full backend: 243 passed, 1 warning; npm build isolated output: PASS, 1578 modules; Real CPU model: 5 fixtures API v1/v2 HTTP200, scores and labels identical

### User-authorized GAME_RANK_30 follow-up

Confirmed DONE status preserved. Context-v2/ACKNOWLEDGEMENT + clause scope, additive reply/attacktarget/assessment/policy fields, exact4attack GAMEevidence and localDashboardV2 updated. Root417PASS,Social177PASS,2browser checks/build/realV1smokePASS; residual GenZ repeated0/7 disclosed. Details: docs/ai-update/CONTEXT_RECOVERY_GAME_RANK_30.md and AUTO_PROGRESS. No labels/checkpoint/0.41/test changes or production deploy.


## CURRENT camping context follow-up — COMPLETE

Pastedcamping30reproduced at actual V1.1:8020/r05:8021; frozen existing AI references, not human gold. General clause patterns + abuse-endorsement disambiguation + APOLOGY_ACCEPTANCE distinguish accepting apology from self-blame. Contextv3/repeatedv4 qualifies grounded context attacks independently of raw0.41, additive attack_instance_basis. Existing target-v3/legacyengine/lexicon unchanged. Actual after:30/30reference labels bothmodels; exact U04→U03evidence[c09,c12,c15,c18], no apology/recovery added; c18notDEFENSE,c25acceptsapology. All rawscores/legacyfields unchanged.

Full540PASS/1warning, UIbuildPASS, servednewUI/actuallegacy+V2API200. Paired890originalV1cachedscores:1improvement/0newlabelerrors/1eventchange/no newCLEAN-reference evidence. Existing developmenterrors remain documented; no freshblind claim.31protected hashes+all datasets/test/SQLite/V1/V1.1/candidates unchanged. No train/promotion/deploy/auto-hide. Prior DONE and r03/r04/r05promotion rejections preserved.

Current report docs/ai-update/final-report/CAMPING_CONTEXT_RECOVERY.md. Evidence reports/ai_update/camping_context_20261103/; currentownedPIDs in demo_after_server_state.json, older demo PID files superseded. RefreshCtrl+F5 at8020or8021 and reanalyze. No other task started.
