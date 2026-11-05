# T038 — Moderator Live Board và luồng xử lý thủ công

## JSON export follow-up — 05/11/2026

Native Chrome export fix verified:7browser checks,5actual-model export checks,
startup13 and Moderator/Studio build PASS. UUID naming came from Playwright's
allowAndName, hidden by prior saveAs tests. User's15comment JSON recovered.
Fresh headed contexts use real filenames and retained downloads; shared helper
prevents overwrite. Current browser activation awaits a new context; full Studio
restart is blocked by9missing external original V1 files. Existing session kept,
no model/path/lock changes. See docs/realtime_moderation/DOWNLOAD_EXPORT_FIX.md
and reports/download_fix_20261105_verified.json. Historical task status retained.

**Dự án:** ShieldVI · **Trạng thái ban đầu:** TODO / NOT STARTED (chỉ đổi theo evidence) · **Nhánh:** Realtime Moderation & Self-service ML Studio

**Mục tiêu:** Moderator theo dõi cảnh báo theo thời gian thực, đọc toàn cảnh hội thoại và quyết định thủ công kèm bằng chứng, appeal và audit.

**Phụ thuộc:** T035, T036, T037. Các task mới là phạm vi triển khai kỹ thuật; T028–T033 không tự đổi trạng thái khi chưa đủ formal acceptance.

## Công việc triển khai
1. Thiết lập màn moderator realtime theo thread, mức rủi ro, thời gian, trạng thái AI và review. Khi có message mới, cập nhật comment, raw/advisory/policy/evidence theo quyền; tìm kiếm, filter, paginate.
2. Khung phân tích: actor→target với nguồn bằng chứng comment ID, timestamp, context tags, lexical cues và link nhảy đến comment. Phân biệt `reply_to_user_id` với `directed_at_user_id`.
3. Chức năng moderator manual hide/unhide, dismiss, request clarification, appeal review, restore; audit trail không thể sửa im lặng. AI không tự thực thi thay moderator.
4. RBAC server-side cho user/moderator/admin/trainer; không dựa frontend route hiding. Log hiển thị không chứa PII nếu không cần thiết.
5. Khi AI offline, board đánh dấu `analysis_pending`; không tạo giả `TOXIC`, không suy diễn lệnh hide.
6. Giữ contract với Social API hiện tại; E2E bao gồm 1 threaded harassment, moderator xử lý, user kháng nghị và phục hồi.

## Nghiệm thu
- Two-client + moderator E2E đi trọn vòng: gửi → AI advisory → moderator đọc evidence → manual action → audit/appeal → restore.
- Role không đủ quyền không gọi được admin action, không xem full moderation evidence; xử lý race/revision theo thiết kế.
- Dashboard cũ và API contracts vẫn PASS regression.

## Bằng chứng / đầu ra
- UI/permission test suite, event trace, moderation audit log, demo recording/script.


## Implementation specification (repository audit 04/11/2026)

- **Status:** DONE_VERIFIED
- **Dependencies:** T035, T036, T037. FormalT028/T029 BLOCKED and T030–T033 PARTIAL remain independent.
- **Architecture context:** Social API FastAPI/SQLAlchemy schema0004, bearer sessions; posts/comments, durable worker and review/appeal already exist. Approved AI defaultV1.1 with threshold.41; v5 signal rules, legacy internal contract1.0.
- **Input:** authenticated requests and immutable synthetic fixtures; canonical model/dataset manifests when applicable.
- **Output:** implemented behavior below, versioned contract, test logs, source SHA, task evidence.
- **Backend/frontend/AI/database scope:** `apps/moderation-web/`; reuse existing modules and original API. No live migration/default-model mutation.
- **Concrete design:** Reuse review/appeal RBAC and audit; staff-only evidence, manual visibility changes with reason/version.
- **Contract/schema:** `/api/live/moderator/events`; pin schema/version, IDs, content_revision, decision_version and analysis provenance; fail closed on unknown version.
- **Acceptance:** all original Nghiệm thu criteria above plus existing tests pass, negative authorization/error paths verified. NOT_RUN is not PASS; no DONE_VERIFIED from docs alone.
- **Unit tests:** valid/malformed schema, limits, stale revision, duplicate IDs, unauthorized caller and absence of side effects.
- **Integration tests:** real temporary SQLite and existing services/worker, restart/retry/idempotency and transaction rollback. Actual inference/training tested separately when required.
- **E2E:** local browser when UI is in scope, independent contexts, no mocked API claimed as actual. For architecture-only T034, contract/sequence validation replaces browser testing.
- **Security/privacy:** bearer auth + server RBAC; membership/post visibility checked; no credentials in URL/log, no raw evidence to normal user; upload/config allowlists and no shell/eval of external input.
- **Errors/recovery:** bounded retry/backoff; truthful queued/failed/cancelled/stale states; explicit missing rights/model/data; preserve user input and idempotency key across retries.
- **Performance:** cap body1MiB/request, content8000chars, context50comments, event page100, no neural inference in send request. These are budgets/limits, not measured latency promises; record real timings.
- **Evidence:** [docs/realtime_moderation/MODERATOR_LIVE.md](../../docs/realtime_moderation/MODERATOR_LIVE.md); additional verified logs/outputs are listed below.
- **Definition of Done:** all task acceptance met with actual tests and retained evidence; otherwise PARTIAL/BLOCKED with exact missing criteria; update shared task order/progress.
- **Current risks/blockers:** Verified local evidence is recorded below; formal human-gold gates remain unmet. GPU/paid/external/private data/production not authorized. Training Studio CPU smoke authorized by current user only after accepted synthetic dataset/preflight. T041 also depends on T040 for unlabeled inputs.

