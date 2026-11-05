> Source directory: `services/social-api/`. Run relative commands from the working directory named in each section; when omitted, use this source directory. [Documentation index](../README.md).

# ShieldVI Social API

T014/T019 thêm E2E đủ 4 server + worker, fault injection, privacy/security regression và công cụ backup SQLite không overwrite. [Runbook local/backup](../guides/RUN_LOCAL.md), [báo cáo và metrics AI thật](../archive/implementation_reports/T014_T019_VALIDATION_REPORT.md). Login/logout và dashboard metrics được sửa để tránh vòng khóa SQLite khi worker đang ghi. Không migrate DB demo trong task.

FastAPI độc lập với AI V3: auth (T008), content/feed/outbox (T009), worker (T012/T017), queue/report/appeal/audit (T013/T018). Runtime Social API không import `app` legacy, Torch, Transformers hoặc đọc AI DB. Dashboard ở `apps/moderation-web`, Social Web ở `apps/social-web`.

## Mốc T013/T018 hiện hành

API và worker yêu cầu **`0004_review`**. Chỉ DB tạm đã được nâng/test; DB demo hiện có chưa migrate trong task. Dừng API/worker, backup Social DB và chỉ nâng sau khi người vận hành duyệt. Downgrade từ chối nếu có appeal/report/structured audit để giữ lịch sử; dùng code tương thích schema hoặc backup đã kiểm chứng.

Dashboard và demo dùng DB tạm/tài khoản giả: [moderation-web README](moderation_web.md). [Contract T013/T018](../architecture/API_CONTRACT.md). Không cần AI/GPU để duyệt thủ công. HIGH auto-hold vẫn tắt.

## Chạy local

Từ thư mục `services/social-api`, Python 3.12+:

```powershell
python -m venv .venv
& ./.venv/Scripts/python.exe -m pip install -e '.[test]'
& ./.venv/Scripts/python.exe -m alembic upgrade head
& ./.venv/Scripts/python.exe -m uvicorn shieldvi_social.main:create_app --factory --app-dir src --host 127.0.0.1 --port 8001 --no-proxy-headers
```

Mặc định tạo DB riêng tại đường dẫn tuyệt đối `services/social-api/data/social.sqlite3` khi chạy migration. Startup kiểm tra schema, không tự `create_all`/migrate. Không chạy migration trên AI DB. Cấu hình qua environment; `.env.example` chỉ hướng dẫn, không tự load `.env`. Đăng ký mặc định **tắt**, CORS mặc định không cho origin browser nào. Muốn thử registration bằng dữ liệu giả trong phiên local, chủ động đặt `SOCIAL_REGISTRATION_ENABLED=true` trước khi chạy server; không bật public registration/Internet trong MVP.

`requirements-dev.lock` là snapshot dependency đã test trên Python 3.12/Windows; để tái lập dùng `pip install -r requirements-dev.lock` rồi `pip install -e . --no-deps`. Không có dependency AI trong service.

Các biến: `SOCIAL_DATABASE_URL` (SQLite absolute URL hoặc `postgresql+psycopg`), `SOCIAL_SESSION_TTL_SECONDS` (60–86400, mặc định 3600), `SOCIAL_CORS_ORIGINS` (JSON array exact HTTP(S) origins), `SOCIAL_AUTH_RATE_LIMIT` (mặc định 10), `SOCIAL_AUTH_RATE_WINDOW_SECONDS` (mặc định 60). Không dùng CORS `*`, cookie credential hay secret hardcode. Không tin X-Forwarded-For; dev server tắt proxy headers, production phải chốt trusted proxy riêng.

## Auth contract

| Route | Input/quyền | Thành công / lỗi |
|---|---|---|
| `GET /health` | Không auth | 200 ready; DB lỗi 503, không lộ connection string |
| `POST /api/v1/auth/register` | JSON username/email/password; registration bật | 201 user; 403 disabled, 409 identity trùng, 422 invalid, 429 rate limit |
| `POST /api/v1/auth/login` | JSON username/password | 200 access_token/token_type/expires_in; 401 generic cho sai/missing/suspended, 422, 429 |
| `GET /api/v1/me` | Authorization: Bearer token | 200 chính mình; 401 token thiếu/sai/hết hạn/thu hồi hoặc account suspended |
| `POST /api/v1/auth/logout` | Bearer hiện tại | 204 thu hồi phiên hiện tại; phiên khác vẫn còn, 401 nếu không hợp lệ |
| `GET /api/v1/admin/access` | Bearer, role admin lấy từ DB | 200 probe quyền chỉ đọc; 401 chưa auth, 403 user/moderator |

