# T020 — Kiểm kê AI và baseline hiện tại

Ngày 02/11/2026 (Asia/Saigon). Phạm vi: audit/snapshot, không triển khai T021 hoặc cải tiến AI. **T020 DONE sau kiểm chứng**, không có thay đổi implementation, checkpoint, threshold hoặc dataset test.

## Backend và trạng thái thực tế

- Canonical backend: `services/moderation-ai/app/`. Runtime import `app.main`, `app.engine`, `app.predictor` đều resolve về service này; root `app/__init__.py` chỉ chuyển tiếp import. Research Dashboard phục vụ từ `services/moderation-ai/app/static/` tại `/dashboard/`.
- GET localhost:8000/health và openapi.json tại thời điểm audit đều bị từ chối kết nối. Không khẳng định có Uvicorn đang phục vụ; các API smoke bên dưới chạy bằng TestClient trong tiến trình riêng, không mở cổng hoặc đổi server người dùng.
- Kiểm kê process bằng CIM bị từ chối truy cập sandbox; bằng chứng là kết quả localhost và đường dẫn import thật. Git status/branch/HEAD đều báo không phải Git repository; branch/commit không có, không giả SHA commit. Snapshot source SHA-256 thay thế định danh trạng thái hiện có.

## Checkpoint và threshold

- V1 gốc tồn tại tại `C:/Users/admin/Downloads/visobert_toxic_final`, XLM-R/ViSoBERT hai lớp CLEAN/TOXIC; threshold_config.json xác nhận **0.41**. Load và inference offline CPU thành công.
- Không có MODEL_PATH override trong tiến trình audit. Default selector đang chọn `models/visobert_head_refined` (V1.1 approved), threshold **0.41**. Đã giữ nguyên default, không ép V1 làm production default.
- Đã lưu hai baseline riêng: **V1_immutable** và **V1_1_configured_default**, mỗi baseline có sample API, 5 JSON kết quả fixture, health, summary và response adapter. V2 synthetic experiment hiện có chỉ được ghi config/hash bảo vệ, không load/activate/train trong task này.
- Việc ghi nhận cả hai baseline là mô tả hiện trạng, không quyết định B0 cho các thực nghiệm tiếp theo. Lựa chọn baseline thực nghiệm và scope T026/T032 vẫn chưa được task này phê duyệt.

## Môi trường có thể tái lập

- Python: 3.12.10 (tags/v3.12.10:0cc8128, Apr  8 2025, 12:21:36) [MSC v.1943 64 bit (AMD64)].
- transformers==4.57.3, tokenizers==0.22.2, huggingface-hub==0.36.2, fastapi==0.162.0, torch==2.15.0, pydantic==2.14.1, pytest==9.2.0, httpx==0.28.1, uvicorn==0.54.0, safetensors==0.8.0, starlette==1.10.0.
- Torch runtime CPU: 2.15.0+cpu, CUDA available=False, threads=6.
- Snapshot toàn bộ phiên bản cài đặt ở installed_versions.snapshot.txt; requirements đang có được hash nhưng không sửa/không cài package. Đã bật HF_HUB_OFFLINE/TRANSFORMERS_OFFLINE và tắt pycache cho tiến trình kiểm tra.

## API và luồng Social

- Legacy: GET /health, POST /api/analyze, POST /api/reviews/batch, GET /api/reviews, /api/reviews/stats, /api/reviews/export, /api/recent và GET /. OpenAPI/docs/redoc và static Dashboard giữ nguyên.
- Nội bộ: POST /api/v1/moderate/comment, contract schema 1.0, Bearer service auth; thiếu auth trả 401, auth test cô lập trả 200. Token ngẫu nhiên chỉ tồn tại trong tiến trình, không ghi vào evidence.
- Luồng xác minh qua source: Social worker → ai_client → endpoint nội bộ → advisory response; Social API sở hữu visibility/audit. Hai bản moderation_contract.py byte-identical. Không gọi worker/DB Social đang chạy, không claim E2E live.
- Lưu OpenAPI, route inventory và JSON schema input/output cho cả legacy Analyze và internal Moderation. Snapshot draft ai_signals v2 chưa được triển khai; không đổi contract.