Common safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md). Imported source preserved at workspace task-pack path; SHA/rename map in TASK_MERGE_REPORT.md.


### Execution evidence

Reusing existing ReviewDetail, staff RBAC/manual audit/appeals; building isolated live moderator entrypoint.



### Execution evidence

33 related backend tests PASS; 8 Chrome E2E checks PASS in three authenticated contexts: same actor-target repeated evidence, preserved moderator draft, manual hide, author appeal, restore, audit and clarification. Source/rules/model defaults unchanged. Old dashboard retained. Dedicated build PASS. Search/thread/risk/time filters explicitly page-scoped; Studio trainer maps to existing admin, no role migration.

- docs/realtime_moderation/MODERATOR_LIVE.md
- reports/task_rollout_20261104/T038_browser_result.json
- reports/task_rollout_20261104/T038_backend_tests_fixed.log
- reports/task_rollout_20261104/T038_build_final.log


---

## Additional Social Feed v2 specification — 04/11/2026

Initial source status below is not an override of verified historical work. Current v2 acceptance is tracked separately.

# T038 — Moderator Dashboard realtime: nhận cảnh báo và duyệt bình luận

**Trạng thái ban đầu:** `NOT_STARTED — VERIFY_IN_REPOSITORY`  
**Độ ưu tiên:** `P0`  
**Phụ thuộc:** T035/T036; live UI T037; review/appeal/audit hiện có  
**Loại:** Thực thi code + kiểm thử + evidence; không chỉ thiết kế tài liệu.

## 1. Mục tiêu

Moderator thấy bình luận/rủi ro mới ngay khi worker hoàn thành, mở đúng bài đăng và chuỗi reply, xem bằng chứng target/repeated, quyết định thủ công, xử lý khiếu nại và lưu lịch sử.

## 2. Phạm vi

`apps/moderation-web`, Social API moderator endpoints, authorization/RBAC, moderation events, audit/appeal, deep links, no automatic enforcement.

## 3. Các bước thực hiện

1. Audit Moderator Dashboard hiện hành; giữ service/UI đã có, không nhân đôi.
2. Thêm live review queue lọc post, comment, risk, job state, actor, assessment, repeated suspicion; event-driven update.
3. Chọn một cảnh báo mở post detail, highlight comment và evidence IDs, hiển thị chain parent/reply, target confidence, raw toxicity vs assessment, model/rule version, policy band và visibility riêng.
4. Action: review/confirm, manual hide, manual restore với reason, permission, audit actor/time, optimistic concurrency, double-submit protection.
5. Appeal: người dùng có quyền gửi appeal cho comment của mình; Moderator xem, quyết định, restore nếu duyệt; lịch sử thao tác không mất.
6. Realtime event security: chỉ moderator theo role/session nhận evidence và review_requested; token hết hạn/reconnect phải reauthorize; log mask PII.
7. UI phân biệt AI job pending/failure/UNKNOWN với CLEAN; không tự xem auto-hide chỉ vì raw score.
8. Deep link đến đúng comment và fallback khi comment bị ẩn/xóa (có quyền moderator).

## 4. API, dữ liệu và hợp đồng tích hợp

Events `moderation.review_requested`, `moderation.decision.updated`; Social API là nguồn visibility/audit. Giữ model signal và policy fields theo contract v1/v2 đã khóa; không cho frontend tự set risk/score.

