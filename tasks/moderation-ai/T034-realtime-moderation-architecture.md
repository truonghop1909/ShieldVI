# T034 — Kiến trúc và contract kiểm duyệt hội thoại realtime

**Dự án:** ShieldVI · **Trạng thái ban đầu:** TODO / NOT STARTED (chỉ đổi theo evidence) · **Nhánh:** Realtime Moderation & Self-service ML Studio

**Mục tiêu:** Định nghĩa luồng mỗi tin nhắn vừa gửi được lưu, đưa vào queue, phân tích với ngữ cảnh hội thoại và đẩy kết quả trở lại giao diện; không cản trở gửi tin nhắn.

**Phụ thuộc:** tham khảo phần kiến trúc kỹ thuật T033 (không yêu cầu T033 formal DONE). Các task mới là phạm vi triển khai kỹ thuật; T028–T033 không tự đổi trạng thái khi chưa đủ formal acceptance.

## Công việc triển khai
1. Audit hiện trạng Social Web/Chat hoặc comment-thread, Social API, moderation-ai, worker, DB, event transport và Dashboard. Xác định app thực tế có chat 1–1, nhóm, bình luận hay chỉ thread; giữ scope tương thích, nếu chưa có mô-đun chat, thiết kế tối thiểu một **Live Conversation Demo** có lưu message thật trong DB test, không mở rộng thành hệ thống DM production ngoài scope.
2. Vẽ sequence gửi comment/message → ghi DB → phát outbox → worker AI → ghi advisory vào DB → fanout event → UI; phương án thất bại/retry. Chọn SSE hoặc WebSocket theo stack đang có; ghi lý do và fallback polling có backoff.
3. Chuẩn hóa dữ liệu: `conversation_id/thread_id`, `message_id/comment_id`, `parent_id`, `author_id`, `timestamp`, `client_request_id`, `message_revision`, `analysis_revision`, `model_version`, `rules_version`, `status`, `updated_at`.
4. Chuẩn hóa trạng thái `QUEUED`, `PROCESSING`, `COMPLETED`, `RETRYING`, `FAILED`, `SUPERSEDED`, có thể `NOT_ANALYZED` cho trường hợp ngoại lệ. Định nghĩa cách hiển thị và kiểm soát quyền xem.
5. Định nghĩa API contract/event envelope ví dụ `conversation.message.created`, `moderation.analysis.updated`, `moderation.analysis.failed` (tên phải thích ứng hệ thống). Schema có ID bền vững, revision, server timestamp, correlation ID và không chứa PII thừa.
6. Chọn phạm vi ngữ cảnh: parent chain, reply sibling gần nhất, diễn biến trước đó theo actor-target và giới hạn có cấu hình; chỉ recompute phần cần thiết, không inference toàn bộ N message sau mỗi lần gửi. Xử lý edit/delete, reordered events, concurrent writers.
7. Thiết kế budget độ trễ: ACK lưu thành công sớm; cập nhật trạng thái AI ngay khi có job; đo enqueue, queue wait, inference, update/fanout riêng. SLO chỉ công bố khi đã đo trên phần cứng thật, không hứa inference tức thì trên CPU.
8. Viết contract version mới, migration plan không phá API/DB hiện có, bảo đảm tương thích backward.

## Nghiệm thu
- Có architecture + sequence + ADR lựa chọn push transport và phạm vi context; API/event schemas được review, validation tests chạy PASS.
- `message_id`, `analysis_revision`, idempotency và xử lý sự kiện cũ được định nghĩa bằng test contract.
- Không dùng raw TOXIC đơn lẻ để tạo directed attack hoặc repeated; không nhầm moderation result với hành động visibility.

## Bằng chứng / đầu ra
- `docs/realtime_moderation/ARCHITECTURE.md`, `SEQUENCE.md`, `CONTRACTS.md`, `SLO_AND_FAILURES.md` (đề xuất, dùng đúng cấu trúc repo).
- Migration/compatibility checklist; contract test log; cập nhật `AUTO_PROGRESS.md`.


## Implementation specification (repository audit 04/11/2026)

