# T035 — Social API: nhận tin nhắn và hàng đợi AI bền vững

**Dự án:** ShieldVI · **Trạng thái ban đầu:** TODO / NOT STARTED (chỉ đổi theo evidence) · **Nhánh:** Realtime Moderation & Self-service ML Studio

**Mục tiêu:** Mỗi thông điệp mới hoặc được sửa trong thread tạo job phân tích an toàn, có idempotency, retry và đồng bộ trạng thái với DB.

**Phụ thuộc:** T034. Các task mới là phạm vi triển khai kỹ thuật; T028–T033 không tự đổi trạng thái khi chưa đủ formal acceptance.

## Công việc triển khai
1. Đường POST tạo tin nhắn/comment: xác thực user và conversation membership, rate-limit, kiểm parent thuộc đúng thread, dùng transaction lưu nội dung và outbox atomically, trả message ID + `moderation_status=QUEUED`.
2. Idempotency theo `(conversation_id, message_id, message_revision, analysis_pipeline_version)`; retry POST với `client_request_id` không tạo 2 message; duplicate job không tạo 2 advisory.
3. Outbox publisher + worker queue durable: retry exponential backoff, dead-letter trạng thái FAILED, thao tác requeue có phân quyền, crash/restart recovery.
4. Để tránh race, áp optimistic revision/compare-and-swap: kết quả revision cũ không thể ghi đè revision mới; delete/tombstone không bị hồi sinh; xử lý hai comment đến gần nhau.
5. Chỉ gửi payload được phép sang AI. Quản lý retention/privacy và structured logs với correlation IDs; redaction message text nếu logs không thật sự cần.
6. Ghi kết quả assessment/evidence vào bảng hoặc cấu trúc phù hợp, giữ raw score/context/target/repeated/policy và visibility tách biệt. Không tự ẩn bài hoặc cập nhật nhãn người.
7. Fanout event sau khi DB commit; consumer reconnect lấy snapshot/since cursor để không bỏ tin.

## Nghiệm thu
- Gửi một tin mới lập tức có bản ghi và job ngay cả khi AI đang offline; khi AI quay lại, kết quả gắn đúng comment/revision, không mất content.
- Ở test giả lập: duplicate POST/job, worker crash, timeouts, edit/delete, out-of-order result, rate-limit, 403/404 conversation scope đều đúng, không có double insert/update.
- Tối thiểu một integration test với DB/queue thật trong môi trường dev/test cách ly; không chỉ mock happy path.

## Bằng chứng / đầu ra
- DB migration/backfill/rollback scripts phù hợp stack, API tests, event audit, retry/recovery logs và hướng dẫn start worker.


## Implementation specification (repository audit 04/11/2026)

