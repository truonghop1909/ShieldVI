# T040 — Annotation Studio: tự gán nhãn theo hội thoại

**Dự án:** ShieldVI · **Trạng thái ban đầu:** TODO / NOT STARTED (chỉ đổi theo evidence) · **Nhánh:** Realtime Moderation & Self-service ML Studio

**Mục tiêu:** Cho phép người dùng tự đọc đầy đủ hội thoại, gán nhãn từng comment, target/repeated, rà soát Round1–Round2, và xuất dataset đủ điều kiện cho train.

**Phụ thuộc:** T039. Các task mới là phạm vi triển khai kỹ thuật; T028–T033 không tự đổi trạng thái khi chưa đủ formal acceptance.

## Công việc triển khai
1. Tạo tab **Labeling**: chọn dataset/version, tiến độ (% và số comment), filter chưa nhãn/mơ hồ/toxic/clean, bàn phím shortcuts, autosave có version và cảnh báo conflict.
2. Hiển thị nguyên thread với author pseudonyms, parent/reply, chronology, từng comment và bối cảnh xung quanh; không chỉ hiện một câu độc lập. Hover/click comment để chọn target và evidence.
3. Label `CLEAN`, `TOXIC`, `UNCERTAIN`, category, severity, `directed_at_user_id`, lời trích dẫn, can ngăn, tự vệ, apology, profanity non-directed, repeated yes/no cùng `evidence_comment_ids`; không đoán missing data.
4. Cho phép auto-suggest nhãn trong **chế độ hỗ trợ tách biệt** và ghi `ai_suggestion`/`model_version`, không trộn với human label; **blind mode mặc định** không thấy dự đoán khi gán benchmark T028.
5. Workflow một người: Round1 → Round2 sau khoảng cách phù hợp, cùng reviewer_id với revision check; sửa Round1 vô hiệu hóa xác nhận Round2 cũ; lưu lịch sử/justification/time, không giả độc lập hai annotators hoặc báo inter-annotator kappa.
6. Review task có trạng thái Draft/Submitted/Reviewed/Disputed/Locked; phân biệt nhãn synthetic và human; một người có thể có intra-review agreement nhưng không đại diện độc lập hai người.
7. Cho export version mới, thống kê per-label, remaining UNCERTAIN, completeness; build train set chỉ từ nhãn đã chọn/đủ điều kiện và không lẫn test lock. Snapshot immutability khi approved.
8. Kiểm RBAC, CSRF, XSS text content, concurrent edits, reconnect, audit history, privacy redactions.

## Nghiệm thu
- Nhập một unlabeled thread → Round1 từng comment → Round2 cùng reviewer_id → export CSV/JSONL, schema và history đúng; chưa Round2 không được đánh nhãn đã xác thực.
- Có thể xử lý UNCERTAIN mà không cưỡng ép binary; target/repeated có evidence hợp lệ; thay Round1 buộc Round2 review lại.
- Blind evaluation T028 không vô tình hiển thị AI score/nhãn đề xuất; synthetic không tự nâng cấp thành human gold.

## Bằng chứng / đầu ra
- Local labeling UI, test 2-round revision workflow, CSV/JSONL export sample + annotation schema, usability demo.


## Implementation specification (repository audit 04/11/2026)

