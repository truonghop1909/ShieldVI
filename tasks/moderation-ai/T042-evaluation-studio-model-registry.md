# T042 — Evaluation Studio, model registry và shadow so sánh

**Dự án:** ShieldVI · **Trạng thái ban đầu:** TODO / NOT STARTED (chỉ đổi theo evidence) · **Nhánh:** Realtime Moderation & Self-service ML Studio

**Mục tiêu:** So sánh mô hình ứng viên với V1/r06 và các Context rule trên cùng tập đủ điều kiện, quản lý checkpoint có phiên bản, shadow/rollback an toàn.

**Phụ thuộc:** T041; T028 chỉ là dependency của **formal real-world acceptance**, không chặn experimental evaluation. Các task mới là phạm vi triển khai kỹ thuật; T028–T033 không tự đổi trạng thái khi chưa đủ formal acceptance.

## Công việc triển khai
1. Tab **Models & Evaluation** liệt kê base/default/candidates với immutable SHA, training run, dataset lineage, type (head-only/full FT), threshold, scope research/experimental/approved.
2. Evaluation wizard chọn dataset holdout có quyền + locked labels, model A/B; tách raw classifier (TP/FP/FN/TN, Macro-F1, Toxic P/R) và advisory Context/Target/Repeated (target precision/recall, event P/R, evidence emitted/completeness). Report UNCERTAIN/exclusions/counts; không dùng test set để tune.
3. Cho so sánh các evaluation configs trên cùng split/model/raw cache nếu phù hợp, ghi inference thật hay replay cache; tránh so sánh khác partition/recipe rồi kết luận nhân quả.
4. Registry workflow `CANDIDATE` → `EVALUATED_SYNTHETIC` → `REVIEW_REQUIRED` → `APPROVED` → `SHADOW` → `ACTIVE` chỉ khi đủ quality gates và có ủy quyền rõ; không tự chuyển trên synthetic metrics.
5. Local shadow A/B dùng 2 pipelines trên cùng input, chỉ một kết quả được Social API dùng; lưu differences + latency. Safe rollback về V1 cho operator được phép, không migrate live DB.
6. Định nghĩa signed/hashed registry manifest, artifact integrity, revert paths, privilege checks, configurable rollout flag default OFF. T028 human gold vẫn thiếu thì promotion formal BLOCKED.
7. Có bảng error audit cho từng comment và actor-target/event, xuất CSV/MD; thận trọng với mẫu nhỏ/dataset bias và privacy.

## Nghiệm thu
- Chạy candidate eval trên synthetic demo + report có tên tập/provenance, uncertainty, split and SHA. Không báo độc lập nếu đã dùng để sửa model.
- Shadow/rollback demo local PASS; unauthorized model promotion bị từ chối server-side; `default` vẫn giữ nguyên.
- Không thể train/tune bằng tập locked test qua UI; không sửa lock để hợp thức hóa metrics.

## Bằng chứng / đầu ra
- Registry UI, evaluation reports, diff/rollback logs, model governance checklist.


## Implementation specification (repository audit 04/11/2026)

