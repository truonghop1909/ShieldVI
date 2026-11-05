> Source directory: `services/moderation-ai/`. Run relative commands from the working directory named in each section; when omitted, use this source directory. [Documentation index](../README.md).

# ShieldVI Moderation AI — T015

Canonical AI backend: `services/moderation-ai/app`. ViSoBERT, lexicon, target/repeated, internal adapter và research review/summary API ở đây. Không import Social API hoặc ghi Social DB. Root `app/__init__.py` chỉ là import bridge cho lệnh/script V3; không có bản implementation thứ hai.

## Chạy local

Từ V3 root, dùng AI venv hiện có:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir services/moderation-ai --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Hoặc từ `services/moderation-ai`:

```powershell
..\..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Khi cần môi trường AI riêng ở service, tạo `.venv` rồi `python -m pip install -r requirements.txt`; không dùng Social API venv để cài Torch. Trong task dùng lại AI venv hiện có, không train/install lại model. Root `requirements.txt` chuyển tiếp tới requirements service. Backend đọc environment, không tự load `.env`.

## Paths và dữ liệu giữ nguyên

- `MODEL_PATH` nếu có vẫn ưu tiên; absolute path giữ nguyên, relative path neo repository root để không đổi checkpoint theo cwd. Không có biến thì giữ approved auto-selection `models/visobert_head_refined` (runtime hiện tại V1.1), fallback Drive như trước. Weights/config không di chuyển hoặc ghi đè, threshold **0.41**.
- `REVIEW_DB_PATH` và `DB_PATH` có absolute path thì giữ nguyên, relative path neo repository root. Default vẫn là file cũ ở V3 root: `shieldvi_reviews.sqlite3`, `moderation_summaries.sqlite3`. Startup không tự relocate/migrate DB, không copy social account/history sang AI.
- Lexicon nằm ở `app/data/lexicon` của service. Rules/pinned sources giữ byte, không bật pending rules.
- Static research build nằm ở `app/static` của service. URL cũ **`/dashboard/`** giữ nguyên, không phải dashboard duyệt Social.

## Auth và contract

Worker gửi `POST /api/v1/moderate/comment`, schema 1.0, shared `AI_SERVICE_TOKEN` ít nhất 32 ký tự, cùng giá trị `SOCIAL_AI_SERVICE_TOKEN` ở worker. Không gửi secret vào browser hoặc `VITE_*`. Internal responses chỉ advisory; Social API áp visibility/audit. HIGH auto-hold vẫn tắt.

Legacy `/api/analyze`, `/health`, `/api/reviews*`, `/api/recent`, `/dashboard/` giữ contract cũ; research endpoints chưa có Social auth. Giữ loopback/private, không public proxy toàn service. Research labels không phải quyết định visibility/appeal của Social DB.

## Dashboard và kiểm chứng

Research React source: [apps/moderation-web/legacy-v3](legacy_research_dashboard.md), dev 5175. Social moderation UI vẫn ở `apps/moderation-web`, 5174. Root `npm --prefix frontend run build` tiếp tục được hỗ trợ qua wrapper.

Hai notebook đã đổi canonical paths/server cwd, giữ Drive checkpoint/review paths và không xóa thư mục giải nén cũ. Chưa chạy Colab/GPU; compile/layout tests không được coi là Colab run.

[T015 report/rollback](../archive/implementation_reports/T015_MIGRATION_REPORT.md), [runbook fullstack](../guides/RUN_LOCAL.md).