User response chỉ id/username/role/status/created_at UTC, không email/password hash/token. Username ASCII lowercase 3–30 (`a-z0-9_`), email lowercase validated tối đa 254, password 12–128 ký tự, không trim/lowercase password. Không yêu cầu client gửi role/status; field dư bị từ chối. Auth request tối đa 16KiB kể cả chunked; content request tối đa 128KiB để hỗ trợ 8000 ký tự Unicode/JSON escaped; validation không echo input/password. Duplicate identity trả lỗi generic nhưng vẫn có thể lộ sự tồn tại tài khoản qua 409; chỉ dành demo private.

Mật khẩu Argon2id random salt, verify và rehash khi tham số thay đổi. Bearer token opaque 256-bit ngẫu nhiên, DB chỉ lưu SHA-256 token, hạn dùng server-side và logout thu hồi; không cần JWT signing secret. Không tự refresh; hết hạn đăng nhập lại. Role/status đọc lại DB mỗi request nên hạ role/suspend có hiệu lực ngay. Không có endpoint cấp role/admin hoặc bootstrap tài khoản thật trong T008; admin fixture chỉ tồn tại trong DB test tạm. Quy trình cấp quyền có audit cho người vận hành là hạng mục sau, không sửa DB thật thủ công trong task này.

T010 nên giữ token trong memory của UI, không localStorage, gửi header Authorization; T008 không dùng cookie nên browser không tự gửi credentials và không có cookie CSRF flow. Response no-store; HTTPS bắt buộc khi rời local. Không log body/token/Authorization; reverse proxy tương lai cũng phải redact headers.

Rate limit login/register theo peer IP **và** username normalized, DB upsert nguyên tử và dùng chung giữa processes/restarts; key hash, cleanup buckets quá cũ. Fixed window có burst tại biên; không phải chống DDoS/lockout hoàn chỉnh. Request sai schema bị reject trước limiter; cần edge limit nếu vận hành public. Không có refresh/password-reset/email-verification/session management UI trong T008.

## DB và migration

`0001_users`: auth. `0002_content`: posts/comments/outbox/audit. `0003_worker`: claim/lease, attempts/retry, request snapshot/hash, moderation_results và system audit actor. `0004_review`: reports, appeals, reviewer leases và audit details. Startup yêu cầu `0004_review`; dừng server/worker rồi chủ động chạy `alembic upgrade head` trên DB social đã backup và có duyệt. **Codex chỉ kiểm thử migration trên DB tạm, chưa nâng DB demo hiện có.** SQLite bật foreign_keys/busy timeout/BEGIN; mutations dùng BEGIN IMMEDIATE, PostgreSQL dùng row locks. Không thay AI DB.

PostgreSQL: cài `.[postgres]`, tạo DB riêng do operator quản lý, export `SOCIAL_DATABASE_URL`, chạy `alembic upgrade head` trên DB mới rồi test. Chuyển dữ liệu SQLite không được thực hiện tự động: backup, tạm dừng writes, migration schema, copy có đối chiếu row/identity/FK, revoke hoặc chuyển sessions có kiểm soát, kiểm thử rồi đổi URL; giữ DB cũ để rollback. Chưa có PostgreSQL server test, chỉ compile migration SQL offline.

`alembic downgrade base` **xóa bảng social/auth**, chỉ chạy trong test DB hoặc sau backup/duyệt thao tác dữ liệu. Test migration dùng DB tạm, không chạy downgrade DB thật. Không auto-clean dữ liệu người dùng khi startup; retention/bảo trì sessions cần chốt trước production.

## Kiểm thử

```powershell
& ./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
```

Mỗi test dùng SQLite file tạm đã chạy Alembic thật; có auth/hash/salt/revoke/expiry, RBAC, validation/PII, CORS, rate-limit restart/account/IP, constraints/schema drift, migration và PostgreSQL offline SQL. T009 thêm rollback content+job/audit, IDOR, ancestor visibility, pagination/count, concurrent create/edit, phiên bản/soft-delete/reply-depth. Không tạo user thật. Service chưa có frontend nên không có build frontend riêng.

## Content contract — T009