- **Status:** DONE_VERIFIED
- **Dependencies:** T041. FormalT028/T029 BLOCKED and T030–T033 PARTIAL remain independent.
- **Architecture context:** Social API FastAPI/SQLAlchemy schema0004, bearer sessions; posts/comments, durable worker and review/appeal already exist. Approved AI defaultV1.1 with threshold.41; v5 signal rules, legacy internal contract1.0.
- **Input:** authenticated requests and immutable synthetic fixtures; canonical model/dataset manifests when applicable.
- **Output:** implemented behavior below, versioned contract, test logs, source SHA, task evidence.
- **Backend/frontend/AI/database scope:** `scripts/ and apps/moderation-web/`; reuse existing modules and original API. No live migration/default-model mutation.
- **Concrete design:** Reuse registry/rollback tooling; same-dataset paired metrics with SHA/scope, proposal only, no activation.
- **Contract/schema:** `/api/studio/models`; pin schema/version, IDs, content_revision, decision_version and analysis provenance; fail closed on unknown version.
- **Acceptance:** all original Nghiệm thu criteria above plus existing tests pass, negative authorization/error paths verified. NOT_RUN is not PASS; no DONE_VERIFIED from docs alone.
- **Unit tests:** valid/malformed schema, limits, stale revision, duplicate IDs, unauthorized caller and absence of side effects.
- **Integration tests:** real temporary SQLite and existing services/worker, restart/retry/idempotency and transaction rollback. Actual inference/training tested separately when required.
- **E2E:** local browser when UI is in scope, independent contexts, no mocked API claimed as actual. For architecture-only T034, contract/sequence validation replaces browser testing.
- **Security/privacy:** bearer auth + server RBAC; membership/post visibility checked; no credentials in URL/log, no raw evidence to normal user; upload/config allowlists and no shell/eval of external input.
- **Errors/recovery:** bounded retry/backoff; truthful queued/failed/cancelled/stale states; explicit missing rights/model/data; preserve user input and idempotency key across retries.
- **Performance:** cap body1MiB/request, content8000chars, context50comments, event page100, no neural inference in send request. These are budgets/limits, not measured latency promises; record real timings.
- **Evidence:** [docs/ml_studio/EVALUATION.md](../../docs/ml_studio/EVALUATION.md); additional verified logs/outputs are listed below.
- **Definition of Done:** all task acceptance met with actual tests and retained evidence; otherwise PARTIAL/BLOCKED with exact missing criteria; update shared task order/progress.
- **Current risks/blockers:** Verified local evidence is recorded below; formal human-gold gates remain unmet. GPU/paid/external/private data/production not authorized. Training Studio CPU smoke authorized by current user only after accepted synthetic dataset/preflight. T041 also depends on T040 for unlabeled inputs.

Common safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md). Imported source preserved at workspace task-pack path; SHA/rename map in TASK_MERGE_REPORT.md.


### Execution evidence

Preparing paired synthetic locked-holdout evaluation and hashed local registry/shadow/rollback without activation; reuse retained actual T041 candidate, no new training.



### Execution evidence

4 backend guard tests PASS,5 Chrome checks PASS and build PASS. Actual paired V1/r06/T041 inference on same4 locked synthetic holdout comments; raw/final confusion/P/R/F1 reported separately, error exports and hashes retained. Target/repeated/evidence reference denominators absent on this cohort: null, not invented. Actual fault-injected local shadow fallback to V1+neural probes PASS. Promotion denied server-side, v1_1 default unchanged; no training.

- docs/ml_studio/EVALUATION.md
- reports/task_rollout_20261104/T042_browser_result.json
- reports/task_rollout_20261104/T042_evaluation.json
- reports/task_rollout_20261104/T042_backend_tests.log
- reports/task_rollout_20261104/T042_build.log


---

## Additional Social Feed v2 specification — 04/11/2026

Initial source status below is not an override of verified historical work. Current v2 acceptance is tracked separately.

# T042 — Evaluation Studio và Model Registry cho các ứng viên AI

**Trạng thái ban đầu:** `NOT_STARTED — VERIFY_IN_REPOSITORY`  
**Độ ưu tiên:** `P1`  
**Phụ thuộc:** T041 candidate outputs; existing evaluation tools, dataset/rights gates của T039  
**Loại:** Thực thi code + kiểm thử + evidence; không chỉ thiết kế tài liệu.

## 1. Mục tiêu

Giao diện xem từng training run/checkpoint và **so sánh có kiểm soát** V1/r06/candidate trên cùng một tập đánh giá hợp lệ; tách classification, Context/Target, Repeated, evidence và dữ liệu synthetic/real. Không tự kích hoạt candidate.

## 2. Phạm vi

Model registry (immutable manifests), evaluation jobs, paired metrics, confusion and error explorer, shadow/local comparisons, RBAC/promotion proposals.

## 3. Các bước thực hiện

