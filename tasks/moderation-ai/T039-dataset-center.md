# T039 — Dataset Center: upload, chuẩn hóa, phiên bản dữ liệu

**Dự án:** ShieldVI · **Trạng thái ban đầu:** TODO / NOT STARTED (chỉ đổi theo evidence) · **Nhánh:** Realtime Moderation & Self-service ML Studio

**Mục tiêu:** Tạo giao diện đưa dataset có nhãn sẵn hoặc chưa gán nhãn vào hệ thống để kiểm tra, xử lý, phân chia và quản lý nguồn trước khi huấn luyện.

**Phụ thuộc:** T034 (chỉ dùng chuẩn ID/threads); có thể làm song song T035–T038. Các task mới là phạm vi triển khai kỹ thuật; T028–T033 không tự đổi trạng thái khi chưa đủ formal acceptance.

## Công việc triển khai
1. Tạo tab **Datasets** trong admin/trainer UI; upload `CSV`, `JSONL`, `JSON`, tùy khả năng có `ZIP` chứa file dữ liệu. Cho phép chọn encoding UTF-8, xem preview 50–100 dòng, mapping cột (`text`, `label`, `thread_id`, `comment_id`, `parent_id`, `user_id`, `timestamp`, `target_user_id`, `category`, `severity`, `source`).
2. Chọn loại dataset `PRELABELED`, `UNLABELED`, `SYNTHETIC`, `HUMAN_REVIEWED`. Nguồn/giấy phép/consent/scope/use restrictions và liên hệ source receipt phải được nhập/kiểm chứng cho dữ liệu thật; không mặc định dataset upload là licensed.
3. Validator schema, parent graph/unique IDs, label vocabulary, timestamp, malformed rows, nonempty text, anonymization/PII warnings, exact & near duplicates, dataset overlap với test/challenge và old train. Báo lỗi từng dòng + cho tải report; không âm thầm bỏ lỗi.
4. ZIP chống path traversal/bomb, size/count quota, MIME/content kiểm tra server-side, virus scanning nếu hạ tầng có; không unpickle/execute uploaded code/model. File gốc lưu immutable+SHA256, import transaction trạng thái `PENDING_VALIDATION`→`ACCEPTED/REJECTED/QUARANTINED`.
5. Label mapping CLEAN=0, TOXIC=1, UNCERTAIN phải policy rõ ràng; cột target/repeated/category là nhãn phụ, không tự coi là classifier labels. Dataset mới chưa duyệt không được huấn luyện bằng default.
6. Data splits theo thread/group, tránh leakage, khóa holdout và chống training với development exclusions; hiển thị số thread, comments, label distribution, review ratio, duplicates, warnings.
7. Tạo Dataset Version: immutable snapshot, hash, parent version, schema, manifest, lineage, audit ai đã import/chỉnh/duyệt; lập report quality.
8. UI lọc/search/bulk select an toàn, xem chi tiết thread, export CSV/JSONL, không hiển thị text có PII công khai.

## Nghiệm thu
- Người dùng tải dataset đã gán nhãn và có thể preview, map columns, xem lỗi, tạo accepted version hợp lệ; tải dataset chưa nhãn và đưa vào Annotation Studio.
- Invalid labels, CSV injection, oversized ZIP, traversal, malformed JSON, duplicate IDs, source rights missing, leakage phải reject/quarantine có thông báo cụ thể.
- Cùng một file upload lại không tạo version trùng không kiểm soát; hash/source vẫn truy được.

## Bằng chứng / đầu ra
- Dataset UI, API docs, validation logs, demo fixture synthetic và privacy/security tests.


## Implementation specification (repository audit 04/11/2026)

