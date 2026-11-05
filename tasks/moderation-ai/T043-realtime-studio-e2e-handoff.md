# T043 — End-to-end demo, benchmark, kiểm thử an toàn và bàn giao

**Dự án:** ShieldVI · **Trạng thái ban đầu:** TODO / NOT STARTED (chỉ đổi theo evidence) · **Nhánh:** Realtime Moderation & Self-service ML Studio

**Mục tiêu:** Một bộ demo Windows cho client realtime moderation + Data/Label/Training Studio, có thể diễn lại được, đo hiệu năng và ghi rõ các giới hạn.

**Phụ thuộc:** T035–T042 (cho scope fully DONE); phần độc lập thực hiện trước khi module khác xong. Các task mới là phạm vi triển khai kỹ thuật; T028–T033 không tự đổi trạng thái khi chưa đủ formal acceptance.

## Công việc triển khai
1. Tạo demo E2E bằng synthetic fixture riêng (không test real), môi trường local isolated DB/queue/AI worker/frontend + trainer worker, scripts setup/start/stop/cleanup Windows PowerShell.
2. Kịch bản A: client A đăng message CLEAN → A/B nhìn thấy tức thì → worker phân tích xong → status cập nhật không reload.
3. Kịch bản B: A/B tranh luận; actor U02 công kích U03 hai lần trong cùng thread → AI context nhận diện attack instances grounded → moderator được thông báo repeated với evidence đúng (không tự ẩn).
4. Kịch bản C: lời can ngăn, trích dẫn, xin lỗi, cảm thán tục không tạo evidence sai; test nhãn có thể mơ hồ và không ép model đúng tuyệt đối.
5. Kịch bản D: AI offline rồi recovery, retry, duplicate request, edit/delete, reconnect, concurrent messages; nội dung không mất, stale result không ghi đè.
6. Kịch bản E: trainer upload dataset gán nhãn sẵn → validate → train CPU head-only nhỏ → thấy progress/loss/Macro-F1 → checkpoint mới. Kịch bản F: import unlabeled → gán nhãn Round1/2 → xuất version → chọn training (không cần đợi training dài bằng dữ liệu thật).
7. E2E kiểm quyền user/moderator/trainer và privacy, quote/negation/PII/upload security, no accidental auto hide/train data. Training background không làm UI realtime đứng; benchmark P50/P95 publish ACK, enqueue, queue wait, inference, fanout cho số lượng concurrent user đã nêu, CPU specs.
8. Ghi freeze versions, test/coverage matrix, known limitations, screenshots/video artifacts nếu có, README cài và test trong Windows, báo cáo thật số PASS/FAIL/warnings; không đóng băng dependencies chưa đạt thành DONE.
9. Checklist demo hội đồng 5–7 phút + phương án offline nếu máy yếu; nếu live ViSoBERT CPU quá chậm, hiển thị PENDING và đợi kết quả thật, không phát nhãn giả.

## Nghiệm thu
- Có lệnh PowerShell chạy demo từ repo, không phải copy tay secrets hoặc sửa source; chạy được hai client + moderator + training UI trên local.
- E2E chứng minh message → live AI analysis thực sự qua worker; dataset upload → labeling → training backend thật và model artifact riêng; các luồng lỗi tái hiện được.
- Không ghi data live, không deploy, không đổi V1/default. Báo cáo giới hạn synthetic, T028/T029 formal BLOCKED trung thực.

## Bằng chứng / đầu ra
- `docs/ai-update/final-report/REALTIME_DEMO_GUIDE.md`, `scripts/demo_*.ps1`, screenshots, performance report, test report, final readiness checklist và ghi chú các task còn BLOCKED.


## Implementation specification (repository audit 04/11/2026)