- **Status:** DONE_VERIFIED
- **Dependencies:** T039. FormalT028/T029 BLOCKED and T030–T033 PARTIAL remain independent.
- **Architecture context:** Social API FastAPI/SQLAlchemy schema0004, bearer sessions; posts/comments, durable worker and review/appeal already exist. Approved AI defaultV1.1 with threshold.41; v5 signal rules, legacy internal contract1.0.
- **Input:** authenticated requests and immutable synthetic fixtures; canonical model/dataset manifests when applicable.
- **Output:** implemented behavior below, versioned contract, test logs, source SHA, task evidence.
- **Backend/frontend/AI/database scope:** `scripts/real_dataset/ and apps/moderation-web/`; reuse existing modules and original API. No live migration/default-model mutation.
- **Concrete design:** Reuse solo two-round revision workflow; blind mode, no fabricated human labels; separate AI suggestions.
- **Contract/schema:** `/api/studio/annotations`; pin schema/version, IDs, content_revision, decision_version and analysis provenance; fail closed on unknown version.
- **Acceptance:** all original Nghiệm thu criteria above plus existing tests pass, negative authorization/error paths verified. NOT_RUN is not PASS; no DONE_VERIFIED from docs alone.
- **Unit tests:** valid/malformed schema, limits, stale revision, duplicate IDs, unauthorized caller and absence of side effects.
- **Integration tests:** real temporary SQLite and existing services/worker, restart/retry/idempotency and transaction rollback. Actual inference/training tested separately when required.
- **E2E:** local browser when UI is in scope, independent contexts, no mocked API claimed as actual. For architecture-only T034, contract/sequence validation replaces browser testing.
- **Security/privacy:** bearer auth + server RBAC; membership/post visibility checked; no credentials in URL/log, no raw evidence to normal user; upload/config allowlists and no shell/eval of external input.
- **Errors/recovery:** bounded retry/backoff; truthful queued/failed/cancelled/stale states; explicit missing rights/model/data; preserve user input and idempotency key across retries.
- **Performance:** cap body1MiB/request, content8000chars, context50comments, event page100, no neural inference in send request. These are budgets/limits, not measured latency promises; record real timings.
- **Evidence:** [docs/ml_studio/ANNOTATION.md](../../docs/ml_studio/ANNOTATION.md); additional verified logs/outputs are listed below.
- **Definition of Done:** all task acceptance met with actual tests and retained evidence; otherwise PARTIAL/BLOCKED with exact missing criteria; update shared task order/progress.
- **Current risks/blockers:** Verified local evidence is recorded below; formal human-gold gates remain unmet. GPU/paid/external/private data/production not authorized. Training Studio CPU smoke authorized by current user only after accepted synthetic dataset/preflight. T041 also depends on T040 for unlabeled inputs.

Common safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md). Imported source preserved at workspace task-pack path; SHA/rename map in TASK_MERGE_REPORT.md.


### Execution evidence

Reusing solo ReviewStore for blind two-round annotation, CAS, same authenticated reviewer, stale-Round2 invalidation and immutable synthetic-reference exports.



### Execution evidence

20 related backend tests PASS; 6 Chrome annotation workflow checks PASS after fixing verified navigation race. Blind context, autosave CAS, same reviewer two rounds, stale R2 invalidation, append-only history and immutable child snapshots verified. Synthetic browser entries remain reference, not human gold. Real-review minimum gap300seconds and source quarantine remain enforced. Dedicated build PASS.

- docs/ml_studio/ANNOTATION.md
- reports/task_rollout_20261104/T040_backend_fixed.log
- reports/task_rollout_20261104/T040_browser_result.json
- reports/task_rollout_20261104/T040_build.log


---

## Additional Social Feed v2 specification — 04/11/2026

Initial source status below is not an override of verified historical work. Current v2 acceptance is tracked separately.

# T040 — Annotation Studio: tự gán nhãn hội thoại theo ngữ cảnh

**Trạng thái ban đầu:** `NOT_STARTED — VERIFY_IN_REPOSITORY`  
**Độ ưu tiên:** `P1`  
**Phụ thuộc:** T039 validated dataset hoặc T028 intake khi hợp lệ; auth/reviewer identity  
**Loại:** Thực thi code + kiểm thử + evidence; không chỉ thiết kế tài liệu.

## 1. Mục tiêu

Giao diện để **chính người dùng** mở từng hội thoại và gán nhãn từng comment theo ngữ cảnh (CLEAN, TOXIC, UNCERTAIN, target, category, repeated) với Round1–Round2, history và export; tuyệt đối không ngầm tạo human labels.

## 2. Phạm vi

Frontend annotation workspace, reviewer permissions, annotation revision data model, optimistic concurrency, audit log, export/versioning, blind mode cho evaluation.