- **Status:** DONE_VERIFIED
- **Dependencies:** T034. FormalT028/T029 BLOCKED and T030–T033 PARTIAL remain independent.
- **Architecture context:** Social API FastAPI/SQLAlchemy schema0004, bearer sessions; posts/comments, durable worker and review/appeal already exist. Approved AI defaultV1.1 with threshold.41; v5 signal rules, legacy internal contract1.0.
- **Input:** authenticated requests and immutable synthetic fixtures; canonical model/dataset manifests when applicable.
- **Output:** implemented behavior below, versioned contract, test logs, source SHA, task evidence.
- **Backend/frontend/AI/database scope:** `services/social-api/ and apps/moderation-web/`; reuse existing modules and original API. No live migration/default-model mutation.
- **Concrete design:** Bounded UTF8 CSV/JSON/JSONL import, mapping, immutable source SHA/version, rights quarantine, exclusion/leakage preflight.
- **Contract/schema:** `/api/studio/datasets`; pin schema/version, IDs, content_revision, decision_version and analysis provenance; fail closed on unknown version.
- **Acceptance:** all original Nghiệm thu criteria above plus existing tests pass, negative authorization/error paths verified. NOT_RUN is not PASS; no DONE_VERIFIED from docs alone.
- **Unit tests:** valid/malformed schema, limits, stale revision, duplicate IDs, unauthorized caller and absence of side effects.
- **Integration tests:** real temporary SQLite and existing services/worker, restart/retry/idempotency and transaction rollback. Actual inference/training tested separately when required.
- **E2E:** local browser when UI is in scope, independent contexts, no mocked API claimed as actual. For architecture-only T034, contract/sequence validation replaces browser testing.
- **Security/privacy:** bearer auth + server RBAC; membership/post visibility checked; no credentials in URL/log, no raw evidence to normal user; upload/config allowlists and no shell/eval of external input.
- **Errors/recovery:** bounded retry/backoff; truthful queued/failed/cancelled/stale states; explicit missing rights/model/data; preserve user input and idempotency key across retries.
- **Performance:** cap body1MiB/request, content8000chars, context50comments, event page100, no neural inference in send request. These are budgets/limits, not measured latency promises; record real timings.
- **Evidence:** [docs/ml_studio/DATASETS.md](../../docs/ml_studio/DATASETS.md); additional verified logs/outputs are listed below.
- **Definition of Done:** all task acceptance met with actual tests and retained evidence; otherwise PARTIAL/BLOCKED with exact missing criteria; update shared task order/progress.
- **Current risks/blockers:** Verified local evidence is recorded below; formal human-gold gates remain unmet. GPU/paid/external/private data/production not authorized. Training Studio CPU smoke authorized by current user only after accepted synthetic dataset/preflight. T041 also depends on T040 for unlabeled inputs.

Common safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md). Imported source preserved at workspace task-pack path; SHA/rename map in TASK_MERGE_REPORT.md.


### Execution evidence

Implementing bounded immutable imports, provenance quarantine, dataset versions and exact/near leakage checks, reusing real_dataset utilities and admin RBAC.



### Execution evidence

17 related backend tests PASS and 6 real Chrome Studio checks PASS; immutable UTF8 CSV/JSON/JSONL imports, mapping, preview/export, rights/PII/formula quarantine, pinned exact/near leakage audit, duplicate replay, explicit lineage and thread splits. Dedicated build PASS. ZIP unsupported and rejected; real source verification remains manual and quarantined; no human gold or training claimed.

- docs/ml_studio/DATASETS.md
- reports/task_rollout_20261104/T039_backend_final.log
- reports/task_rollout_20261104/T039_browser_result.json
- reports/task_rollout_20261104/T039_build.log


---

## Additional Social Feed v2 specification — 04/11/2026

Initial source status below is not an override of verified historical work. Current v2 acceptance is tracked separately.

# T039 — Dataset Center: upload, kiểm tra, nguồn gốc và phiên bản

**Trạng thái ban đầu:** `NOT_STARTED — VERIFY_IN_REPOSITORY`  
**Độ ưu tiên:** `P1`  
**Phụ thuộc:** Auth/admin UI và công cụ dataset hiện tại; có thể làm sau T038  
**Loại:** Thực thi code + kiểm thử + evidence; không chỉ thiết kế tài liệu.

## 1. Mục tiêu

Có giao diện để chọn và tải lên dataset CSV/JSON/JSONL với nhãn có sẵn hoặc chưa có nhãn; xem trước, mapping, kiểm tra quality/license/provenance, lưu version không thay đổi và chuyển sang Annotation/Training khi đủ điều kiện.

## 2. Phạm vi

Admin/researcher UI, upload API/worker, dataset manifest, quarantine, validator, dedup/leakage audits, permissions, export.