- **Status:** DONE_VERIFIED
- **Dependencies:** T035, T036, T037, T038, T039, T040, T041, T042. FormalT028/T029 BLOCKED and T030–T033 PARTIAL remain independent.
- **Architecture context:** Social API FastAPI/SQLAlchemy schema0004, bearer sessions; posts/comments, durable worker and review/appeal already exist. Approved AI defaultV1.1 with threshold.41; v5 signal rules, legacy internal contract1.0.
- **Input:** authenticated requests and immutable synthetic fixtures; canonical model/dataset manifests when applicable.
- **Output:** implemented behavior below, versioned contract, test logs, source SHA, task evidence.
- **Backend/frontend/AI/database scope:** `scripts/ and docs/ai-update/final-report/`; reuse existing modules and original API. No live migration/default-model mutation.
- **Concrete design:** Disposable DB/accounts, real training/inference evidence separate from fixture tests; two-client/moderator E2E and measured timestamps, safe cleanup.
- **Contract/schema:** `local Windows demo runner`; pin schema/version, IDs, content_revision, decision_version and analysis provenance; fail closed on unknown version.
- **Acceptance:** all original Nghiệm thu criteria above plus existing tests pass, negative authorization/error paths verified. NOT_RUN is not PASS; no DONE_VERIFIED from docs alone.
- **Unit tests:** valid/malformed schema, limits, stale revision, duplicate IDs, unauthorized caller and absence of side effects.
- **Integration tests:** real temporary SQLite and existing services/worker, restart/retry/idempotency and transaction rollback. Actual inference/training tested separately when required.
- **E2E:** local browser when UI is in scope, independent contexts, no mocked API claimed as actual. For architecture-only T034, contract/sequence validation replaces browser testing.
- **Security/privacy:** bearer auth + server RBAC; membership/post visibility checked; no credentials in URL/log, no raw evidence to normal user; upload/config allowlists and no shell/eval of external input.
- **Errors/recovery:** bounded retry/backoff; truthful queued/failed/cancelled/stale states; explicit missing rights/model/data; preserve user input and idempotency key across retries.
- **Performance:** cap body1MiB/request, content8000chars, context50comments, event page100, no neural inference in send request. These are budgets/limits, not measured latency promises; record real timings.
- **Evidence:** [final report](../../docs/ai-update/final-report/T034_T043_FINAL_REPORT.md); actual verified logs and timings are listed below.
- **Definition of Done:** all task acceptance met with actual tests and retained evidence; otherwise PARTIAL/BLOCKED with exact missing criteria; update shared task order/progress.
- **Current risks/blockers:** Verified local evidence is recorded below; formal human-gold gates remain unmet. GPU/paid/external/private data/production not authorized. Training Studio CPU smoke authorized by current user only after accepted synthetic dataset/preflight. T041 also depends on T040 for unlabeled inputs.

Common safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md). Imported source preserved at workspace task-pack path; SHA/rename map in TASK_MERGE_REPORT.md.### Verified follow-up — schema startup diagnostics, 04/11/2026Database initialization now reports both schema stages, persistent logs and90second deadlines, with owned-process cleanup on interruption/timeout.7 startup tests PASS; actual4-context InteractiveCheck and stop script PASS;readiness1311PASS. Evidence: reports/task_rollout_20261104/DEMO_SCHEMA_FIX_tests.log,DEMO_SCHEMA_FIX_e2e.log, DEMO_SCHEMA_FIX_readiness.log andDEMO_SCHEMA_FIX_20261104.json. No training or task-status change.


### Execution evidence

Running broad regression, read-only readiness verification and real approved-default neural HTTP/browser workflow; preparing reproducible Windows demo/start-stop and final acceptance/evidence report.



### Execution evidence

Final737AI/root+244Social Python tests PASS/0FAIL (one deprecation warning per suite),4frontend transport tests PASS,original and opt-in builds PASS. Actual approved-default V1.1 neural HTTP/worker/SQLite E2E:8checks/3contexts PASS; four-context auto-login/Studio tabs/Windows stop script PASS. Enqueue SQL/ACK/queue/inference/fanout measured on4synthetic messages; tiny local sample, not SLO.1311 readiness files and13source-pack entries unchanged;27historical statuses preserved. Five canonical handoff guides/report complete. No extra training, promotion, deploy or production changes.

- docs/ai-update/final-report/T034_T043_FINAL_REPORT.md
- docs/ai-update/final-report/REALTIME_DEMO_GUIDE.md
- reports/task_rollout_20261104/T043_root_regression.log
- reports/task_rollout_20261104/T043_social_final.log
- reports/task_rollout_20261104/T043_transport_tests.log
- reports/task_rollout_20261104/T043_browser_result.json
- reports/task_rollout_20261104/T043_interactive_check.json
- reports/task_rollout_20261104/T043_performance.json
- reports/task_rollout_20261104/T043_readiness_final.log


