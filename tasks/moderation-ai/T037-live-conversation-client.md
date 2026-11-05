# T037 — Client UI: hội thoại realtime và trạng thái kiểm duyệt

**Dự án:** ShieldVI · **Trạng thái ban đầu:** TODO / NOT STARTED (chỉ đổi theo evidence) · **Nhánh:** Realtime Moderation & Self-service ML Studio

**Mục tiêu:** Người dùng thấy ngay tin nhắn đã gửi và trạng thái AI cập nhật trực tiếp; đúng thread, đúng revision, không chặn nhập tin.

**Phụ thuộc:** T034, T035, T036. Các task mới là phạm vi triển khai kỹ thuật; T028–T033 không tự đổi trạng thái khi chưa đủ formal acceptance.

## Công việc triển khai
1. Audit framework và màn hình social hiện có; thêm hoặc hoàn thiện Thread/Conversation view, giữ nguyên luồng bình luận gốc. Nếu chưa có chat UI, tạo route demo riêng có đăng nhập 2 tài khoản và một conversation dùng message persistence thực, không chỉ mock chat bằng dữ liệu tĩnh. Hiển thị parent/child hoặc chat theo trật tự hợp lý.
2. Optimistic UI: gửi comment -> render pending local -> reconcile server ID -> `QUEUED` -> `PROCESSING` -> `COMPLETED/FAILED`; phân biệt lưu tin thành công với AI phân tích thành công.
3. Kết nối SSE/WebSocket được chốt T034; subscribe theo conversation và auth. Nhận `analysis_revision`, ignore stale events; reconnect có last-event cursor + snapshot fallback.
4. Các nhãn/điểm AI hiển thị có chủ đích: user bình thường thấy trạng thái an toàn/trung tính (theo quyền), moderator mới thấy raw score/target/evidence/policy. Không công khai dữ liệu riêng của nạn nhân.
5. Có nút mở chi tiết phân tích hội thoại và lọc các lượt công kích cho tài khoản đủ quyền; không hiển thị “bị phạt/ẩn” nếu chỉ mới có advisory.
6. Trạng thái empty/error/AI offline/slow job; loading không quay vô hạn. Hỗ trợ tin dài, teencode, mobile viewport, bàn phím/scroll và accessibility.
7. Dùng E2E giả lập 2 client và một moderator trên một conversation, kiểm concurrent messages, reconnect, edit, delete, out-of-order push.

## Nghiệm thu
- Trên local, A gửi message: A và B thấy comment mới không cần F5; status phân tích cập nhật sau khi worker xong, không refresh; kết quả đúng message_id/thread_id.
- Offline AI vẫn gửi/hiển thị được, status `RETRYING/FAILED` trung thực, tự cập nhật sau recovery.
- Không có duplicate message, stale badge, leaked evidence hoặc UI crash khi response lỗi.

## Bằng chứng / đầu ra
- E2E browser screenshots/video tùy công cụ có sẵn, UI test, dev startup instructions và demo GIF/video nếu tự tạo được.


## Implementation specification (repository audit 04/11/2026)