- **Status:** DONE_VERIFIED
- **Dependencies:** T034. FormalT028/T029 BLOCKED and T030–T033 PARTIAL remain independent.
- **Architecture context:** Social API FastAPI/SQLAlchemy schema0004, bearer sessions; posts/comments, durable worker and review/appeal already exist. Approved AI defaultV1.1 with threshold.41; v5 signal rules, legacy internal contract1.0.
- **Input:** authenticated requests and immutable synthetic fixtures; canonical model/dataset manifests when applicable.
- **Output:** implemented behavior below, versioned contract, test logs, source SHA, task evidence.
- **Backend/frontend/AI/database scope:** `services/social-api/src/shieldvi_social/`; reuse existing modules and original API. No live migration/default-model mutation.
- **Concrete design:** Reuse Post/Comment/ModerationJob/ModerationResult and Worker. Add transactional event log; retain existing revision/idempotency policy.
- **Contract/schema:** `/api/live/threads/{post_id}/events`; pin schema/version, IDs, content_revision, decision_version and analysis provenance; fail closed on unknown version.
- **Acceptance:** all original Nghiệm thu criteria above plus existing tests pass, negative authorization/error paths verified. NOT_RUN is not PASS; no DONE_VERIFIED from docs alone.
- **Unit tests:** valid/malformed schema, limits, stale revision, duplicate IDs, unauthorized caller and absence of side effects.
- **Integration tests:** real temporary SQLite and existing services/worker, restart/retry/idempotency and transaction rollback. Actual inference/training tested separately when required.
- **E2E:** local browser when UI is in scope, independent contexts, no mocked API claimed as actual. For architecture-only T034, contract/sequence validation replaces browser testing.
- **Security/privacy:** bearer auth + server RBAC; membership/post visibility checked; no credentials in URL/log, no raw evidence to normal user; upload/config allowlists and no shell/eval of external input.
- **Errors/recovery:** bounded retry/backoff; truthful queued/failed/cancelled/stale states; explicit missing rights/model/data; preserve user input and idempotency key across retries.
- **Performance:** cap body1MiB/request, content8000chars, context50comments, event page100, no neural inference in send request. These are budgets/limits, not measured latency promises; record real timings.
- **Evidence:** [services/social-api/src/shieldvi_social/live_app.py](../../services/social-api/src/shieldvi_social/live_app.py); additional verified logs/outputs are listed below.
- **Definition of Done:** all task acceptance met with actual tests and retained evidence; otherwise PARTIAL/BLOCKED with exact missing criteria; update shared task order/progress.
- **Current risks/blockers:** Verified local evidence is recorded below; formal human-gold gates remain unmet. GPU/paid/external/private data/production not authorized. Training Studio CPU smoke authorized by current user only after accepted synthetic dataset/preflight. T041 also depends on T040 for unlabeled inputs.

Common safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md). Imported source preserved at workspace task-pack path; SHA/rename map in TASK_MERGE_REPORT.md.


### Execution evidence

Implement additive canonical-app live routes, engine-scoped transactional event hooks and opt-in worker wrapper. Reuse frozen content/idempotency/jobs/retry/review; explicit extension schema on disposableDB only.



### Execution evidence

Additive canonical Social extension implemented: explicit membership+postvisibility, existing idempotent comment/job transaction, atomic durable minimal events, auth SSE/poll/replay, worker hooks/retry/restart/stale handling.26newcontract/integration testsPASS; fullSocial203PASS/1deprecationwarning. Initial2failures retained: bulkSQL stale invalidation event gap fixed; expiryfixture corrected to satisfy existingDBconstraint. SQLite rollback/deactivation/concurrentPOST/privacy verified; AIresponses are unitfixtures, not claimed realmodel. Base0004/source/readiness1311SHA remain unchanged.

- services/social-api/src/shieldvi_social/live_app.py
- services/social-api/src/shieldvi_social/live_store.py
- services/social-api/src/shieldvi_social/live_routes.py
- reports/task_rollout_20261104/T035_social_regression.log
- docs/realtime_moderation/RUN_LOCAL.md


---

## Additional Social Feed v2 specification — 04/11/2026

Initial source status below is not an override of verified historical work. Current v2 acceptance is tracked separately.

# T035 — Social API: đăng bài, bình luận, reply và AI job bền vững

**Trạng thái ban đầu:** `NOT_STARTED — VERIFY_IN_REPOSITORY`  
**Độ ưu tiên:** `P0`  
**Phụ thuộc:** T034 đủ contract để implement; Social DB/API hiện hữu  
**Loại:** Thực thi code + kiểm thử + evidence; không chỉ thiết kế tài liệu.

## 1. Mục tiêu

Triển khai hoặc hoàn thiện backend: một nick tạo bài, các nick khác comment/reply, comment được lưu ngay và tự xếp hàng AI moderation. Tin tồn tại ngay cả khi AI offline/restart; request retry không tạo bản ghi trùng.

## 2. Phạm vi

`services/social-api` post/comment endpoints, DB schema/migrations trên DB demo, auth/permission, outbox/job, worker lifecycle, publish event. Không sửa Social DB thật hoặc migration production thiếu phê duyệt.