## 5. Kế hoạch kiểm thử

- Moderator E2E: U01 post, U03 comment toxic, worker xử lý, live queue cập nhật, open đúng evidence.
- Hide/restore manual và appeal, audit fields/identity/time reason đầy đủ.
- Unauthorized regular user gọi moderator endpoints/SSE => 403/401 và không nhận dữ liệu.
- Worker offline/UNKNOWN không bị tự động ẩn; event stale không ghi đè review.
- Browser tests nếu môi trường cho phép; capture security/role evidence.

## 6. Acceptance criteria / Definition of Done

- [ ] Live queue tự cập nhật không F5.
- [ ] Có deep-link chính xác post/comment/evidence.
- [ ] Manual hide/restore + appeal thực sự đổi DB demo, có audit.
- [ ] User thường không thấy công cụ hoặc event moderator.
- [ ] Không auto-hide/ban do prediction; có PASS/FAIL/NOT_RUN rõ ràng.

## 7. Deliverables và bằng chứng

Moderator UI, API integration tests, audit/evidence fixture, demo script và regression logs.



Shared safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md), Social Feed v2 section. The source journal was unstarted; actual execution follows below.

## T038 Social Feed v2 — IN_PROGRESS, 04/11/2026

Reusing verified moderator live review/appeal; add durable post/comment deep links and verify reauthentication, exact evidence and role checks.

Evidence: 

## T038 Social Feed v2 — DONE_VERIFIED, 04/11/2026

Added authenticated moderator deep links and exact comment context restoration after login.22 related backend tests PASS, Moderator build PASS, actual seven-context Chrome9checks PASS including five actors, repeated evidence, manual hide/appeal/restore, deep-link reauth, reconnect, XSS and >30comment thread. All owned demo processes stopped.

Evidence: reports/social_feed_v2_20261104/live_regression.log, reports/social_feed_v2_20261104/T038_build.log, reports/social_feed_v2_20261104/T038_feed_e2e.log, reports/task_rollout_20261104/demo_1a59f364c7adc9e5/social_feed_result.json


## T038 staff quick conversation JSON testing - 05/11/2026

Added Test AI bang JSON tab beside live queue in Admin: paste/import/sample,
background progress/cancel, per-comment raw score vs assessment/context/lexicon/
policy/reply/target, repeated evidence, and JSON download. Hidden live queue
keeps SSE/state; editor survives tab switches. New owner-private staff-only
transient jobs call existing LiveAIClient/default-v5 with unchanged model/0.41.
No frontend service key, core API rewrite, content/dataset/gold-label writes or
training. Input contract caps50comments/128KiB/64000text chars; parent/time/ID
validation, one running job,120second run budget,15second max AI read timeout,
4MiB results,16recent jobs/30minute memory retention. Offline => FAILED, never
fake CLEAN; cancellation cooperative. Shutdown signals active jobs to stop.

Validation:11new backend tests PASS, full265Social tests PASS/1existing warning,
5actual Chrome checks PASS, Admin build PASS, readiness1311PASS. Actual default
neural sample5comments: c02 clean reply/no instance, c03/c05 directed at U01,
c04 intervention/no instance, repeated U02-to-U01 evidence c03/c05. Manual test
controls are not human gold or independent evaluation. Actual test DB still
contains only starter1post/0comments/1job/1result; no quick-test content persisted.
Desktop screenshot inspected; mobile screenshot saved. Active user demo and
pointer retained; test processes stopped. No deploy, model/default/checkpoint
or threshold change. Restart demo required for new Python routes; normal launch
creates a new session while original demo data stays in its report directory.

Evidence: reports/demo_quick_json_20261105_backend.log,
reports/demo_quick_json_20261105_social_regression.log,
reports/demo_quick_json_20261105_browser.log,
reports/demo_quick_json_20261105_build.log,
reports/demo_quick_json_20261105_readiness.log,
reports/demo_quick_json_20261105_verified.json;
actual screenshots/export under reports/task_rollout_20261104/demo_122a69ae101a68d2/.
Resume: Admin live.html -> Test AI bang JSON -> Nap JSON mau -> Phan tich hoi thoai.


## Responsive UI follow-up — 05/11/2026

Live/Studio UI scope verified:144layout checks/12viewports and13responsive
workflows PASS;24existing browser checks PASS;builds/startup/transport PASS.
No training/API/model/reference change. Frozen legacy and real-device
coverage excluded. See docs/realtime_moderation/RESPONSIVE_UI_REPORT.md
and reports/responsive_20261105_verified.json. Historical status retained.