## 3. Các bước thực hiện

1. Tận dụng review UI T028 (nếu có) thay vì nhân đôi. Một screen gồm danh sách thread, thread tree, comment đang chọn, parent chain, actor/time và gắn cờ cần rà soát.
2. Field: `label CLEAN/TOXIC/UNCERTAIN`, `category`, `severity` nếu schema có, `directed_at_user_id`, `is_directed_attack`, `is_repeated_attack`, `evidence_comment_ids`, `reason`; target không được điền từ reply recipient mặc định.
3. Lưu draft, next/prev, phím tắt, lọc missing/uncertain, progress; không tự lấy CLEAN khi bỏ trống.
4. Round 1 và Round 2 dùng cùng reviewer_id cho người làm đồ án một mình. Round 2 chỉ xác nhận đúng revision Round 1; sửa Round1 làm stale Round2, bắt buộc xem lại.
5. Lưu history lý do đổi, timestamps, reviewer, nhãn version và source dataset snapshot; export CSV/JSON theo thread, lock chỉ khi đủ điều kiện.
6. Chế độ `blind_evaluation` không hiện AI prediction hoặc candidate score; workspace AI-assisted review khác phải gắn rõ `machine_suggestion` và con người xác nhận, không đổi label source.
7. Bảo mật: reviewer không xem corpus ngoài quyền, autosave an toàn/retry, tránh mất nhãn khi nhiều tab, CSRF/Auth.
8. Đối với NOV10/Fresh10 đã xem và dùng phát triển, cho phép adjudication tham khảo nhưng không được gọi independent gold.

## 4. API, dữ liệu và hợp đồng tích hợp

Contract annotation record: `dataset_version, thread_id, comment_id, reviewer_id, round, revision, label, category, severity?, directed_at_user_id?, evidence_ids, rationale, created_at, updated_at`; historical original reference remains immutable.

## 5. Kế hoạch kiểm thử

- Chạy browser workflow với 2 vòng nhãn và export; kiểm invalid target/evidence.
- Chạy stale revision, auto-save/logout, blind mode không trả model prediction.

## 6. Acceptance criteria / Definition of Done

- Full browser flow Round1→Round2→export với corpus tạm; blank labels không bị mặc định CLEAN.
- Khi sửa Round1, Round2 cũ bị invalidated; stale submit báo conflict.
- `blind_evaluation`: AI prediction hoàn toàn ẩn từ UI/API payload cho người gán nhãn.
- History/undo/draft/reload giữ nhãn, actor–target/evidence refs valid; single reviewer không bị báo kappa hai người.
- Upload chưa duyệt không tự promote REAL/HUMAN_GOLD.

## 7. Deliverables và bằng chứng

Annotation Studio UI, history/API tests, solo review guide, export sample và screenshot evidence.



Shared safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md), Social Feed v2 section. The source journal was unstarted; actual execution follows below.

## T040 Social Feed v2 — IN_PROGRESS, 04/11/2026

Revalidate solo Round1/Round2, history, derived immutable snapshots and stale Round2 invalidation. Browser automation labels only synthetic test entries.

Evidence: 

## T040 Social Feed v2 — DONE_VERIFIED, 04/11/2026

6 annotation backend tests and6 actual Chrome tests PASS: full context, one authenticated reviewer, two rounds, autosave/history, immutable child snapshot and stale Round2 export rejection. Automated synthetic test annotations are not human gold.

Evidence: reports/social_feed_v2_20261104/T040_backend.log, reports\task_rollout_20261104\demo_6a5b68a80812e8d6\T040_browser_result.json


## Responsive UI follow-up — 05/11/2026

Live/Studio UI scope verified:144layout checks/12viewports and13responsive
workflows PASS;24existing browser checks PASS;builds/startup/transport PASS.
No training/API/model/reference change. Frozen legacy and real-device
coverage excluded. See docs/realtime_moderation/RESPONSIVE_UI_REPORT.md
and reports/responsive_20261105_verified.json. Historical status retained.
