# Giao kèo API giữa Social API và AI Moderation

T015 chuyển implementation AI sang `services/moderation-ai/app`, giữ contract và URL cũ; `/dashboard/` là research React tại `apps/moderation-web/legacy-v3`, còn dashboard Social dùng Social API. HTTP/OpenAPI/static/model outputs trước/sau được đối chiếu trong [báo cáo migration](../archive/implementation_reports/T015_MIGRATION_REPORT.md). Các mô tả đường dẫn legacy ở các mốc bên dưới là snapshot lịch sử.

T014/T019 không đổi schema hoặc threshold: Social/internal AI 422 redact cả unknown JSON field names, internal AI 5xx không echo lỗi/path từ model dependency; legacy error contract giữ nguyên. Dashboard stats dùng chung auth read session để tránh SQLite lock cycle; response fields không đổi. [Evidence/runbook](../archive/implementation_reports/T014_T019_VALIDATION_REPORT.md).

**T013/T018 đã bổ sung dashboard, reports, appeal và audit** trên Social API/schema `0004_review`. Auth/content/feed/worker ở `ShieldVI_V3_Hybrid_Review/services/social-api`, AI vẫn ở legacy `app/` cho tới T015. [Báo cáo hiện hành](../archive/implementation_reports/T013_T018_ADMIN_REPORT.md); [mốc worker T012/T017](../archive/implementation_reports/T012_T017_WORKER_REPORT.md). Các mục T008/T009/T017 bên dưới là snapshot theo chặng; endpoint decisions được mở rộng theo mục mới này.

## Review / reports / appeals — T013/T018

OpenAPI sinh từ Social API chạy thật với DB tạm: [social-review.openapi.json](../../contracts/social-review.openapi.json). Browser chỉ gọi Social API bằng user Bearer, không nhận AI service token. Các route yêu cầu auth; role lấy lại từ DB mỗi request. Mọi response no-store, validation không echo dữ liệu.

| Route | Quyền / payload | Kết quả |
|---|---|---|
| `GET /api/v1/moderation/queue` | moderator/admin; `tab=review|reports|appeals|failed|all`, `entity_type=all|post|comment`, page 1–10000, page_size 1–50 | `{items:[{entity_type,content,priority,report_count}],total,page,page_size}`; không gồm author-deleted |
| `GET /api/v1/moderation/content/{kind}/{id}` | moderator/admin; kind post/comment | `{entity_type,content,policy_version,parent_context,ai,job,appeals,reports,claim}`; context full text staff-only, ai null nếu thiếu/current deleted; không gửi job request_json/service token/reporter_id |
| `GET /api/v1/moderation/content/{kind}/{id}/audit` | moderator/admin; page/page_size như queue | `{items,total,page,page_size}` với actor/type/role, UTC epoch timestamp, event/reason, revision/decision version, before/after visibility, policy, structured details; không bulk export |
| `POST /api/v1/moderation/content/{kind}/{id}/claim` | moderator/admin; `{expected_revision,expected_decision_version,reason}` | detail, lease 300s; nhận duyệt tăng decision version, vô hiệu AI job cũ, giữ visibility |
| `POST /api/v1/moderation/decisions` | moderator/admin; `{entity_type,entity_id,action:approve|hide|restore,expected_revision,expected_decision_version,reason,false_positive?:false}` | current content; human audit/provenance; false_positive chỉ approve/restore, feedback không phải gold |
| `GET /api/v1/me/moderation` | chính user; page/page_size | `{items:[{entity_type,content,decision_reason,appeals,can_appeal}],total,page,page_size}`; không có body ancestor hoặc reporter/reviewer identity |
| `GET /api/v1/content/{kind}/{id}/moderation` | chính author; người khác 404, kể cả staff phải dùng staff endpoint | một item như danh sách của mình; deleted chỉ tombstone |
| `POST /api/v1/content/{kind}/{id}/reports` | user auth, không phải author, effective public gồm mọi ancestor; `{expected_revision,expected_decision_version,reason}` | 200 `{status:RECEIVED}`, dedupe reporter/content/revision kể cả report đã đóng; không trả report/reporter ID |
| `POST /api/v1/content/{kind}/{id}/appeals` | chính author, HIDDEN/HELD; `{expected_revision,expected_decision_version,reason}` | 201 `{id,content_revision,appealed_decision_version,status,reason,outcome,resolution_reason,created_at,resolved_at}`; không tự restore |
| `POST /api/v1/moderation/appeals/{appeal_id}/resolve` | moderator/admin; `{expected_revision,expected_decision_version,reason,outcome:RESTORED|UPHELD}` | staff detail; appeal RESOLVED, review RESOLVED, visibility PUBLISHED hoặc HIDDEN; actor/reason/outcome audit |