## 3. Các bước thực hiện

1. Kiểm tra API bài đăng và bình luận đã có. Chỉ mở rộng phần thiếu; giữ backward compatibility.
2. Implement `create/list/detail post`, `list/create comment`, `reply by parent_id`; validate parent thuộc cùng post, depth limit, size/type, timestamp từ server, permissions.
3. Lấy actor từ session/JWT đã xác thực; hỗ trợ demo nhiều nick độc lập, không cho client impersonate.
4. Ghi comment + job/outbox atomically (hoặc có recovery thật) trước khi trả ACK; trả canonical `post_id/comment_id/parent_id/created_at/moderation_status`.
5. Idempotency: request_id/idempotency key có constraint, retry từ client hoặc reconnect trả lại bản ghi cũ, không tạo thêm job.
6. Worker claim/retry: chống double-processing, backoff, timeout, limit attempt, restart recovery, failed/unknown state và audit.
7. Phát `post.created/comment.created` sau commit theo đúng quyền; truyền state update phiên bản/sequence; tránh gửi sự kiện stale/duplicate.
8. Nếu có thay đổi visibility sau manual review, lưu audit riêng và không cho AI tự viết trực tiếp Social DB.
9. Cung cấp seed tối thiểu 5 account demo và DB tạm bằng workflow an toàn, không hardcode secret hay dùng production accounts.

## 4. API, dữ liệu và hợp đồng tích hợp

API tham khảo (áp dụng route thực tế trong repo): `POST /posts`, `GET /posts`, `GET /posts/{id}`, `POST /posts/{id}/comments`, `GET /posts/{id}/comments`, `POST /posts/{id}/comments/{comment_id}/replies`. Dữ liệu tối thiểu: `post_id`, `comment_id`, `parent_id`, `author_user_id` server-derived, `text`, `revision`, `moderation_job_id/status`. Phản hồi lỗi 400/403/404/409 rõ ràng.

## 5. Kế hoạch kiểm thử

- Integration với DB tạm: post+reply hợp lệ; wrong-post parent bị từ chối; delete/hidden parent policy phù hợp; quá kích thước bị chặn.
- AI service down: comment POST thành công, job còn sau restart; worker retry và lưu result một lần.
- Client gửi lại cùng idempotency key: đúng một comment/job, response nhất quán.
- RBAC: user không đọc post riêng tư hoặc tạo comment bằng actor của người khác.
- Test race 2 requests trùng key, event phát sau commit, timestamp/order server, XSS payload có thể hiển thị an toàn.

## 6. Acceptance criteria / Definition of Done

- [ ] Hai session tạo post và bình luận/reply thực tế trong DB demo.
- [ ] API ACK không chờ AI inference; trạng thái job được lưu.
- [ ] AI offline + restart không mất comment hoặc moderation job.
- [ ] Retry/idempotency không nhân bản post/comment/job.
- [ ] Parent/reply graph, permissions và event authorization đều có test PASS.
- [ ] Không migrate/xóa database thật; không bật auto-hide.

## 7. Deliverables và bằng chứng

Code/API/migration safe, fixtures demo, logs integration/recovery, route docs, cập nhật `AUTO_PROGRESS.md`.



Shared safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md), Social Feed v2 section. The source journal was unstarted; actual execution follows below.

## T035 Social Feed v2 — IN_PROGRESS, 04/11/2026

Verify durable post/comment/reply and five authenticated demo accounts using disposable SQLite; reuse canonical transaction and worker.

Evidence: 

## T035 Social Feed v2 — DONE_VERIFIED, 04/11/2026

14 actual temporary-SQLite tests PASS, including five authenticated actors creating a post and comments/reply with one durable job each, publication privacy, same-key races, replay and RBAC. Demo seeds five normal accounts plus staff; canonical API reused.

Evidence: services/social-api/tests/test_live_api.py, reports/social_feed_v2_20261104/T035_backend.log