### Demo startup follow-up (verified 04/11/2026)

Readiness now shows stages/timing/log paths with90second deadline and direct loopback HTTP. Ctrl+C is handled without traceback and cleans up owned processes.3startup tests PASS; actual4browser-context launch/Studio/stop PASS; injected operator interruption cleanup PASS. AI readiness21.5seconds in this check. See reports/task_rollout_20261104/DEMO_STARTUP_FIX_20261104.json and AUTO_PROGRESS. Prior DONE_VERIFIED status and protected model/lock remain unchanged.


---

## Additional Social Feed v2 specification — 04/11/2026

Initial source status below is not an override of verified historical work. Current v2 acceptance is tracked separately.

# T043 — End-to-end Windows demo: đăng bài–comment realtime + AI Studio

**Trạng thái ban đầu:** `NOT_STARTED — VERIFY_IN_REPOSITORY`  
**Độ ưu tiên:** `P0/P1`  
**Phụ thuộc:** T034–T042 trong phạm vi cần demo; blockers phải phân biệt rõ  
**Loại:** Thực thi code + kiểm thử + evidence; không chỉ thiết kế tài liệu.

## 1. Mục tiêu

Đóng gói demo đồ án **mạng xã hội có bài đăng**, tối thiểu 5 session account, moderation realtime, moderator review/appeal và chu trình Dataset→Annotation→Training→Evaluation; hướng dẫn chạy Windows và bằng chứng kiểm thử/độ trễ thực đo.

## 2. Phạm vi

Demo Windows scripts, DB synthetic isolated, accounts/credentials config, browser E2E, backend/frontend test/build, service start/stop, privacy cleanup và final acceptance.

## 3. Các bước thực hiện

1. Viết `WINDOWS_LOCAL_START_STOP.md` và scripts idempotent start/check/stop cho Social API, Moderation AI, worker, social-web, moderation-web, dataset/training services; không kill process ngoài dự án, tránh port conflicts.
2. Seed 5 account demo U01–U05 trong DB tạm (mỗi account auth/session riêng), 1 post có nội dung thảo luận, comment/reply do từng nick gửi thực sự.
3. Demo A: U01 đăng bài; U02 clean comment; B/C/D/E thấy comment không F5. Demo B: U03 toxic comment → job pending→done, Moderator nhận cảnh báo.
4. Demo C: U03 tiếp tục công kích cùng U01, repeated evidence chỉ nếu AI đủ context/target; không hardcode để pass. Demo D: U04 can ngăn, U03 xin lỗi, không tự tạo attack mới thiếu căn cứ.
5. Demo E: Moderator manual hide, tác giả appeal, moderator restore; audit đầy đủ và client cập nhật.
6. Demo F: stop AI → người dùng vẫn comment được, job retry/pending, restart AI → worker xử lý và push status; no lost/duplicate job.
7. Demo G: Dataset Center upload file synthetic labeled/unlabeled, validate, approve training snapshot; Annotation Studio Round1/Round2 từ người dùng; Training Studio chạy một CPU head-only nhỏ thật; Evaluation Registry xem metrics và candidate hash.
8. Performance benchmark: đo `comment_ack_ms`, `event_delivery_ms`, `queue_wait_ms`, `inference_ms`, `result_delivery_ms`, p50/p95 nếu đủ n, CPU/RAM/GPU/config; không giả số hoặc đặt SLA tùy tiện.
9. Chạy unit/integration E2E, frontend build, auth/RBAC security, leak prevention, cleanup. Ghi PASS/FAIL/NOT_RUN theo từng scenario và link evidence.
10. Viết hướng dẫn trình diễn cho hội đồng và FAQ: synthetic ≠ real gold, head-only vs full fine-tune, why realtime asynchronous, limitations model; không quảng cáo production-ready khi chưa được review.

## 4. API, dữ liệu và hợp đồng tích hợp

Demo scripts và kết quả T043 không được sửa default model/threshold, production DB, real evaluation cohort hoặc existing readiness lock. Phải ghi rõ là local synthetic demo. Browser E2E fixture AI khác actual model inference; cả hai cần được gắn nhãn nguồn đúng.

## 5. Kế hoạch kiểm thử