`content` giữ format post/comment hiện có. `ai` là advisory response schema 1.0 đã lưu cho đúng revision, có model_name/version, lexicon_version, ai_label, toxicity_score, model_threshold=0.41, analyzed_at, lexical/target/repeated evidence và limitations. Không có kết quả thì null, không score=0. Deleted không trả body/AI evidence/context qua detail. Audit human `details` có review/risk, false_positive hoặc appeal/outcome, model/lexicon/job/request ID nếu có; lúc AI offline là null. Audit system T017 liên kết job/request trong reason với result lưu bền.

Guards:

- 401 thiếu/expired/revoked/suspended; 403 role sai; 404 resource không thuộc author/không effective public; 409 revision/version thay đổi, terminal, claim của reviewer khác, appeal đã đóng/sai revision; 422 invalid/blank reason hoặc >500; 429 content mutation limit chung. Reason không NUL/surrogate. Body cap 16KiB cho review, response validation không echo reason/token.
- Hai quyết định cùng expected version: đúng một thành công; duplicate không thêm audit thứ hai. SQLite BEGIN IMMEDIATE, PostgreSQL content lock theo post→comment→appeal; PostgreSQL mới kiểm tra SQL offline, chưa test server.
- Approve cho pending/flagged/public; hidden/held dùng restore. Author-deleted terminal. Appeal mở phải resolve tường minh, không bypass bằng manual decisions hoặc admin DELETE. Không bắt buộc nhận claim trước quyết định, nhưng lease của reviewer khác được tôn trọng. Lease hết hạn reader hiện QUEUED/APPEALED đúng nguồn, không đổi visibility; chưa có background sweeper cập nhật cột review_status vật lý.
- Appeal một OPEN/content/revision, dedupe cùng appealed decision version; resolve tăng decision version. Sau UPHELD tác giả có thể nộp appeal mới cho quyết định mới, không áp giới hạn thời gian/SLA trong demo. Author edit đóng appeal cũ SUPERSEDED, author delete đóng AUTHOR_DELETED; lịch sử giữ lại, stale resolve 409.
- Report chỉ tăng queue review, không đổi risk/visibility/decision version; report count không phải bằng chứng tự động. Quyết định/manual edit/delete đóng reports của revision, vẫn giữ dữ liệu dedupe/audit. Staff detail tối đa 50 reports và 50 appeals, author tối đa 20 appeals lịch sử/content; audit có phân trang.
- Queue priority (số nhỏ trước): held 0, failed pending 1, pending 2, open appeal 3, repeated candidate 4, còn lại 5; tiếp theo created_at cũ, report_count giảm, type/ID. Không starvation guarantee giữa nhóm khi tải lớn; cần vận hành/đánh giá ở T014/T019. Cờ repeated là advisory từ result hiện có, không nâng HIGH.
- AI retry/late result không ghi đè quyết định người duyệt. Hidden ancestor che descendants cả direct/list/count/report; restore cha không restore child bị ẩn riêng. User status không lộ ancestor ẩn của người khác.

## Worker / manual fallback — T012/T017

OpenAPI Social API hiện tại: [social-worker.openapi.json](../../contracts/social-worker.openapi.json). Các snapshot auth/content phía dưới giữ làm mốc T008/T009.

