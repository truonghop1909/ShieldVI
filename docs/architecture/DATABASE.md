# Phác thảo database

## Hiện hành T013/T018 — schema `0004_review`

Social API và worker yêu cầu `0004_review`; chưa chạy trên DB demo hiện có. Migration thêm `content_reports` (unique entity/revision/reporter, OPEN/CLOSED), `appeals` (unique entity/revision/appealed decision version, OPEN/RESOLVED/CLOSED, outcome/reason/resolver/timestamps), `review_claims` (PK entity type/id, reviewer FK, revision/source/lease) và nullable `content_audit.details_json`.

Content lock serialize report/appeal/claim/manual/edit/delete; chỉ một OPEN appeal được kiểm tra trong transaction. Cả appeal resolution, content update và audit cùng commit; stale versions không tạo quyết định trùng. Reports không tự hide; author edit/delete đóng công việc cũ theo revision; giữ lịch sử/dedupe. Manual audit details liên kết model/lexicon/job/request khi có, không chứa snapshot/token. Audit reader staff-only, author chỉ đọc trạng thái/lý do quyết định/appeal của mình.

Reviewer lease 300s, expiry được tính khi đọc queue/detail/author status; cột UNDER_REVIEW được thay khi mutation tiếp theo, chưa có sweeper. Lease claim vô hiệu job AI hiện có, expiry tiếp tục manual queue. Downgrade từ chối trước khi drop nếu có reports/appeals/claims hoặc structured audit, không tự xóa lịch sử. Test upgrade/downgrade trống, metadata diff, giữ user/session và lịch sử trên SQLite tạm; PostgreSQL chỉ offline SQL compilation. [Báo cáo T013/T018](../archive/implementation_reports/T013_T018_ADMIN_REPORT.md).

## Mốc T012/T017 — schema `0003_worker`

`0003_worker` mở rộng 0002, chưa áp dụng vào DB demo của người dùng trong task. Moderation_jobs thêm claim_token/lease_until, total_attempts/retry_count, request_json/request_hash, last_error/last_ai_check_at. Snapshot chỉ trong Social DB khi active/retry, clear text khi terminal hoặc content edit/delete. Moderation_results PK job_id/FK cascade, lưu model/lexicon/threshold/score/policy/signals và timestamp. Content_audit hỗ trợ actor_type system và nullable actor_id (worker không mạo danh author).

Result/visibility/audit/job completion cùng transaction, job result không nhân đôi; stale lease/request/revision/decision/policy không được mutate content. Manual approve/hide và failed requeue có user actor/role/reason/version guard. Downgrade bị từ chối nếu có system audit không thể biểu diễn trong schema 0002; dùng backup đã kiểm chứng. Hướng dẫn và evidence: [worker report](../archive/implementation_reports/T012_T017_WORKER_REPORT.md).

## Đã triển khai ở T008

Service mới độc lập tại `V3 root/services/social-api`; schema version `0001_users` qua Alembic, không tự tạo schema ở app startup:

- `users`: UUID string, username/email lowercase unique, password_hash Argon2id, role user/moderator/admin và status active/suspended có CHECK, created_at epoch UTC.
- `auth_sessions`: token_hash SHA-256 primary key, user_id FK users ON DELETE CASCADE, created_at/expires_at epoch UTC và CHECK expiry. Raw token chỉ trả lúc login, không lưu DB.
- `auth_rate_buckets`: key_hash, window_start, count; upsert nguyên tử theo action/peer hoặc account; cleanup cửa sổ cũ. Không lưu IP/username thô ở bảng limiter.

SQLite dev mặc định `services/social-api/data/social.sqlite3` (đường dẫn tuyệt đối tính từ service), không dùng DB review AI. Mọi test dùng file DB tạm riêng đã upgrade Alembic. PostgreSQL dùng `postgresql+psycopg`, optional driver, schema SQL portable; mới kiểm tra offline SQL, chưa có server/data migration thật. Kế hoạch chuyển/rollback trong [README](../modules/social_api.md).

## Bổ sung T009 — schema hiện tại `0002_content`