- **Status:** DONE_VERIFIED
- **Dependencies:** Read verified T033 architecture; formal T033 completion is not a prerequisite. FormalT028/T029 BLOCKED and T030–T033 PARTIAL remain independent.
- **Architecture context:** Social API FastAPI/SQLAlchemy schema0004, bearer sessions; posts/comments, durable worker and review/appeal already exist. Approved AI defaultV1.1 with threshold.41; v5 signal rules, legacy internal contract1.0.
- **Input:** authenticated requests and immutable synthetic fixtures; canonical model/dataset manifests when applicable.
- **Output:** implemented behavior below, versioned contract, test logs, source SHA, task evidence.
- **Backend/frontend/AI/database scope:** `docs/realtime_moderation/`; reuse existing modules and original API. No live migration/default-model mutation.
- **Concrete design:** SSE authenticated fetch; stable cursor, public-post read permission + explicit membership, no browser AI token.
- **Contract/schema:** `contracts/realtime_event.schema.json`; pin schema/version, IDs, content_revision, decision_version and analysis provenance; fail closed on unknown version.
- **Acceptance:** all original Nghiệm thu criteria above plus existing tests pass, negative authorization/error paths verified. NOT_RUN is not PASS; no DONE_VERIFIED from docs alone.
- **Unit tests:** valid/malformed schema, limits, stale revision, duplicate IDs, unauthorized caller and absence of side effects.
- **Integration tests:** real temporary SQLite and existing services/worker, restart/retry/idempotency and transaction rollback. Actual inference/training tested separately when required.
- **E2E:** local browser when UI is in scope, independent contexts, no mocked API claimed as actual. For architecture-only T034, contract/sequence validation replaces browser testing.
- **Security/privacy:** bearer auth + server RBAC; membership/post visibility checked; no credentials in URL/log, no raw evidence to normal user; upload/config allowlists and no shell/eval of external input.
- **Errors/recovery:** bounded retry/backoff; truthful queued/failed/cancelled/stale states; explicit missing rights/model/data; preserve user input and idempotency key across retries.
- **Performance:** cap body1MiB/request, content8000chars, context50comments, event page100, no neural inference in send request. These are budgets/limits, not measured latency promises; record real timings.
- **Evidence:** [docs/realtime_moderation/ARCHITECTURE.md](../../docs/realtime_moderation/ARCHITECTURE.md); additional verified logs/outputs are listed below.
- **Definition of Done:** all task acceptance met with actual tests and retained evidence; otherwise PARTIAL/BLOCKED with exact missing criteria; update shared task order/progress.
- **Current risks/blockers:** Verified local evidence is recorded below; formal human-gold gates remain unmet. GPU/paid/external/private data/production not authorized. Training Studio CPU smoke authorized by current user only after accepted synthetic dataset/preflight. T041 also depends on T040 for unlabeled inputs.

Common safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md). Imported source preserved at workspace task-pack path; SHA/rename map in TASK_MERGE_REPORT.md.


### Execution evidence

Architecture/contracts drafted from audited canonical services; schema/status/revision tests running, no model/DB/default changes.



### Execution evidence

Architecture/sequence/transport ADR/contracts/budgets/failure+compatibility plan complete. SSE authenticated fetch chosen over extraWebSocket; public-post+membership visibility preserved.13contract testsPASS including malformed identity/time, privacy fields, ordering/stale versions; no runtime/model/DB changes.

- docs/realtime_moderation/ARCHITECTURE.md
- contracts/realtime_event.schema.json
- reports/task_rollout_20261104/T034_tests_final.log


---

## Additional Social Feed v2 specification — 04/11/2026

Initial source status below is not an override of verified historical work. Current v2 acceptance is tracked separately.

# T034 — Kiến trúc realtime cho bài đăng, bình luận và trả lời

**Trạng thái ban đầu:** `NOT_STARTED — VERIFY_IN_REPOSITORY`  
**Độ ưu tiên:** `P0`  
**Phụ thuộc:** Đọc và kiểm chứng phần liên quan của T032–T033; không coi task bị BLOCKED là đã DONE  
**Loại:** Thực thi code + kiểm thử + evidence; không chỉ thiết kế tài liệu.

## 1. Mục tiêu

Chốt thiết kế cho **Social Feed**, nơi U01 đăng bài, U02–U05 bình luận hoặc trả lời, dữ liệu hiện trên các trình duyệt khác nhau không cần F5, AI kiểm tra comment mới và Moderator nhận cảnh báo qua kết nối realtime. Không tạo màn hình private chat làm demo chính.

## 2. Phạm vi

Social API, Social DB, session/auth, worker/outbox, Moderation AI contracts, social frontend, moderator frontend, luồng đăng bài–comment–reply và luồng AI offline.