- Worker gọi internal AI bằng service Bearer token, không dùng user token/browser key. Retry/correlation/evidence/lease/version guards và mapping shadow nằm trong [README backend](../modules/social_api.md).
- `GET /api/v1/moderation/jobs`: user Bearer, moderator/admin; queue_size/counts/retry_attempts/expired_leases/oldest_wait_seconds/model_availability và tối đa 50 failed job IDs/error codes, không text/snapshot/token.
- `POST /api/v1/moderation/decisions`: user Bearer, moderator/admin; `{entity_type,entity_id,action:"approve"|"hide",expected_revision,expected_decision_version,reason}`. Không cần model; actor/time/reason audit, optimistic version guard, stale job invalidate, author-deleted không restore. 403 role, 404 missing, 409 stale/terminal, 422 invalid.
- `POST /api/v1/moderation/jobs/{job_id}/retry`: user Bearer, moderator/admin; `{expected_revision,expected_decision_version,reason}` cho failed job còn đúng pending revision. Giữ total attempts/history, tạo request_id mới, không publish trực tiếp.
- Create/edit vẫn trả pending ngay. AI hợp lệ LOW mới PUBLISHED; REVIEW→PUBLISHED_FLAGGED; lỗi/schema/correlation/lease/policy không hợp lệ không được approve. HIGH auto-hold không được bật.

## Social content đã triển khai — T009

Spec hiện tại sinh từ server thật: [social-content.openapi.json](../../contracts/social-content.openapi.json). [Service README](../modules/social_api.md) giải thích guards và config. `social-auth.openapi.json` bên dưới là snapshot T008 giữ để đối chiếu.

- Tất cả content routes yêu cầu Bearer. POST `/api/v1/posts` nhận `{body}`; POST `/api/v1/posts/{id}/comments` nhận `{body,parent_id?}`. Cần `Idempotency-Key` UUID; 201 lần đầu, 200 replay cùng payload/current resource, 409 key khác payload, không tạo job trùng.
- GET `/api/v1/posts/{id}`, `/api/v1/comments/{id}` và `/api/v1/posts/{id}/comments`: kiểm tra visibility/ownership/staff và ancestors; không được phép xem trả 404. Không trả body ancestor trong reply.
- PATCH `/api/v1/posts/{id}` hoặc `/api/v1/comments/{id}` nhận `{body,expected_revision,expected_decision_version}`, chỉ author; parent/post/author/id không đổi. Tăng revision/version, đưa pending, tạo job mới và vô hiệu job cũ; stale versions 409.
- DELETE cùng đường dẫn nhận JSON `{expected_revision,expected_decision_version,reason?}`. Author soft-delete terminal trả body=null; admin ẩn nội dung người khác (HIDDEN) với reason bắt buộc; admin không viết lại body người khác. Người khác bị 403 hoặc 404; moderator mới chỉ được đọc private ở T009.
- GET `/api/v1/feed?page=1&page_size=20`: chỉ public posts, kể cả author không thấy own pending trên feed. List comments cũng phân trang; page 1–10000, page_size 1–50, total tính sau lọc. Feed giảm dần `(created_at,id)`, comments tăng dần; offset có thể dịch khi có ghi đồng thời.
- Body 1–8000 ký tự không chỉ whitespace; cap request content 128KiB, auth vẫn 16KiB. Reject client-set state/author; field error không echo dữ liệu. Content mutation rate mặc định 30/60s/user (429 + Retry-After); replay dedupe không tính thêm quota.
- Create luôn PENDING_MODERATION/QUEUED/UNKNOWN với job/audit cùng transaction; **chưa có publish tự động** khi chưa tích hợp worker/policy. Cờ PUBLISHED_FLAGGED/risk/review chỉ trả chi tiết cho author/staff; người xem thường nhận PUBLISHED và risk/review=null. Deleted không vào feed/list; tombstone riêng cho author/staff.
- Parent pending/hidden/held/deleted che descendants cho người khác qua cả direct ID/list; restore parent không đổi state con. Author có thể xem riêng content của chính mình nhưng không body ancestor người khác; list trên post private chỉ post author/staff được truy cập và author chỉ thấy comment của mình. Reply depth tối đa 32, same-post FK/self-check và parent immutable chống loop.
- Tại mốc T009 chưa có approve/AI; T017 đã bổ sung manual decisions và worker như phần trên, còn appeal đầy đủ thuộc task sau. HIGH auto-hold vẫn tắt. Social API không gồm `/api/analyze` legacy.

## Social auth đã triển khai — T008

Spec sinh từ server thật: [social-auth.openapi.json](../../contracts/social-auth.openapi.json). Hướng dẫn config/auth/DB: [service README](../modules/social_api.md).