- `posts`, `comments`: body, author, revision/decision_version, visibility/review/risk tách riêng, timestamps UTC epoch, policy_version nullable (chưa chọn active policy). UUID create_key + request_hash để dedupe theo author và loại content; same key khác payload conflict.
- `comments` có post FK, composite parent FK `(parent_id,post_id) → (id,post_id)`, CHECK không self-parent, depth 0–32; API giữ parent/post immutable nên không tạo cycle. Index feed, thread và parent hỗ trợ query.
- `moderation_jobs` ở mốc T009: entity type/id/revision UNIQUE, request_id UNIQUE, expected_decision_version, policy_version, status/attempts/retry time/outcome. Content mới + job + audit cùng transaction. Edit tạo revision/job mới; delete không tạo job mới. Worker/lease/result application đã bổ sung trong 0003 ở trên.
- `content_audit`: actor id/role, event/reason/time, entity/revision/decision_version, before/after visibility và policy version. Chỉ metadata, không sao chép body vào audit, chưa có API public audit. Author delete là tombstone; admin hide có reason, không hard-delete.
- `content_rate_buckets`: limiter content theo user riêng với auth, bền qua restart. Limiter commit riêng trước transaction content; lỗi ghi job rollback toàn bộ content/audit.
- SQLite mutations dùng BEGIN IMMEDIATE trước auth reads; PostgreSQL lock post rồi comment và kiểm tra expected versions. Feed/list/direct ID lọc effective visibility qua ancestors; không cập nhật hàng loạt state con khi parent ẩn.
- Nâng `0001_users → 0002_content` giữ users/sessions; rollback về 0001 chỉ kiểm thử trên DB tạm, xóa content nhưng giữ auth. Chưa migrate DB thật. Moderation_results đã bổ sung ở 0003; reports/appeals/workflow quản trị đầy đủ bên dưới vẫn là phác thảo. Content_audit đã mở rộng system/manual events T017, không thay toàn bộ workflow T013.

## Social DB (social-api sở hữu)
- `users(id, username UNIQUE, email UNIQUE, password_hash, role, status, created_at)` — password luôn hash bằng thuật toán phù hợp, không lưu plaintext.
- `posts(id, author_id, body, content_revision, decision_version, visibility_status, review_status, risk_tier, policy_version, created_at, updated_at)`
- `comments(id, post_id, author_id, parent_id NULL, body, content_revision, decision_version, visibility_status, review_status, risk_tier, policy_version, created_at, updated_at)`
- `moderation_jobs(id, entity_type, entity_id, status, attempts, next_retry_at, created_at)`
- `moderation_results(id, job_id, model_version, score, signals_json, policy_action, created_at)`
- `moderation_actions(id, entity_type, entity_id, moderator_id, action, reason, created_at)`
- `reports(id, reporter_id, entity_type, entity_id, reason, status, created_at)`
- `appeals(id, author_id, entity_type, entity_id, reason, status, decided_by, decided_at)`

**Quy tắc:** post/comment `status` nằm tại Social DB; kết quả AI advisory không phải trạng thái bài viết. IDs xuyên hệ thống cần opaque/pseudonymous. Có migration/schema version. `parent_id` phải trỏ comment cùng bài, không tự trỏ chính mình. Soft-delete phù hợp với nhu cầu audit, nhưng tôn trọng yêu cầu xóa dữ liệu.

T016: `status` ở câu trên chỉ là cách gọi tổng quát; **không tạo một cột status chung**. Dùng visibility/review/risk riêng theo [T016_POLICY_SPEC.md](T016_POLICY_SPEC.md). Jobs cần content_revision, policy snapshot, expected decision_version, request_id/idempotency key, claim token/lease, outcome và retry timestamps. Actions cần actor type/id, before/after, revision, decision_version, reason, policy version, request/job/appeal correlation. Schema migration chi tiết thuộc task triển khai; đây chưa phải DB hiện có.

## AI review DB (moderation-ai sở hữu)
- lưu request_id, model version, signal metadata, reviewer/annotation nếu có; tránh lưu email/IP/token. Không tự sao chép toàn bộ mạng xã hội. Cân nhắc thời hạn lưu log và chính sách quyền riêng tư.

## Trạng thái moderation đề xuất
Canonical visibility: PENDING_MODERATION → PUBLISHED (LOW) hoặc PUBLISHED_FLAGGED (REVIEW/HIGH shadow); moderator có thể HIDDEN/restore theo bảng quyền T016. UNKNOWN giữ pending; job lỗi không tạo visibility `failed_review`. Review lifecycle tách riêng, appeal resolution lưu outcome. Không cập nhật hàng loạt state con khi parent ẩn/restore; effective visibility kiểm tra ancestors. Ghi lý do quyết định và actor, tránh đè quyết định người duyệt bằng model chạy lại.

## API validation / bảo mật
JWT/HTTP-only cookie hoặc session an toàn; hash password, role check server-side, rate limiting login/comment, pagination, giới hạn độ dài, escape HTML khi render, CSRF nếu dùng cookie auth, CORS chính xác cho từng origin, test IDOR (không sửa/xóa bài người khác), audit admin actions.
