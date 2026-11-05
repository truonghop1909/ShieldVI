# T041 — Training Studio: UI chọn dataset và huấn luyện ViSoBERT candidate

**Dự án:** ShieldVI · **Trạng thái ban đầu:** TODO / NOT STARTED (chỉ đổi theo evidence) · **Nhánh:** Realtime Moderation & Self-service ML Studio

**Mục tiêu:** Từ giao diện, chọn dataset đã gán nhãn và cấu hình training; thực sự khởi chạy worker backend, theo dõi progress/logs, lưu checkpoint candidate riêng, không đổi default.

**Phụ thuộc:** T039, T040 (PRELABELED có thể train trước T040 khi validator pass). Các task mới là phạm vi triển khai kỹ thuật; T028–T033 không tự đổi trạng thái khi chưa đủ formal acceptance.

## Công việc triển khai
1. Tab **Training** riêng cho trainer/admin: chọn một hoặc nhiều dataset versions `ACCEPTED`; chọn mode `synthetic-only`, `labeled-real-only` khi có quyền, `mixed` có tỷ lệ + báo cáo provenance; chọn task binary toxicity đầu tiên, các tác vụ target/repeated cần thiết kế/mô hình riêng.
2. Wizard cấu hình: base checkpoint (mặc định V1 read-only), head-only CPU hoặc full/partial fine-tune GPU nếu tài nguyên cho phép; epochs, LR, batch, max_length, class weights, seed, validation split, early stopping, max runtime/resource quota. Dùng preset an toàn + cảnh báo train-from-scratch/few examples.
3. Preflight: schema+rights+PII+split/leakage, nhãn binary hợp lệ, không train từ UNCERTAIN hoặc test/holdout, storage, dependency versions, GPU/CPU RAM estimate. Không chấp nhận file arbitrary Python/pickle.
4. Backend Job API tạo `training_run_id`, immutable config + dataset SHA + base model SHA; queue durable, isolated training process; `QUEUED/RUNNING/PAUSED?` (nếu thật sự hỗ trợ)/`CANCELLING/CANCELLED/FAILED/COMPLETED`, checkpoint resume chỉ khi validated.
5. Worker stream metrics mỗi epoch/step bằng SSE/WebSocket hoặc polling backoff: train/val loss, learning rate, duration, GPU/CPU memory, validation Macro-F1, Toxic P/R/F1, confusion matrix; log an toàn, lỗi/hết RAM có hướng dẫn.
6. Huấn luyện thật tối thiểu 1 smoke run head-only trên dataset synthetic nhỏ với giới hạn CPU; lưu `config.json`, tokenizer metadata, weights safetensors (nếu tương thích), threshold candidate config, hash, evaluation & environment manifest. Không báo success chỉ vì API trả 200.
7. Quản lý cạnh tranh: CPU/GPU training worker cách ly không cướp tài nguyên moderation realtime; tối thiểu giới hạn tài nguyên, ưu tiên latency moderation, có cancel; không tự train trong web request.
8. Sau train, hiển thị Training Run Detail: logs, progress, các epoch, artifact path, checksum, reproducible command, downloadable run manifest. Không tự sửa `MODEL_PATH`, model registry default hoặc V1.
9. Quyền trainer/admin, audit người start/cancel, CSRF/secure uploads, chống model artifact injection và config tampering.

## Nghiệm thu
- UI chọn PRELABELED dataset → validate → start run → nhận trạng thái realtime → completed sau thực sự có checkpoint + métrics + SHA. Smoke job CPU có log, model load/inference thật.
- Tải unlabeled dataset → annotation → approved dataset version → cùng workflow train (khi user đã hoàn tất gán nhãn).
- Train crash/cancel/restart có status trung thực; không động tới default model, không làm nghẽn realtime moderation ở test tải nhẹ.
- Không cho một dataset test/uncertain-only/without consent đi qua preflight; không tuyên bố đã train full encoder nếu chỉ head-only.

## Bằng chứng / đầu ra
- Training UI/API/worker, example run manifest, checkpoint test, concurrency/permissions logs, hướng dẫn chạy CPU/GPU.


## Implementation specification (repository audit 04/11/2026)