## 3. Các bước thực hiện

1. Audit có giới hạn: tìm API/model hiện có cho post, comment, reply, auth/RBAC, AI job, review/appeal, events; ghi phần có thể reuse, phần còn thiếu và rủi ro. Kiểm tra `git status --short` trước khi sửa.
2. Vẽ luồng tuần tự: `POST post/comment` → DB commit → durable moderation job → ACK → event `comment.created` → worker → versioned AI assessment → event `comment.moderation.updated` → live moderator. Không để comment HTTP chờ inference trên CPU.
3. Quyết định SSE hoặc WebSocket dựa trên hiện trạng. Với transport server→client, xem xét SSE + HTTP POST; giải thích lựa chọn, xác thực subscribe, quyền xem từng post, reconnect/resume.
4. Định nghĩa state machine gồm `PENDING_ANALYSIS`, `ANALYZING`, `ANALYZED`, `NEEDS_REVIEW`, `RETRYING`, `AI_UNAVAILABLE`; ánh xạ sang các enum hiện hữu thay vì tự tạo nếu đã có.
5. Thiết kế atomicity: comment và outbox/job ghi trong cùng transaction, hoặc chiến lược reconciliation có test; idempotency key, version/revision/sequence, retry/backoff/dead-letter.
6. Thiết kế phân quyền role viewer/author/moderator/researcher; xác thực actor từ session, cấm user tự khai `user_id` tùy ý, cấm lộ moderator evidence qua events public.
7. Thiết kế policy xử lý comment khi AI thất bại: comment vẫn lưu, visibility theo policy hiện tại, có trạng thái UNKNOWN/retry. Không auto-hide chỉ theo score.
8. Liệt kê thay đổi tương thích ngược đối với hợp đồng v1/v2; không đổi v1/v2 contract nếu chưa có versioning/migration.

## 4. API, dữ liệu và hợp đồng tích hợp

Sơ đồ schema/event tham khảo (điều chỉnh theo repo): `post.created(post_id, actor_id, revision, event_id)`, `comment.created(post_id, comment_id, parent_id, actor_id, revision, event_id)`, `comment.moderation.updated(comment_id, job_state, assessment_version, event_id, seq)`, `moderation.review_requested(post_id, comment_id, risk, evidence_ids, model_version)`. Mỗi event có phạm vi người nhận/role và chính sách lọc dữ liệu.

## 5. Kế hoạch kiểm thử

- Contract tests cho event payload, payload thiếu version và role-based filtering.
- Kiểm tra threat model: unauthorized subscription, reconnect/stale event, duplicate requests, worker down, out-of-order completion.
- Đối chiếu schema với client đang có; không gọi thiết kế là chạy realtime khi chưa có code runtime.

## 6. Acceptance criteria / Definition of Done

- [ ] Có `REPO_AUDIT` nêu rõ hiện trạng reuse và các blocker.
- [ ] Có ADR SSE/WebSocket hoặc kế thừa transport đang có, nêu lý do.
- [ ] Có sequence diagram + state machine + event/API contract versioned.
- [ ] Có bản đồ RBAC, idempotency, durability, reconnect, stale updates, AI offline.
- [ ] Có test plan truy xuất được từ từng acceptance của T035–T038.
- [ ] Không đổi default model, policy, readiness lock.

## 7. Deliverables và bằng chứng

`docs/` hoặc vị trí chuẩn của repo: `REALTIME_SOCIAL_ARCHITECTURE.md`, `EVENT_CONTRACT.md`, `REALTIME_SECURITY_MATRIX.md`, `REPO_AUDIT.md`; cập nhật task order/progress với evidence.



Shared safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md), Social Feed v2 section. The source journal was unstarted; actual execution follows below.

## T034 Social Feed v2 — IN_PROGRESS, 04/11/2026

Verified and merged the new source pack; audit Social Feed gaps before runtime changes.

Evidence: reports/social_feed_v2_20261104/MERGE_MANIFEST.json

## T034 Social Feed v2 — DONE_VERIFIED, 04/11/2026

Audited actual post/comment APIs, authenticated SSE, worker/context, Studio and Social Feed UI gaps. Added transport ADR, state mapping, RBAC and acceptance trace.13 contract tests PASS; original model/readiness/runtime untouched.

Evidence: docs/realtime_moderation/REPO_AUDIT.md, reports/social_feed_v2_20261104/T034_contract.log