Tất cả route content yêu cầu Bearer token, kể cả GET/feed. UUID path/parent được validate. POST create yêu cầu header `Idempotency-Key` là UUID (UI dùng `crypto.randomUUID()`), scope theo tác giả và loại post/comment. Lần đầu 201; cùng key/payload 200, `Idempotency-Replayed: true`, trả resource ở **trạng thái hiện tại**, không sinh thêm job/audit. Cùng key khác body/post/parent 409. Replay sau xóa chỉ trả tombstone, không khôi phục body. Không lưu raw token trong idempotency key.

| Route | Input / response |
|---|---|
| `POST /api/v1/posts` | `{body}` → post pending |
| `GET /api/v1/posts/{id}` | Public hoặc chính tác giả/moderator/admin; không có quyền trả 404 |
| `PATCH /api/v1/posts/{id}` | `{body,expected_revision,expected_decision_version}`; chỉ tác giả |
| `DELETE /api/v1/posts/{id}` | JSON `{expected_revision,expected_decision_version,reason?}`; author soft-delete, admin ẩn bài người khác cần reason |
| `POST /api/v1/posts/{id}/comments` | `{body,parent_id?: UUID}`; parent phải tồn tại/cùng post/được quyền đọc/chưa xóa; tối đa depth 32 |
| `GET /api/v1/posts/{id}/comments` | `page=1&page_size=20`, đã lọc quyền/ancestors, tăng dần `(created_at,id)` |
| `GET /api/v1/comments/{id}` | Guard content và mọi ancestor; author chỉ xem body của chính mình, không trả body parent |
| `PATCH /api/v1/comments/{id}` | Như post edit; parent/post/author/id không được thay đổi |
| `DELETE /api/v1/comments/{id}` | Như post delete, có JSON body |
| `GET /api/v1/feed` | Chỉ post public, giảm dần `(created_at,id)`, không gồm own pending |

Body 1–8000 ký tự Unicode hợp lệ, không NUL/không chỉ whitespace, giữ nguyên spelling/spacing. Reject fields dư như author_id/visibility/risk; HTML được lưu như text, frontend T010 phải render text, không dùng dangerouslySetInnerHTML. Page 1–10000, page_size 1–50; response `{items,total,page,page_size}` với total sau lọc quyền. Offset pagination có thể dịch trang khi có bài mới, không phải snapshot cursor.

Create **luôn** `PENDING_MODERATION/QUEUED/UNKNOWN`, content + job + audit cùng transaction. Worker T012/T017 mới được áp LOW→PUBLISHED, REVIEW→PUBLISHED_FLAGGED sau advisory hợp lệ; không có mock score fallback trong runtime. `policy_version` bắt đầu null, job chọn snapshot `social-policy-shadow-0.2` khi claim. Không có HIGH auto-hold hoặc auto-ban. Trước khi worker chạy/AI sẵn sàng, bài mới vẫn pending; moderator có thể review thủ công qua API dưới đây.

Edit tăng content_revision và decision_version, pending lại, invalidate jobs cũ (SUCCEEDED/STALE_IGNORED), tạo job mới, giữ audit metadata; không lưu bản sao body cũ ở T009. Score/evidence/result persistence thuộc task integration sau. Require cả expected versions cho edit/delete; xung đột kể cả admin decision mới hơn trả 409. Parent immutable ngăn cycle; DB composite FK cùng post và CHECK chống self-parent là lớp bảo vệ bổ sung.

Chỉ author được sửa body, **admin không viết lại text của người khác**. Author delete → DELETED_BY_AUTHOR/body=null, terminal. Admin DELETE nội dung người khác → HIDDEN/REJECTED có reason/version/audit, không bypass appeal/lease đang mở. T017 có manual decisions offline; T013/T018 bổ sung dashboard, restore, reports, appeals và audit reader.

## Worker và Admin offline — T012/T017

Trước lần chạy đầu, từ service root:

```powershell
& ./.venv/Scripts/python.exe -m pip install -r requirements-dev.lock
& ./.venv/Scripts/python.exe -m pip install -e . --no-deps
# Sau backup và dừng server/worker đang dùng Social DB:
& ./.venv/Scripts/python.exe -m alembic upgrade head
```