- **Status:** DONE_VERIFIED
- **Dependencies:** T034, T035, T036. FormalT028/T029 BLOCKED and T030–T033 PARTIAL remain independent.
- **Architecture context:** Social API FastAPI/SQLAlchemy schema0004, bearer sessions; posts/comments, durable worker and review/appeal already exist. Approved AI defaultV1.1 with threshold.41; v5 signal rules, legacy internal contract1.0.
- **Input:** authenticated requests and immutable synthetic fixtures; canonical model/dataset manifests when applicable.
- **Output:** implemented behavior below, versioned contract, test logs, source SHA, task evidence.
- **Backend/frontend/AI/database scope:** `apps/social-web/`; reuse existing modules and original API. No live migration/default-model mutation.
- **Concrete design:** Fetch SSE with Authorization, cursor replay, reconnect backoff, dedupe revisions, pending send reconciliation; two browser contexts.
- **Contract/schema:** `/live.html`; pin schema/version, IDs, content_revision, decision_version and analysis provenance; fail closed on unknown version.
- **Acceptance:** all original Nghiệm thu criteria above plus existing tests pass, negative authorization/error paths verified. NOT_RUN is not PASS; no DONE_VERIFIED from docs alone.
- **Unit tests:** valid/malformed schema, limits, stale revision, duplicate IDs, unauthorized caller and absence of side effects.
- **Integration tests:** real temporary SQLite and existing services/worker, restart/retry/idempotency and transaction rollback. Actual inference/training tested separately when required.
- **E2E:** local browser when UI is in scope, independent contexts, no mocked API claimed as actual. For architecture-only T034, contract/sequence validation replaces browser testing.
- **Security/privacy:** bearer auth + server RBAC; membership/post visibility checked; no credentials in URL/log, no raw evidence to normal user; upload/config allowlists and no shell/eval of external input.
- **Errors/recovery:** bounded retry/backoff; truthful queued/failed/cancelled/stale states; explicit missing rights/model/data; preserve user input and idempotency key across retries.
- **Performance:** cap body1MiB/request, content8000chars, context50comments, event page100, no neural inference in send request. These are budgets/limits, not measured latency promises; record real timings.
- **Evidence:** [apps/social-web/src/live.jsx](../../apps/social-web/src/live.jsx); additional verified logs/outputs are listed below.
- **Definition of Done:** all task acceptance met with actual tests and retained evidence; otherwise PARTIAL/BLOCKED with exact missing criteria; update shared task order/progress.
- **Current risks/blockers:** Verified local evidence is recorded below; formal human-gold gates remain unmet. GPU/paid/external/private data/production not authorized. Training Studio CPU smoke authorized by current user only after accepted synthetic dataset/preflight. T041 also depends on T040 for unlabeled inputs.

Common safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md). Imported source preserved at workspace task-pack path; SHA/rename map in TASK_MERGE_REPORT.md.


### Execution evidence

Build additive live.html React entry in existing social-web using current auth/content APIs and authorized fetchSSE, original pages/build outputs untouched. Need two independent Chrome sessions and reconnect/offline/stale/privacy evidence.



### Execution evidence

12 real Chrome two-client workflow checks PASS with temporary SQLite, authenticated SSE, actual default-v5 rules and explicitly non-neural raw fixture. Includes offline reconnect regression fixed via snapshot retry, AI503 recovery, idempotent lost ACK, edit/delete, reload, XSS and RBAC. Dedicated production build PASS. Actual neural incremental timing is separately retained under T036.

- apps/social-web/src/live.jsx
- reports/task_rollout_20261104/T037_browser_result.json
- reports/task_rollout_20261104/T037_build_final.log
- reports/task_rollout_20261104/T037_cleanup.json


---

## Additional Social Feed v2 specification — 04/11/2026

Initial source status below is not an override of verified historical work. Current v2 acceptance is tracked separately.

# T037 — Giao diện bảng tin: đăng bài và nhiều nick bình luận realtime

**Trạng thái ban đầu:** `NOT_STARTED — VERIFY_IN_REPOSITORY`  
**Độ ưu tiên:** `P0`  
**Phụ thuộc:** T035 API; T034 event transport; T036 để hiển thị tiến độ AI  
**Loại:** Thực thi code + kiểm thử + evidence; không chỉ thiết kế tài liệu.

## 1. Mục tiêu

Tạo Social Feed có trải nghiệm mạng xã hội: nick A đăng bài, 4 nick khác comment/reply, các tab thấy cập nhật **không F5** và trạng thái AI sau khi worker xử lý. Không thay bằng giao diện chat giữa hai người.

## 2. Phạm vi

`apps/social-web` hoặc frontend hiện hành; feed/post detail/composer/comment tree/reply/status subscription/authorization UX; không tạo frontend framework song song.

## 3. Các bước thực hiện

1. Audit router/components hiện tại; thêm trang Bảng tin (feed), Form đăng bài, Post detail và comment thread view.
2. Hiện avatar hoặc initials, tên tài khoản, nội dung, created_at, comment count, phân trang/lazy load, loading/empty/error states.
3. UI bình luận: composer, reply action, hiển thị parent context, indent/thread tree hợp lý, nút xem thêm với comment dài, dùng CSS safe text rendering/XSS controls.
4. Dùng session/auth thực, cho U01 đăng bài và U02–U05 comment; browser profiles/incognito khác nhau, không giả user bằng dropdown trên client mà bỏ qua auth.
5. Sau POST hiện optimistic/pending state nhưng reconciled theo server ID; không duplicate khi event tới, reconnect/replay/resubscribe từ event cursor.
6. Hiển thị `Đang gửi`, `Đã đăng`, `Đang phân tích`, `Đã phân tích`, `Cần xem xét`, `AI tạm không khả dụng`, tránh rò chi tiết model/policy nội bộ cho user thường.
7. Realtime permissions: rời post hoặc logout => unsub; không nhận events riêng tư; handle 401, reconnect auth expiry.
8. Responsive desktop/mobile và accessibility keyboard; không phá UI hiện có.