- **Status:** DONE_VERIFIED
- **Dependencies:** T039. FormalT028/T029 BLOCKED and T030–T033 PARTIAL remain independent.
- **Architecture context:** Social API FastAPI/SQLAlchemy schema0004, bearer sessions; posts/comments, durable worker and review/appeal already exist. Approved AI defaultV1.1 with threshold.41; v5 signal rules, legacy internal contract1.0.
- **Input:** authenticated requests and immutable synthetic fixtures; canonical model/dataset manifests when applicable.
- **Output:** implemented behavior below, versioned contract, test logs, source SHA, task evidence.
- **Backend/frontend/AI/database scope:** `scripts/ and services/social-api/`; reuse existing modules and original API. No live migration/default-model mutation.
- **Concrete design:** Real isolated CPU head-only smoke after dataset eligibility; max4CPUthreads/900s/cost0, distinct T041 run, not r07; safe config allowlist/cancel, no default promotion.
- **Contract/schema:** `/api/studio/training-runs`; pin schema/version, IDs, content_revision, decision_version and analysis provenance; fail closed on unknown version.
- **Acceptance:** all original Nghiệm thu criteria above plus existing tests pass, negative authorization/error paths verified. NOT_RUN is not PASS; no DONE_VERIFIED from docs alone.
- **Unit tests:** valid/malformed schema, limits, stale revision, duplicate IDs, unauthorized caller and absence of side effects.
- **Integration tests:** real temporary SQLite and existing services/worker, restart/retry/idempotency and transaction rollback. Actual inference/training tested separately when required.
- **E2E:** local browser when UI is in scope, independent contexts, no mocked API claimed as actual. For architecture-only T034, contract/sequence validation replaces browser testing.
- **Security/privacy:** bearer auth + server RBAC; membership/post visibility checked; no credentials in URL/log, no raw evidence to normal user; upload/config allowlists and no shell/eval of external input.
- **Errors/recovery:** bounded retry/backoff; truthful queued/failed/cancelled/stale states; explicit missing rights/model/data; preserve user input and idempotency key across retries.
- **Performance:** cap body1MiB/request, content8000chars, context50comments, event page100, no neural inference in send request. These are budgets/limits, not measured latency promises; record real timings.
- **Evidence:** [docs/ml_studio/TRAINING.md](../../docs/ml_studio/TRAINING.md); additional verified logs/outputs are listed below.
- **Definition of Done:** all task acceptance met with actual tests and retained evidence; otherwise PARTIAL/BLOCKED with exact missing criteria; update shared task order/progress.
- **Current risks/blockers:** Verified local evidence is recorded below; formal human-gold gates remain unmet. GPU/paid/external/private data/production not authorized. Training Studio CPU smoke authorized by current user only after accepted synthetic dataset/preflight. T041 also depends on T040 for unlabeled inputs.

Common safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md). Imported source preserved at workspace task-pack path; SHA/rename map in TASK_MERGE_REPORT.md.


### Execution evidence

Implementing durable isolated CPU head-only training, bounded config, dataset/model SHA preflight and cancellation; current user specifically authorizes one eligible synthetic smoke, not r07/default promotion.



### Execution evidence

7 backend tests PASS, 6 real Chrome checks PASS and build PASS. Actual retained synthetic-only V1 frozen-encoder CPU-head run:18threads/36comments, train22/validation10/test4,1epoch/3optimizersteps,2threads,trainer3.36s,reloaderror0.0,base/encoder/sources unchanged. Tiny synthetic validation Macro-F1=1.0 is workflow evidence only. Durable queued/running/cancel/crash/restart guards tested; no model/default/threshold/lock mutation. Training authorization for this smoke consumed; do not automatically rerun it during final regression.

- docs/ml_studio/TRAINING.md
- reports/task_rollout_20261104/T041_backend_service_final.log
- reports/task_rollout_20261104/T041_browser_result.json
- reports/task_rollout_20261104/T041_retained.json
- reports/task_rollout_20261104/T041_run_manifest.json


---

## Additional Social Feed v2 specification — 04/11/2026

Initial source status below is not an override of verified historical work. Current v2 acceptance is tracked separately.

# T041 — Training Studio: chạy huấn luyện ViSoBERT candidate thật từ giao diện

**Trạng thái ban đầu:** `NOT_STARTED — VERIFY_IN_REPOSITORY`  
**Độ ưu tiên:** `P1`  
**Phụ thuộc:** T039 approved labeled snapshot; T040 nếu nguồn chưa gán nhãn; model/training scripts hiện tại  
**Loại:** Thực thi code + kiểm thử + evidence; không chỉ thiết kế tài liệu.

## 1. Mục tiêu

Người dùng chọn dataset và checkpoint, tùy chỉnh hyperparameters rồi bấm **Start Training** để worker **huấn luyện thật** (head-only CPU smoke hoặc fine-tune có GPU phù hợp), xem log/progress, dừng job và lưu candidate riêng. Không dùng số liệu giả hoặc tự thay default.

## 2. Phạm vi

Research/admin UI, training job orchestration, isolated worker process, reproducibility/manifest, resource limits, checkpoint storage, audit/events.