Chạy AI legacy từ V3 root với `AI_SERVICE_TOKEN` đã cấp qua environment/secret source, checkpoint hiện hành giữ nguyên. Nếu cần đúng V1 gốc, đặt MODEL_PATH tường minh; runtime legacy hiện có thể auto-select refined V1.1 approved như T007 đã ghi. Không đổi threshold để né lỗi contract.

```powershell
& ./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-proxy-headers
```

Worker dùng **cùng giá trị khóa** ở `SOCIAL_AI_SERVICE_TOKEN`, origin tại `SOCIAL_AI_BASE_URL` (mặc định `http://127.0.0.1:8000`). Cấp cả hai biến secret trong các shell tương ứng; không đưa khóa vào lệnh URL/source/frontend hoặc hardcode ví dụ. `.env.example` không tự load. Sau đó, từ service root:

```powershell
& ./.venv/Scripts/python.exe -m shieldvi_social.worker --stats
& ./.venv/Scripts/python.exe -m shieldvi_social.worker --once
# Hoặc chạy liên tục, Ctrl+C để dừng:
& ./.venv/Scripts/python.exe -m shieldvi_social.worker
```

Social API (8001), AI (8000), worker và Social Web chạy riêng. Social Web đã có nút Làm mới để cập nhật trạng thái/feed. Worker không phụ thuộc admin online. `--stats` không cần AI token; worker xử lý cần token tối thiểu 32 ký tự. Không tự khởi động worker trong web lifespan.

Tham số env: `SOCIAL_AI_CONNECT_TIMEOUT=3`, `SOCIAL_AI_READ_TIMEOUT=60`, `SOCIAL_WORKER_LEASE_SECONDS=180`, `SOCIAL_WORKER_MAX_ATTEMPTS=3`, `SOCIAL_WORKER_POLL_SECONDS=2`. Lease phải vượt read + 3×connect + 5 giây; đo latency model thật trước khi tăng. HTTP client không tin proxy env, không follow redirect, cap response 1MiB, validate schema/version/finite score/correlation/evidence. Bearer service key chỉ backend↔AI.

Claim QUEUED/RETRY_WAIT đến hạn hoặc PROCESSING lease hết hạn: SQLite atomic BEGIN IMMEDIATE, PostgreSQL SKIP LOCKED; token lease mới cho mỗi lần claim. Commit claim trước HTTP, không giữ DB transaction khi inference. Claim crash vẫn tính attempt. Retry network/timeout/429/5xx/schema/correlation có giới hạn, delay 5s rồi 30s + 0–20% jitter, Retry-After số giây tối đa 1h; 4xx khác dừng để operator xử lý. Hết attempts → FAILED_PERMANENTLY + manual queue, không vô hạn retry và không tự approve.

Snapshot text/context tối thiểu nằm **chỉ trong Social DB** cho job đang chờ/retry để request_id có payload nhất quán. Context dùng opaque IDs, timestamps/parent thật, có parent closure, tối đa 50 context nodes, mỗi context text tối đa 1000 ký tự, tổng 64000 ký tự; không email/password/token/IP và không bịa mentioned_user_ids. Window bounded/partial ghi limitation, không suy repeated từ một item. Terminal/delete/edit xóa snapshot text, giữ hash/metadata. `moderation_results` lưu version/score/signals (có thể có lexical fragments), không lưu raw comment text riêng; retention/privacy trước production vẫn cần duyệt.

Kết quả chỉ apply khi lease/token/request/content revision/decision version/policy snapshot còn hợp lệ và content còn pending. Result + visibility + audit + job completion cùng transaction; mỗi job tối đa một result/audit apply. Chấp nhận inference **at-least-once** khi crash/network; không cam kết GPU chỉ tính một lần, nhưng quyết định không nhân đôi. Edit/delete/manual decision vô hiệu job cũ. AI không đọc/ghi Social DB, không gọi ngược Social API.

Policy `social-policy-shadow-0.2` thực thi thiết kế T016: score/TOXIC/lexicon/directed/repeated chỉ dẫn tới REVIEW/PUBLISHED_FLAGGED; không có luật HIGH auto-hold. Hợp lệ không tín hiệu → LOW/PUBLISHED. AI lỗi → UNKNOWN/PENDING + retry/manual. Advisory suggested_action không được phép ẩn/xóa/ban. Đây là triển khai shadow được yêu cầu trong T012, không nạp `contracts/moderation_policy.example.json` draft làm cấu hình enforce.

### Vận hành thủ công T017 (T013/T018 mở rộng bằng dashboard/appeal)