## 4. API, dữ liệu và hợp đồng tích hợp

Giao diện dùng API T035 và `post.created`, `comment.created`, `comment.moderation.updated` của T034. Dữ liệu status client-safe có thể hạn chế chi tiết risk/evidence; moderator-only payload thuộc T038.

## 5. Kế hoạch kiểm thử

- Frontend build và unit/component tests thật.
- Browser E2E ≥ 2 sessions độc lập tạo post/comment/reply, màn còn lại tự cập nhật không reload.
- Session thứ ba không có quyền không nhận private post/comment.
- Reconnect/reload: không mất, không nhân đôi, thứ tự ổn, kết quả AI cập nhật sau ACK.
- Long thread 30–100 comments: UI đọc được, pagination/lazy load đúng, không bị che text.

## 6. Acceptance criteria / Definition of Done

- [ ] Tạo và xem được bài đăng trong Social Feed bằng tài khoản thật demo.
- [ ] Các nick khác comment/reply trong cùng post, đúng author và parent.
- [ ] Hai browser sessions nhận bình luận và trạng thái AI không F5.
- [ ] Reconnect/reload không duplicate/mất comment.
- [ ] Phân quyền UI/API, XSS và loading/error states được test.
- [ ] Có ảnh/chứng cứ browser E2E thật hoặc ghi rõ NOT_RUN.

## 7. Deliverables và bằng chứng

Code UI, hướng dẫn mở ≥5 nick demo, build/test logs, evidence hai cửa sổ trước/sau.



Shared safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md), Social Feed v2 section. The source journal was unstarted; actual execution follows below.

## T037 Social Feed v2 — IN_PROGRESS, 04/11/2026

Implement Social Feed entry, post cards/composer, automatic public-feed refresh, comment metadata and five-session browser verification.

Evidence: 

## T037 Social Feed v2 — DONE_VERIFIED, 04/11/2026

Social Feed/cards/post composer and serialized public-feed refresh implemented; reply context/metadata rendered, post retries reuse idempotency key. Build PASS. Actual seven-context Chrome check PASS: five authenticated users discover a new post, comment/reply, receive AI/repeated and manual review/appeal updates without reload/duplicates. Two failed attempts retained (initial send timeout; Windows Proactor accept WinError64 on retry); demo-only Selector loop passed.

Evidence: apps/social-web/src/live.jsx, reports/social_feed_v2_20261104/T037_build.log, reports/social_feed_v2_20261104/T037_feed_e2e.log, reports/social_feed_v2_20261104/T037_feed_e2e_retry1.log, reports/social_feed_v2_20261104/T037_feed_e2e_retry2.log, reports/task_rollout_20261104/demo_5a35dbbdda80d3dc/social_feed_result.json


## T037 comment composer discoverability - 05/11/2026

User opened the correct live URL but could not see a composer after selecting
Xem bai va binh luan. Read-only active-demo audit found published posts and no
comment POSTs. Browser RED reproduced textarea outside viewport (ratio0).
Live UI now scrolls selected detail into view and focuses the composer after
snapshot load, including reopening the same post. Explicit label/id avoids
nested textarea content changing the accessible label after typing. Background
updates neither steal focus nor clear draft text. No API permission/policy change.

Actual Chrome5checks PASS: viewport/focus, comment persistence+real approved
AI analysis, same-post refocus, draft/focus retention, mobile viewport. Initial
red and first follow-up failure retained; final unchanged expectations PASS.
Social build PASS;1311readiness PASS. Test DB/processes isolated and stopped;
user demo_4851e8216db58367/pointer retained, no default/model/train/production
changes or task-status overwrite. Reload the existing tab once; no demo restart
needed. Evidence: reports/demo_comment_ux_20261105_red.log,
demo_comment_ux_20261105_green.log, demo_comment_ux_20261105_green2.log,
demo_comment_ux_20261105_build_final.log, demo_comment_ux_20261105_readiness.log,
demo_comment_ux_20261105_verified.json; all under reports/.


## T037 clickable composer and short-screen layout - 05/11/2026