## 3. Các bước thực hiện

1. Audit script đã có (r06 head-only CPU, Colab, registry). Nếu không có GPU, hỗ trợ CPU head-only training nhỏ và báo đúng `frozen encoder`.
2. Training UI: chọn dataset snapshot/version (quyền train đã được kiểm), label mapping và train/validation split; chọn base checkpoint; mode `head_only` hoặc `fine_tune` khi điều kiện cho phép.
3. Các fields: epochs, batch size, learning rate, max_length, seed, CPU/GPU, early stopping, class weighting; giá trị có giới hạn server-side, không thực thi arbitrary code/shell.
4. Snapshot dataset riêng có manifest/hash; chia theo thread và scenario-family, kiểm leakage, loại UNCERTAIN đúng chính sách, không dùng holdout hay ViCTSD test để train/tune.
5. Tạo run_id/job queue; worker/process riêng với quota CPU threads/memory/GPU, lock/concurrency; tránh làm Social API/AI moderation không phản hồi.
6. Start/Cancel/Status/Resume hoặc terminal failure: status `QUEUED/RUNNING/CANCELLING/CANCELLED/FAILED/SUCCEEDED`; stream log cursor/metrics versioned, đừng dùng fake progress.
7. Ghi config, seed, package versions, dataset manifest, model/tokenizer hash, optimizer, checkpoint SHA và stdout/stderr an toàn; checkpoint lưu immutable theo run_id, không ghi đè V1/r06/default.
8. Chạy smoke training nhỏ thật trên synthetic approved/no paid resources, đo thời gian CPU và loss/validation. Nếu không đủ tài nguyên, ghi `BLOCKED/NOT_RUN` và để job runnable, không báo DONE.
9. Kết quả candidate chỉ chuyển T042 evaluation, không tự promote hoặc đổi MODEL_PATH mặc định.

## 4. API, dữ liệu và hợp đồng tích hợp

API gợi ý: `POST /training/runs`, `GET /training/runs/{id}`, `GET /training/runs/{id}/logs?cursor=`, `POST /training/runs/{id}/cancel`, `GET /training/runs`; role researcher/admin. Run record phải lưu dataset hash, model base hash, config, source processor, status, started/ended times, metrics, artifact paths.

## 5. Kế hoạch kiểm thử

- Chạy một training smoke thật có checkpoint và log.
- Test invalid config, unauthorized, cancel, restart-safe job, dataset approval, isolation với Social API.

## 6. Acceptance criteria / Definition of Done

- API/UI job start thật, logs/progress đi từ worker thật, saved weights/checkpoint hash thay đổi theo training run.
- Cancel job giữa chừng không để orphan process/partial checkpoint trông như SUCCEEDED; restart hiển thị trạng thái chính xác.
- Reject unapproved dataset, holdout, missing labels, unauthorized user, hyperparameters vượt giới hạn và tùy ý shell path.
- Resource isolation: Social API/AI demo vẫn nhận comment khi trainer chạy, có latency evidence.
- Training report không gọi head-only là full fine-tune; synthetic metrics không thay T028.

## 7. Deliverables và bằng chứng

Training Studio UI/API/worker, ít nhất một CPU head-only smoke run thực (nếu khả thi), checkpoint candidate, logs và reproducibility manifest.



Shared safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md), Social Feed v2 section. The source journal was unstarted; actual execution follows below.

## T041 Social Feed v2 — IN_PROGRESS, 04/11/2026

Reverify retained actual head-only CPU smoke/candidate and concurrent Social ACK evidence; rerun lifecycle/resource/preflight guards without redundant training.

Evidence: 

## T041 Social Feed v2 — DONE_VERIFIED, 04/11/2026

7 guard/lifecycle tests PASS. Retained actual CPU frozen-encoder smoke/checkpoint/source SHA reverified (not rerun), including authenticated UI execution and47ms Social ACK during that actual training. Candidate remains experimental, threshold.41; no new training authorized/needed for existing receipt.

Evidence: reports/social_feed_v2_20261104/T041_backend.log, reports/social_feed_v2_20261104/T041_receipt_reverified.json, reports/task_rollout_20261104/T041_browser_result.json, reports/task_rollout_20261104/T041_concurrency.json


## Responsive UI follow-up — 05/11/2026

Live/Studio UI scope verified:144layout checks/12viewports and13responsive
workflows PASS;24existing browser checks PASS;builds/startup/transport PASS.
No training/API/model/reference change. Frozen legacy and real-device
coverage excluded. See docs/realtime_moderation/RESPONSIVE_UI_REPORT.md
and reports/responsive_20261105_verified.json. Historical status retained.