1. Quét registry có sẵn; đăng ký V1, r06, candidate mới với hash/lineage, config, source dataset, tokenizer, processor version và rights metadata. Không sửa weights đã khóa.
2. UI danh sách model/runs, status, linked training config, dataset version, files/hash, validation metrics và error logs.
3. Paired evaluation yêu cầu cùng frozen cohort/split + label definition + metric code cho mọi model; ngăn chọn test làm tuning.
4. Báo cáo `Accuracy`, `Macro-F1`, Toxic P/R/F1, confusion matrix TN/FP/FN/TP, số UNCERTAIN loại khỏi binary metric và abstention; error explorer theo comment/thread.
5. Đánh giá riêng target hit/precision/recall, repeated pair events TP/FP/FN, evidence correctness và completeness; không dùng prediction raw làm chứng minh target/repeated.
6. Hiển thị rõ provenance `SYNTHETIC_DEV`, `SYNTHETIC_CHALLENGE_ALREADY_VIEWED`, `HUMAN_REVIEWED`, `INDEPENDENT_REAL_LOCKED`. Không tự coi synthetic là independent real.
7. Shadow/local comparison không tác động default/visibility; rollback plan là tài liệu/proposal, deployment và promotion cần phê duyệt riêng.
8. Log/metrics không lấy bằng cách mock hay sao chép report cũ thiếu model/dataset hash; ghi NOT_RUN khi không chạy inference thực.
9. Chạy tests quyền đọc model artifacts và bảo vệ PII/data leak trong error explorer.

## 4. API, dữ liệu và hợp đồng tích hợp

Registry schema tối thiểu `model_id, checkpoint_sha256, base_model_id, processor_version, training_run_id, dataset_version, label_provenance, evaluation_cohort_sha256, metric_source, promoted=false`. Metrics mang cờ `raw_classifier` hay `final_advisory` và chú thích dataset.

## 5. Kế hoạch kiểm thử

- Paired evaluation trên frozen split; đối soát confusion matrix và UNCERTAIN.
- Kiểm registry authorization, model hash, shadow/no-promotion.

## 6. Acceptance criteria / Definition of Done

- UI liệt kê, mở chi tiết candidate có checkpoint và manifest hợp lệ.
- Chạy paired evaluation bằng cùng cohort; thay cohort phải cảnh báo không so sánh trực tiếp.
- Metrics đúng confusion matrix, UNCERTAIN xử lý minh bạch; raw vs final, target vs repeated tách riêng.
- Shadow mode kiểm tra không ghi default/DB social visibility; rollback proposal không tự deploy.
- Unauthorized user không được sửa registry hoặc tải model/dataset nhạy cảm.

## 7. Deliverables và bằng chứng

Evaluation Studio UI, model registry manifest, comparison report JSON/MD, tests và permission logs.



Shared safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md), Social Feed v2 section. The source journal was unstarted; actual execution follows below.

## T042 Social Feed v2 — IN_PROGRESS, 04/11/2026

Verify existing paired V1/r06/T041 evaluation hashes and recompute confusion/Macro-F1; rerun registry and no-promotion guards without training.

Evidence: 

## T042 Social Feed v2 — DONE_VERIFIED, 04/11/2026

4 registry/evaluation guards PASS. Historical actual paired inference on the same4 synthetic holdout comments reverified against registry/model/dataset SHA; confusion counts and Macro-F1 recalculated. Target/repeated reference denominators remain absent/null. No claim of new inference or real-world evaluation; default/no-promotion gates unchanged.

Evidence: reports/social_feed_v2_20261104/T042_backend.log, reports/social_feed_v2_20261104/T042_report_reverified.json, reports/task_rollout_20261104/T042_evaluation.json


## Responsive UI follow-up — 05/11/2026

Live/Studio UI scope verified:144layout checks/12viewports and13responsive
workflows PASS;24existing browser checks PASS;builds/startup/transport PASS.
No training/API/model/reference change. Frozen legacy and real-device
coverage excluded. See docs/realtime_moderation/RESPONSIVE_UI_REPORT.md
and reports/responsive_20261105_verified.json. Historical status retained.
