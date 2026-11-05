# T020 — Audit AI & snapshot baseline

- **Status:** DONE
- **Priority:** P0
- **Dependencies:** none
- **Owner:** Codex đề xuất code, người dùng duyệt
- **Scope:** cập nhật AI ShieldVI, không phải tự động bật xử phạt

## Mục tiêu

Chốt hiện trạng trước khi sửa. Tìm vị trí backend đang chạy, checkpoint, schema, test, baseline predictions, pin dependency và luồng Social adapter. Giữ bằng chứng có thể tái lập.

## Các bước triển khai

1. `git status --short`, ghi branch/commit (không tự commit).
2. Dùng tìm kiếm hẹp định vị `app/engine.py`, `app/lexical.py`, `app/predictor.py`, `app/schemas.py`, `app/main.py` hoặc service đã migrate; xác nhận đúng import tại runtime.
3. Ghi phiên bản Python, Transformers, tokenizers, hub, FastAPI, PyTorch và dependency của test.
4. Chạy test backend hiện có, health/API smoke với mock phân biệt rõ; inference model thật chỉ nếu đã có quyền truy cập checkpoint.
5. Export raw JSON results cho 5 fixture vào `reports/ai_update/baseline/` nếu model có sẵn, kèm timestamp/sha256 config; không chỉnh score để khớp bản screenshot.
6. Ghi snapshot contract đầu ra và schema (không dump dữ liệu người dùng thật).

## Phạm vi file

- Codex **phải xác minh** service thực tế ở `app/` legacy hoặc `services/moderation-ai/`; chỉ tạo/sửa file hợp lý trong đó.
- Test và tài liệu trong `tests/`, `docs/ai-update/`, `datasets/` hoặc service-scoped equivalents.
- Không sửa Social DB, baseline checkpoint, train/test split hay nội dung fixture trừ khi task nêu rõ và người dùng duyệt.

## Kiểm thử / bằng chứng

Snapshot trước/sau `python -m pytest -q` tại đúng backend; JSON sample `/api/analyze`; thiếu checkpoint phải ghi `REAL_INFERENCE_NOT_RUN` và lý do.

## Acceptance criteria (Definition of Done)

Baseline V1/0.41 bất biến; báo cáo test thật, source paths đã xác minh, model availability, version manifest, không viết code cải tiến.

## Chặn rủi ro / stop conditions

- Nếu thiếu dữ liệu, license, nhãn người kiểm duyệt, checkpoint, GPU hoặc quyền phù hợp: ghi `BLOCKED` + lý do, không giả lập thành PASS.
- Nếu xuất hiện breaking change hoặc metric xấu đi rõ ràng: báo tác động, rollback và xin duyệt.
- Task chỉ `DONE` sau khi có evidence đúng; công việc chưa chạy cần ghi `CHƯA CHẠY`.

## Nhật ký thực hiện (Codex cập nhật)

- Ngày: 02/11/2026 (Asia/Saigon); Git branch/commit không có vì workspace không phải Git repository. Định danh trạng thái bằng source/protected SHA-256.
- Báo cáo: [T020_BASELINE_REPORT.md](../../docs/ai-update/T020_BASELINE_REPORT.md); [evidence](../../reports/ai_update/baseline/2026-11-02_T020/result.json).
- Canonical import xác nhận `services/moderation-ai/app/`; root app là bridge. Cổng 8000 không phản hồi khi audit; không claim server live.
- V1 gốc có sẵn, threshold 0.41, inference offline thật PASS. Default V1.1 được giữ nguyên, baseline V1 và V1.1 lưu riêng.
- Test backend trước/sau: **170 passed, 1 warning**, exit 0 cả hai lần. Cwd services/moderation-ai; lệnh/summary/log đầy đủ trong evidence.
- API: thiếu checkpoint 503, mock-only 200, sample thật và 5 fixture/150 comment mỗi model HTTP 200; internal adapter auth 200/unauth 401. OpenAPI/schema/routes được lưu.
- 71 protected hashes trước/sau không đổi; không train, đổi checkpoint/threshold/default, sửa test split, ghi DB thật hay cải tiến code.
- File cập nhật: task này, TASK_ORDER_AI.md, tasks/TASK_ORDER.md; thêm docs/ai-update/T020_BASELINE_REPORT.md và reports/ai_update/baseline/2026-11-02_T020/.
- Giới hạn: mock không chứng minh inference; fixture synthetic không phải gold/blind metric; không có live Social E2E, Git commit hoặc frontend build trong phạm vi này. Baseline B0 thực nghiệm chưa tự quyết định.
- Task đề xuất tiếp theo: **T021**, chưa bắt đầu; dừng sau T020.