Tất cả endpoint dưới dùng **Bearer user token**, role moderator/admin đọc từ DB; không dùng service key AI. Task không tạo/cấp staff account thật, chỉ test fixture role; quy trình provisioning/admin UI thuộc chặng quản trị sau.

- `GET /api/v1/moderation/jobs`: counts, queue_size, retry_attempts, expired_leases, oldest wait, model_availability và tối đa 50 failed job IDs/error codes; không trả text/snapshot/token. Availability dựa trên outcome 5 phút gần nhất, không phải GPU health probe.
- `POST /api/v1/moderation/decisions`: `{entity_type:"post"|"comment",entity_id,action:"approve"|"hide"|"restore",expected_revision,expected_decision_version,reason,false_positive?:false}`. Hoạt động không cần AI/GPU; tăng decision_version, audit actor/time/reason, invalidate jobs. Không restore DELETED_BY_AUTHOR; conflict 409. Appeal mở phải resolve qua appeal endpoint; không tự cấp role từ request.
- `POST /api/v1/moderation/jobs/{job_id}/retry`: `{expected_revision,expected_decision_version,reason}`, chỉ FAILED_PERMANENTLY còn đúng pending revision. Reset attempts của chu kỳ, giữ total_attempts/retry_count; request_id mới và snapshot mới; không publish trực tiếp.

Nếu AI down quá 3 attempts, admin có thể duyệt thủ công hoặc requeue sau khi sửa lỗi. Không hứa SLA. SYSTEM audit có actor_type=system, actor_id=null, identifier=moderation-worker; không mạo danh tác giả. Manual decisions có policy version manual-review-v1. Downgrade 0003 bị từ chối khi có system audit vì 0002 không biểu diễn được actor null: dùng backup trước migration đã kiểm chứng thay vì mất lịch sử.

### Evidence T011/T012/T017

```powershell
& ./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
& ./.venv/Scripts/python.exe tests/run_worker_smoke.py
```

Smoke chạy hai server loopback, worker CLI và SQLite/tài khoản tạm; AI fixture có marker explicit, score **stub**, tuyệt đối không phải production fallback. Bao gồm AI down→retry→recover/publish, profanity flagged và manual approve lúc AI offline. Real checkpoint inference/GPU/Colab, PostgreSQL row locks/server và tải thực chưa kiểm chứng. Auto-hold HIGH vẫn tắt. Không chạy migration trên DB demo/user trong quá trình kiểm thử task.

Feed chỉ public. Direct GET/comment list kiểm tra post và toàn bộ ancestor comment; parent hidden/pending/held/deleted che descendants đối với người khác mà không đổi state con. Author được xem content của chính mình qua direct GET nhưng không body ancestor của người khác; staff xem theo quyền. Comment list trên post private chỉ truy cập được bởi post author/staff, và author chỉ thấy comment của mình; direct GET riêng vẫn cho comment author thấy bản của mình. Deleted items không vào list. Khi parent khôi phục, chỉ descendants vốn public mới hiện lại. Cờ/risk/review nội bộ của người khác không public: PUBLISHED_FLAGGED được trả là PUBLISHED, risk/review=null cho người xem thường.

Content mutation limiter theo user_id: mặc định 30/60s, cấu hình `SOCIAL_CONTENT_RATE_LIMIT` và `SOCIAL_CONTENT_RATE_WINDOW_SECONDS`, DB riêng với auth limiter. Dedupe replay không tính thêm quota; lỗi permission/state sau limiter có tính quota. Rate budget commit trước transaction content; content/job/audit vẫn atomic. CORS hỗ trợ PATCH/DELETE và Idempotency-Key, không cookie credentials.

Migration downgrade `0002_content → 0001_users` xóa content/jobs/audit nhưng giữ auth; chỉ dùng DB tạm hoặc sau backup/duyệt dữ liệu. Test roundtrip có reply graph trên SQLite và giữ users/sessions; PostgreSQL mới compile SQL offline, chưa kiểm chứng row locks trên server thật.

Tham chiếu kỹ thuật: [Argon2 PasswordHasher](https://argon2-cffi.readthedocs.io/en/stable/api.html), [SQLAlchemy SQLite transaction/FK](https://docs.sqlalchemy.org/en/20/dialects/sqlite.html), [Alembic tutorial](https://alembic.sqlalchemy.org/en/latest/tutorial.html).