- Chạy E2E 5 nick, browser reconnect, AI offline/retry, manual review/appeal.
- Test import/annotation/train/evaluation thật và đo latency có số mẫu/hardware.

## 6. Acceptance criteria / Definition of Done

- 5 session riêng tương tác 1 post, nhiều comment/reply không F5; browser E2E có bằng chứng.
- AI comment flows, moderator alert/manual review/appeal/recovery chạy được và không mất job khi restart.
- Dataset Center import, Annotation Studio Round1/Round2 và ít nhất 1 training run thật + candidate/evaluation registry (nếu máy đủ tài nguyên).
- Backend tests, frontend builds, DB tmp, auth/RBAC, reconnect, resource safety checks.
- Latency có n/config/hardware và actual measurements; không viết số giả.
- Full demo có README, startup/cleanup, accounts và final checklist test outcomes thật.

## 7. Deliverables và bằng chứng

`docs/final/SOCIAL_FEED_REALTIME_DEMO.md`, `docs/final/DATASET_ANNOTATION_GUIDE.md`, `docs/final/TRAINING_STUDIO_GUIDE.md`, `docs/final/WINDOWS_LOCAL_START_STOP.md`, `docs/final/T034_T043_FINAL_ACCEPTANCE.md`, logs/screenshots, status update.



Shared safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md), Social Feed v2 section. The source journal was unstarted; actual execution follows below.

## T043 Social Feed v2 — IN_PROGRESS, 04/11/2026

Run full regression and final actual five-account Social Feed/Moderator E2E including owned AI stop/restart/retry. Prepare current demo/acceptance report and integrity checkpoint.

Evidence: 

## T043 Social Feed v2 — DONE_VERIFIED, 04/11/2026

Final744root/startup+247Social Python tests PASS,4transport tests PASS, both UI builds PASS. SSE scheduling RED→GREEN and full10-check7-context Social Feed/AI offline-recovery E2E PASS; original8-check3-context actual neural E2E PASS. All owned processes stopped;1311readiness files unchanged. Retained actual training/evaluation receipts reverified, not rerun. No production/default/training changes.

Evidence: docs/realtime_moderation/SOCIAL_FEED_V2_ACCEPTANCE.md, reports/social_feed_v2_20261104/root_regression_utf8.log, reports/social_feed_v2_20261104/social_regression_sse_final.log, reports/social_feed_v2_20261104/T043_sse_red.log, reports/social_feed_v2_20261104/T043_sse_green.log, reports/social_feed_v2_20261104/T043_feed_e2e_sse_fix.log, reports/social_feed_v2_20261104/T043_original_e2e.log


## T043 operator-selected demo password - 05/11/2026

Added -AskPassword: secure console prompt,12-128character validation, transient
SHIELDVI_DEMO_PASSWORD restored after exit. Default remains random. Applies to
new disposable demo accounts only; no plaintext credential file/log, existing
DB password reset, model/default/threshold or training change.13startup/password
tests PASS; actual7-context auto-login with supplied password and stop/cleanup
PASS. Readiness1311PASS, original lockSHA unchanged. No Git metadata.

Evidence: reports/demo_password_20261105_tests.log,
reports/demo_password_20261105_e2e.log,
reports/demo_password_20261105_readiness.log,
reports/demo_password_20261105_verified.json.
User clarified the earlier interrupt was not manually requested; sender remains
unknown. Proposed background mode was interrupted before any edits were applied;
that investigation is still OPEN. Do not claim -Background exists.


## Responsive UI follow-up — 05/11/2026

Live/Studio UI scope verified:144layout checks/12viewports and13responsive
workflows PASS;24existing browser checks PASS;builds/startup/transport PASS.
No training/API/model/reference change. Frozen legacy and real-device
coverage excluded. See docs/realtime_moderation/RESPONSIVE_UI_REPORT.md
and reports/responsive_20261105_verified.json. Historical status retained.


## Native Chrome visual follow-up — 05/11/2026

Fixed headed demo viewport override and fluid Live/Studio shells.70native-width/
mobile layout cases,10workflows,8existing actual-AI E2E cases PASS; builds/startup/
readiness PASS. Prior viewport-only acceptance did not cover native resizing.
See docs/realtime_moderation/RESPONSIVE_VISUAL_FIX_REPORT.md and
reports/visual_fix_20261105_verified.json. Historical task status preserved.