## 3. Các bước thực hiện

1. Khảo sát dataset scripts/review/tool T028 hiện có; không tạo data pipeline mới nếu có thể gọi lại validator.
2. Upload wizard: file type/size/row limits, preview, choose schema/mapping: `thread_id, comment_id, parent_id, user_id, timestamp, text, label`, optional category/severity/target/repeated/source/receipt.
3. Phân biệt: `SYNTHETIC`, `REAL`, `UNVERIFIED`; `LABELED`, `UNLABELED`, `PARTIALLY_LABELED`; `TRAIN_CANDIDATE`, `DEV`, `HOLDOUT`, `QUARANTINE`.
4. Validate JSON parse, encoding UTF-8, empty text/IDs, duplicate IDs, parent graph/cycles/cross-thread refs, timestamps missing/invalid, label vocabulary, uncertainty; không bịa timestamp/user IDs.
5. Kiểm exact/near duplicates và leakage giữa train/dev/test, scenario family/source-level splits; ghi lỗi, warnings, sample rows.
6. Lưu immutable snapshot và manifest có SHA256, uploader, type/source/license/receipt, validator version, schema, counts, lineage, privacy status.
7. Upload không đồng nghĩa nguồn đã hợp lệ hoặc `TRAIN_APPROVED`; dữ liệu chưa có quyền/PII đưa quarantine. Cho operator review bằng chứng trước khi promote.
8. Security: chống path traversal, zip bombs, formula injection CSV, XSS preview, quota, malicious MIME, không chạy code người tải lên. RBAC và audit.
9. Export snapshot đã phê duyệt và report quality; không tự thay đổi original ViCTSD test hay T028 locked splits.

## 4. API, dữ liệu và hợp đồng tích hợp

Upload statuses: `UPLOADED → VALIDATING → QUARANTINED/VALIDATED → REVIEWED → TRAIN_APPROVED` (state thực tế tùy repo); `HOLDOUT` luôn không được train. Manifest lưu `source_kind, label_source, rights_status, pii_status, split_role, sha256, validation_report`.

## 5. Kế hoạch kiểm thử

- Chạy import/preview trên cả 3 định dạng, có/không nhãn.
- Chạy malformed parent/IDs, oversized/malicious payload, duplicate, leakage, permission/quarantine, export checksum.

## 6. Acceptance criteria / Definition of Done

- Labeled CSV / unlabeled JSONL / conversation JSON nạp thành công; mapping, preview, counts chính xác.
- Upload hỏng: parent orphan/cycle, duplicate, invalid label, oversized file, path traversal bị chặn có error rõ.
- Quarantine hoạt động; không thể chọn holdout/test/unverified cho training bằng đường API/UI thông thường.
- Role kiểm soát upload/review/training approval; SHA/export round-trip giữ dữ liệu.
- Synthetic không hiển thị là REAL hoặc human gold.

## 7. Deliverables và bằng chứng

Dataset Center UI/API, manifest mẫu, validator logs, lỗi mẫu, tài liệu nhập dữ liệu.



Shared safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md), Social Feed v2 section. The source journal was unstarted; actual execution follows below.

## T039 Social Feed v2 — IN_PROGRESS, 04/11/2026

Revalidate existing immutable Dataset Center imports, rights/PII/leakage guards and actual browser upload/export without duplicating implementation.

Evidence: 

## T039 Social Feed v2 — DONE_VERIFIED, 04/11/2026

Reused existing Dataset Center;14 validator/API tests PASS and6 actual Chrome upload/mapping/preview/export/idempotency/rejection checks PASS on a fresh synthetic-only Studio. No source rights or human gold fabricated.

Evidence: reports/social_feed_v2_20261104/T039_backend.log, reports\task_rollout_20261104\demo_6a5b68a80812e8d6\T039_browser_result.json


## Responsive UI follow-up — 05/11/2026

Live/Studio UI scope verified:144layout checks/12viewports and13responsive
workflows PASS;24existing browser checks PASS;builds/startup/transport PASS.
No training/API/model/reference change. Frozen legacy and real-device
coverage excluded. See docs/realtime_moderation/RESPONSIVE_UI_REPORT.md
and reports/responsive_20261105_verified.json. Historical status retained.
