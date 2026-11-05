# Chạy và kiểm chứng ShieldVI local — T014/T019

## Demo tương tác A–D với AI thật

Từ V3 root chạy `.\services\social-api\.venv\Scripts\python.exe -X utf8 scripts/demo_social.py`. Script tạo DB/tài khoản tạm và chạy đủ 5 process với checkpoint CPU thật. Terminal in URL Social/Admin và mật khẩu cho `demo_alice`, `demo_bob`, `demo_admin`; có lệnh `ai-off`, `ai-on`, `status`, `quit`. [Hướng dẫn bấm từng bước A–D](DEMO_ABCD.md), [smoke AI thật](../baseline/DEMO_ABCD/smoke.json). Không migrate DB demo cũ. Các lệnh test tự động bên dưới vẫn được giữ để regression.

Sau T015, canonical AI ở `services/moderation-ai/app`; root import bridge vẫn chạy lệnh V3 cũ. Research dashboard ở `apps/moderation-web/legacy-v3` (dev 5175), được AI phục vụ cùng URL `/dashboard/`. Model/DB paths mặc định giữ ở V3 root; relative env paths được neo root. [Migration và rollback](../archive/implementation_reports/T015_MIGRATION_REPORT.md).

Chỉ dùng local/private và tài khoản thử. Không deploy, mở public proxy, train hay tự migrate DB demo hiện có. Tất cả lệnh dưới đây tính từ `ShieldVI_V3_Hybrid_Review/`, PowerShell. Python 3.12 và Node đã có; venv Social API và dependencies của hai React app phải được cài theo README từng service/app. Nếu PowerShell chặn `npm.ps1`, dùng `npm.cmd`, không cần đổi execution policy.

## E2E tự tạo môi trường riêng

```powershell
.\services\social-api\.venv\Scripts\python.exe -X utf8 services/social-api/tests/run_fullstack.py
```

Tự tạo SQLite tạm/schema 0004, tài khoản giả, token ngẫu nhiên; chạy **4 server + 1 worker** trên loopback: Social API, AI fixture, Social Web, Moderation Web và worker riêng. Chrome headless kiểm tra đăng ký/login/post/comment → shadow moderation → AI 503/admin offline → manual hide → appeal → restore → AI recovery. Sau test dừng đúng process tree do runner tạo và dọn DB tạm. Không sửa DB demo hay cấp staff thật. AI fixture dùng score tổng hợp, **không phải inference thật**; việc đo checkpoint thật là lệnh riêng phía dưới.

Evidence ở `ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/T014_T019/fullstack/`: browser tests, metrics, server logs, log-privacy, process-health và cleanup. Không bật trace/HAR chứa credential. Failure diagnostics được redact token/mật khẩu tạm.

Demo tương tác với DB/tài khoản giả và duyệt thủ công: [README dashboard](../modules/moderation_web.md), lệnh `apps/moderation-web/tests/run_browser.py --demo`. Demo này có hai UI + Social API; không chạy worker/AI. E2E tự động phía trên kiểm tra đủ năm process.

## Chạy 4 server và worker với checkpoint hiện có

| Terminal | Thư mục | Lệnh |
|---|---|---|
| 1 — AI | V3 root | `.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir services/moderation-ai --host 127.0.0.1 --port 8000 --no-proxy-headers` |
| 2 — Social API | V3 root | `.\services\social-api\.venv\Scripts\python.exe -m uvicorn shieldvi_social.main:create_app --factory --app-dir services/social-api/src --host 127.0.0.1 --port 8001 --no-proxy-headers` |
| 3 — Social Web | `apps/social-web` | `npm.cmd run dev` → 127.0.0.1:5173 |
| 4 — Moderation Web | `apps/moderation-web` | `npm.cmd run dev` → 127.0.0.1:5174 |
| 5 — Worker | V3 root | `.\services\social-api\.venv\Scripts\python.exe -m shieldvi_social.worker` |

Social API/worker dùng **cùng** `SOCIAL_DATABASE_URL`, riêng biệt với AI review/summary DB. Schema phải là 0004, startup không tự migrate. Nếu DB có dữ liệu, dừng API/worker, backup/verify và chỉ nâng khi người vận hành duyệt. Task này chỉ chạy migration trên DB tạm. Mặc định đăng ký tắt; chỉ bật `SOCIAL_REGISTRATION_ENABLED=true`, `VITE_REGISTRATION_ENABLED=true` cho phiên demo riêng. Dashboard cần account moderator/admin do người vận hành cấp; chưa có API tự bootstrap staff thật, không sửa role DB thật bằng fixture script.