## Kiểm thử thực tế

- Cwd backend: `services/moderation-ai`; chạy bằng venv gốc: `python -X utf8 -m pytest -q <root>/tests -p no:cacheprovider --basetemp <evidence>/test_tmp_before` và tương tự test_tmp_after.
- **Trước: 170 passed, 1 warning in 3.64s**, exit 0.
- **Sau: 170 passed, 1 warning in 3.68s**, exit 0.
- Warning hiện có: Starlette/httpx deprecation; không cài/nâng dependency để xử lý trong T020.
- Missing model: health HTTP 200/model_loaded=false, /api/analyze HTTP 503, không tạo score giả.
- Mock-only: /api/analyze HTTP 200, model_name T020 MOCK ONLY; chỉ chứng minh contract, không phải inference thật.
- Real inference V1 và V1.1: sample DEMO_A HTTP 200; mỗi model xử lý 5 fixture Gen Z × 30 comment, tất cả HTTP 200/threshold 0.41. Internal adapter 200 khi có auth, 401 khi thiếu auth.
- **71 file được bảo vệ có SHA-256 trước/sau hoàn toàn giống nhau**, gồm checkpoint/config/tokenizer, source AI/tests/contracts, ViCTSD holdout, fixture và SQLite hiện có. Không đổi dataset test. STORE_SUMMARIES=0; review endpoints có side effect không được gọi. Test DB chỉ ở basetemp riêng.
- Frontend build CHƯA CHẠY vì không sửa frontend; live Uvicorn/Social E2E CHƯA CHẠY. Thời gian audit chính: 33.81 giây.

## Snapshot hành vi trên fixture tổng hợp

Các số dưới là số câu model gắn toxic, không phải số lỗi hay metric accuracy/F1. Fixture là synthetic developer regression, chưa có gold độc lập. Không chỉnh score, nhãn hoặc fixture.

| Fixture | V1: flagged | V1.1: flagged | V1 repeated | V1.1 repeated |
|---|---:|---:|---|---|
| SHIELDVI_01_GAME_RANK_LAG_30 | 9 | 9 | True | True |
| SHIELDVI_02_SHOP_GIAY_SECONDHAND_30 | 5 | 5 | True | True |
| SHIELDVI_03_DANCE_COVER_TIKTOK_30 | 8 | 7 | True | True |
| SHIELDVI_04_DI_CAMPING_CHIA_TIEN_30 | 6 | 6 | True | True |
| SHIELDVI_05_FANART_AI_DISPUTE_30 | 6 | 6 | True | True |

## Bằng chứng và điểm dừng

- [Thư mục evidence](../../reports/ai_update/baseline/2026-11-02_T020/) — result, inventory, logs test, protected hashes, schema/routes, phiên bản, source Social adapter và raw JSON thật.
- [Result](../../reports/ai_update/baseline/2026-11-02_T020/result.json), [V1 summary](../../reports/ai_update/baseline/2026-11-02_T020/V1_immutable/summary.json), [V1.1 summary](../../reports/ai_update/baseline/2026-11-02_T020/V1_1_configured_default/summary.json).
- Script capture_baseline.py là công cụ ghi baseline, không phải code cải tiến. Lượt đầu dừng vì FastAPI lazy IncludedRouter không có .path; đã sửa riêng công cụ audit để đọc routes từ OpenAPI. Chi tiết ở capture_attempts.json. Lượt chạy hoàn chỉnh PASS; không sửa backend để vượt lỗi.
- Đã đọc AGENTS.md, TASK_ORDER_AI, skill shieldvi-ai-upgrade; AGENTS_AI_ADDENDUM.md được đọc từ gói nguồn dự phòng vì bản active đã hợp nhất quy tắc vào AGENTS/skill, không tạo bản hướng dẫn trùng.
- Cập nhật chỉ T020 thành DONE trong task, TASK_ORDER_AI và bảng tổng hợp TASK_ORDER. T021–T033 giữ TODO; các task Social giữ nguyên.
- Task tiếp theo đề xuất **T021**, chỉ thực hiện khi được giao riêng. Dừng sau T020; không train hoặc triển khai task tiếp theo.