- `POST /api/v1/auth/register`: `{username,email,password}`, 201 trả user; đăng ký tắt mặc định (403); không nhận role/status client; duplicate username/email 409 generic; invalid 422, rate limit 429.
- `POST /api/v1/auth/login`: `{username,password}`, 200 `{access_token,token_type:"bearer",expires_in}`; credentials sai/account absent/suspended đều 401 cùng thông báo; không có refresh tự động.
- `GET /api/v1/me`: Bearer, chỉ trả chính user của session, 401 thiếu/sai/hết hạn/đã revoke; không nhận user_id để chọn người khác.
- `POST /api/v1/auth/logout`: Bearer, 204 revoke session hiện tại; 401 nếu session không hợp lệ.
- `GET /api/v1/admin/access`: read-only RBAC probe, chỉ admin 200, user/moderator 403, thiếu auth 401; không phải endpoint moderation.
- User response: `id,username,role,status,created_at` UTC, không email/password hash. 422 không echo input; request tối đa 16KiB. Role/status lấy DB mỗi request; token opaque random, DB chỉ lưu hash, TTL mặc định 3600s. Không dùng cookie/secret JWT.
- CORS exact origin allowlist, không credentials/wildcard. Login/register rate-limit durable theo peer IP và normalized username; 429 có Retry-After. Frontend T010 phải giữ token trong memory và dùng Authorization header, không đưa token vào URL/localStorage.
- `GET /health`: DB probe, 200 ready hoặc 503 unavailable; startup từ chối schema chưa migrate. Chưa có public users list hoặc endpoint cấp role/admin.

## Social API — ví dụ
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/me`
- `GET /api/v1/feed?page=1&page_size=20`
- `POST /api/v1/posts`
- `GET /api/v1/posts/{post_id}`
- `POST /api/v1/posts/{post_id}/comments`
- `GET /api/v1/posts/{post_id}/comments`
- `GET /api/v1/moderation/queue` (moderator only)
- `POST /api/v1/moderation/decisions` (moderator only)
- `POST /api/v1/moderation/appeals` (author only)

## Internal AI API đã triển khai — `POST /api/v1/moderate/comment`

Request/response examples đã validate: `contracts/moderation_request.example.json`, `contracts/moderation_response.example.json`. Schemas máy đọc: [request](../../contracts/moderation_request.schema.json), [response](../../contracts/moderation_response.schema.json). Python models vendored byte-identical tại AI/Social, có parity tests, không import runtime service chéo.

- Chỉ gọi từ backend/worker, không gọi trực tiếp từ browser.
- Gửi `request_id`, `content_id` opaque, text và context tối thiểu cần thiết, không gửi email/tên thật/password/token.
- Field chuẩn là `toxicity_score` và `model_threshold` (không dùng alias draft model_score/threshold), kèm `model_version`, `lexicon_version`, `analyzed_at`, `lexical_signals`, `target_evidence`, `evidence`, `limitations` và correlation content_revision/content_id/request_id.
- `suggested_action` là advisory, không phải quyết định tự động xóa bài.
- Validate schema, version, timeout, max payload; xử lý 4xx/5xx, idempotent và retry.
- Gửi context cho repeated harassment phải có nguồn/quan hệ rõ, không suy luận từ một bình luận đơn.
- AI legacy `/api/analyze` và `/health` phải tiếp tục tương thích.
- Request thêm content_type, opaque user_id, timezone timestamp, parent_id/mentioned_user_ids đã platform-resolve. Context source social-api, recent_comments có id/user/text/timestamp/parent thật; parent closure, không duplicate/cycle/future context; tối đa 50 nodes/64000 ký tự/1MiB body. Không dùng parent_text rời rạc làm bằng chứng lặp lại.
- `AI_SERVICE_TOKEN` env bắt buộc, tối thiểu 32 ký tự; worker dùng cùng giá trị SOCIAL_AI_SERVICE_TOKEN. Thiếu cấu hình/model/threshold khác 0.41 →503; sai auth→401; invalid payload→422 không echo input; oversize→413; rate/busy→429 có Retry-After. Rate limiter per-process cho private demo.
- Adapter không ghi Social DB hoặc audit request text vào AI DB, không gọi Social API; sử dụng legacy conservative engine, không dùng research_synthetic/0.03. Response score giữ raw precision, không đổi nhãn do rounding; repeated chỉ trả cho actor/content hiện tại có evidence/context thật. Ví dụ score trong JSON không phải inference thật.