AI/worker dùng cùng secret dài ít nhất 32 ký tự: `AI_SERVICE_TOKEN` ở terminal AI, `SOCIAL_AI_SERVICE_TOKEN` ở terminal worker; không đưa vào `VITE_*`, URL, source hoặc log. Có thể nhập secret có sẵn mà không echo:

```powershell
$shieldviSecret = Read-Host 'Service token' -AsSecureString
$env:AI_SERVICE_TOKEN = [System.Net.NetworkCredential]::new('', $shieldviSecret).Password
# Trong terminal worker, nhập cùng secret vào SOCIAL_AI_SERVICE_TOKEN thay cho AI_SERVICE_TOKEN.
```

Worker `SOCIAL_AI_BASE_URL=http://127.0.0.1:8000`; timeout/retry mặc định 3s connect/60s read, 180s lease, tối đa 3 attempts. AI thiếu key/checkpoint/schema lỗi không được publish thay bằng score giả. V3 tự chọn refined V1.1 approved hiện có theo `app/predictor.py`; không gọi nó là V1 baseline. Threshold giữ 0.41. CPU có thể chạy, GPU không bắt buộc cho local smoke; inference latency phụ thuộc máy và số context rows.

Vite proxy `/api` về Social API 8001; browser không gọi AI. Nếu dùng `VITE_SOCIAL_API_BASE` cross-origin, cấu hình `SOCIAL_CORS_ORIGINS` đúng origin cần dùng (5173/5174), không wildcard/credentials. `.env.example` là mẫu; backend đọc environment, không tự load `.env`.

AI vẫn giữ `/api/reviews*`, `/api/recent`, `/health` và dashboard research chưa áp auth Social API; giữ loopback/private, không public proxy nguyên server. Auth service chỉ bảo vệ endpoint `/api/v1/moderate/comment`. Colab cần phiên GPU/checkpoint/mount/lifecycle và reverse proxy có auth/route allowlist riêng; Colab/public proxy chưa chạy trong chặng này. Hai notebook đã cập nhật canonical layout ở T015, chỉ được compile/layout test local.

## Backup và diễn tập khôi phục

Từ V3 root, cấu hình `SOCIAL_DATABASE_URL` đúng DB social trước khi dùng. Chọn tên file mới trong thư mục riêng được phân quyền, không ở static/Git; backup chứa password hashes, session hashes, nội dung và audit. Công cụ chỉ hỗ trợ SQLite, không tự restore/migrate và không overwrite file có sẵn.

```powershell
.\services\social-api\.venv\Scripts\python.exe -m shieldvi_social.backup --output '<absolute-path-to-new-backup.sqlite3>'
.\services\social-api\.venv\Scripts\python.exe -m shieldvi_social.backup --verify '<absolute-path-to-new-backup.sqlite3>'
```

Dùng SQLite backup API thay vì copy một file DB đang ghi; verify integrity, foreign keys và schema. Hỗ trợ schema 0001–0004 để backup trước upgrade. Đã test bản backup trên **đường dẫn khác trong DB tạm**: mở Social API với `SOCIAL_DATABASE_URL` trỏ bản copy, xác nhận session/content/job/audit còn tồn tại. Với dữ liệu thật, dừng tiến trình và kiểm chứng bản phục hồi ở đường dẫn riêng trước khi đổi cấu hình; không tự ghi đè DB gốc. Chưa chốt retention/encryption/offsite rotation/khôi phục thảm họa cho production.

## Fault injection và đánh giá

```powershell
# Tắt AI process thật 600 giây, admin không thao tác trong outage; chỉ DB/tài khoản tạm.
.\services\social-api\.venv\Scripts\python.exe -X utf8 services/social-api/tests/run_outage.py --seconds 600

# Inference CPU thật, local files only, không train/tune/export text.
.\.venv\Scripts\python.exe -X utf8 scripts/evaluate_social_policy.py --output ../ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/T014_T019/ai-evaluation.json --threads 2
```

Sau budget retry, job FAILED_PERMANENTLY giữ pending. Bật AI lại không tự retry vô hạn; staff dùng nút Thử lại AI kèm reason/version hoặc duyệt thủ công. Không reset DB, mass unhide hoặc đổi threshold để giải phóng queue. Runner outage tạo lại môi trường tạm và xác minh đường phục hồi này.

Evaluator giữ nguyên 1.000 dòng ViCTSD test và nhãn Toxicity có sẵn, kiểm tra hash, tách 30 câu synthetic không-gold. Đo classifier, lexical/hybrid **review screening** và active shadow policy; không biến ViCTSD toxicity thành gold HIGH/target/repeated. Chạy lại chỉ để tái lập khi cần, không dùng output test để chọn threshold. [Kết quả và giới hạn](../archive/implementation_reports/T014_T019_VALIDATION_REPORT.md).