Screenshot showed the Vi?t b?nh lu?n heading mistaken for a button and the
actual textarea below the viewport. Red Chrome probe verified that no button
with that name existed. Replaced heading with a real type=button/focus action,
moved composer immediately below post and above comments/pagination, added
placeholder/styling, and replaced competing smooth scrolls with a single
instant composer focus path. Reply also focuses composer; no auto-submit or
API/model/policy change. Existing expectations retained and strengthened to
require full textarea and submit visibility on1060x480viewport.

Actual Chrome7checks PASS: real write button, short-screen full visibility,
composer before pagination, post selection/same-post focus, persisted comment
with approved neural worker, draft/no-focus-steal and mobile. Social build
PASS;1311readiness PASS. Active user demo_8d1daf6059b99b03 retained, no user DB
mutation or demo stop. Original task statuses unchanged. Evidence:
reports/demo_comment_button_20261105_red.log,
reports/demo_comment_button_20261105_green.log,
reports/demo_comment_button_20261105_build.log,
reports/demo_comment_button_20261105_readiness.log,
reports/demo_comment_button_20261105_verified.json.


## T037 compact feed visual polish - 05/11/2026

Polished only the opt-in Social feed: compact post cards, initial avatars,
author/time grouping, post-count badge, small icon action, selected-post badge
and aria-current, responsive spacing and pagination only when needed. Kept
pseudonymous author IDs, authorization, polling/SSE, comment workflow and
backend/model/policy unchanged. No new styling-only unit tests.

Existing7actual Chrome comment checks PASS after styling; desktop1366x900 and
mobile390x780 screenshots inspected. Social build PASS in a new output folder.
Test DB/processes isolated and cleaned; live user demo_8d1daf6059b99b03 retained.
No model/training/dataset/production change or task-status overwrite. Refresh
current browser tab to see updated styling. Evidence:
reports/demo_feed_style_20261105_browser.log,
reports/demo_feed_style_20261105_build.log,
reports/demo_feed_style_20261105_verified.json;
screenshots reports/task_rollout_20261104/demo_b0a88f0856199726/feed_desktop.png
and comment_ux.png in the same directory.


## Live usernames and structured reply tags - 05/11/2026

Added opt-in live_identity metadata/schema and authenticated /api/live/feed;
message ACKs and snapshots expose server-derived author_username plus readable
parent reply_to_user_id/username. Permissions filter content before resolving
handles; hidden parent identity remains null, client identity spoofing rejected.
Core V1 APIs/schemas, worker snapshot/hash logic, AI inputs/rules/model/threshold
and readiness lock untouched. No DB migration or rewriting historical text.

Social feed/post/comments display usernames, Reply shows an @username chip
and original parent excerpt; saved comments name the reply recipient. Chip is
presentation over parent_id, not text inserted into authored body, and is not
an attack verdict. Moderator context and actor-target evidence show names while
retaining canonical IDs. Plain typed handles without Reply create no parent link.

Validation:254Social tests PASS (26related included),15incremental AI tests
PASS,4actual Chrome control groups/3sessions PASS, both frontend builds PASS,
1311readiness files PASS. Actual default neural results: clean reply recipient
correct with no target/instance;2direct attacks Bob-to-Alice correctly grounded;
repeated pair/evidence correct and clean reply excluded. Synthetic controls,
not human-gold quality evaluation. Screenshots inspected for Social identity.

Active user demo_8d1daf6059b99b03 was preserved/read-only, never restarted.
Backend currently running uses old loaded routes: operator must stop/relaunch
demo to load names API. UI falls back on404 during that interval. A normal
relaunch creates a fresh demo DB/accounts; old session data/logs stay in their
original report directory, not reset/deleted. No training/default/production
change or task-status overwrite. Evidence: reports/demo_identity_20261105_*.log,
reports/demo_identity_20261105_ai_verified.json,
reports/demo_identity_20261105_verified.json and demo_531e30a5c4f2f43f/ actual
browser/AI evidence under reports/task_rollout_20261104/.


## Responsive UI follow-up — 05/11/2026

Live/Studio UI scope verified:144layout checks/12viewports and13responsive
workflows PASS;24existing browser checks PASS;builds/startup/transport PASS.
No training/API/model/reference change. Frozen legacy and real-device
coverage excluded. See docs/realtime_moderation/RESPONSIVE_UI_REPORT.md
and reports/responsive_20261105_verified.json. Historical status retained.
