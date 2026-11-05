# Changelog

## Siết kiểm thử evidence demo D (2026-10-30)
- `scripts/demo_social.py`: chỉ chấp nhận suspected repeated = true, evidence có ít nhất hai timestamp và cùng evidence đó có ít nhất hai comment ID khác nhau; thiếu/rỗng/trùng ID sẽ FAIL với lý do rõ ràng.
- `tests/test_demo_evidence.py`: 10 regression cases PASS bằng `.venv\Scripts\python.exe -m pytest tests/test_demo_evidence.py -q -p no:cacheprovider`. Chưa chạy lại smoke A–D với AI thật sau thay đổi này; kết quả smoke trước đây chưa kiểm tra comment IDs và không chứng minh điều kiện mới đạt.

## Hướng dẫn demo A–D tương tác (2026-10-30)
- Thêm `scripts/demo_social.py`: Social API/worker, hai UI và AI CPU thật trong một phiên, tài khoản/DB tạm; console có ai-off/ai-on/status/quit, không sửa model/threshold hoặc DB cũ.
- `--smoke` đã PASS đủ A–D bằng HTTP: clean publish, toxic flag, AI process stop/restart/retry, repeated actor-target evidence/priority và human hide/appeal/restore. Không dùng predictor giả; câu và tài khoản synthetic, không phải gold/quality evaluation.
- Hướng dẫn thao tác: `docs/guides/DEMO_ABCD.md`; evidence `docs/baseline/DEMO_ABCD/smoke.json`. Không đổi product service/UI, không mở task mới hoặc migrate dữ liệu thật.

## T015 — Canonical moderation-ai và research dashboard migration (2026-10-30)
- Sau fresh regression gate và yêu cầu T015: move AI vào `services/moderation-ai/app`, research React vào `apps/moderation-web/legacy-v3`, giữ Social dashboard tại app cha và root import/npm compatibility.
- Cố định model/review/summary paths theo repo root, giữ checkpoint/datasets/DB tại chỗ; cập nhật requirements/build/static, Windows launcher, scripts, Colab và tests. Không đổi thuật toán/threshold 0.41/HIGH-off hoặc Social DB schema.
- 143 legacy/migration + 177 Social API tests, 16 Chrome tests, ba frontend builds và legacy build wrapper pass. HTTP với cùng real CPU checkpoint trước/sau cho response/OpenAPI/static trùng; rollback snapshot đã rehearsal qua DB tạm.
- Snapshot 59 source/config/static files, protected 52 model/dataset/database hashes không đổi; DB demo 0002 chưa migrate. Colab/GPU/ZIP thực tế chưa kiểm chứng.
- Báo cáo, commands/evidence và rollback: `docs/archive/implementation_reports/T015_MIGRATION_REPORT.md`.

## T014/T019 — E2E, AI evaluation và privacy/security (2026-10-30)
- E2E 4 server + worker: auth/content, AI 503/admin offline, manual decision/appeal/restore/recovery; thêm outage AI process thật 600s và manual retry sau khi hết budget.
- Sửa SQLite lock cycle ở login/logout và dashboard metrics khi worker commit; redact unknown validation field names/internal model 5xx, reject NUL removal reason, hide SQL parameters. Thêm backup SQLite không overwrite/restore tự động.
- Inference CPU thật trên 1.000 ViCTSD test, checkpoint V1.1 hiện có, threshold 0.41: Macro-F1 0.7420, precision 0.5524, recall 0.5273, shadow review load 10.5%; synthetic 30 câu tách riêng. Người dùng xác nhận chưa có thread gold độc lập, không suy ra chất lượng HIGH/target/repeated; khuyến nghị auto-hold tắt.
- 177 Social API tests, 139 legacy tests, 16 Chrome tests và hai frontend build pass; backup subset 19 cases cuối pass. Không migrate DB demo/train/tune/deploy/T015.
- Báo cáo, metrics/evidence và hướng dẫn: `docs/archive/implementation_reports/T014_T019_VALIDATION_REPORT.md`, `docs/guides/RUN_LOCAL.md`.

## T013/T018 — Dashboard, decisions, reports, appeals và audit (2026-10-30)
- Thêm moderation-web riêng, queue ưu tiên/phân trang, full text/context, AI provenance, false-positive feedback, claim lease, offline decisions/retry và audit reader; role moderator/admin bắt buộc ở server.
- Social Web thêm danh sách nội dung của chính mình, trạng thái/lý do, appeal và report. Report không tự hide, appeal không tự restore; chống IDOR/hidden ancestor, stale revision/manual override và reviewer concurrency.
- Schema 0004_review chỉ migrate trên DB tạm; không sửa DB demo/AI/checkpoint/threshold, HIGH vẫn tắt. Demo riêng dùng tài khoản giả và SQLite tạm.
- 158 Social API tests, 130 V3/adapter tests, 6 Chrome review tests và 9 Chrome Social Web regression pass; hai frontend build pass. AI fixtures tổng hợp, không chứng minh inference thật/quality.
- Commands, files, evidence và giới hạn: `docs/archive/implementation_reports/T013_T018_ADMIN_REPORT.md`.

## T011 → T012/T017 — AI adapter và durable worker (2026-10-30)
- Sau khi người dùng xác nhận dependency, thêm service-auth internal AI adapter, validated versioned schemas/examples, giữ các API/checkpoint/threshold V3.
- Worker riêng: lease/claim ownership, bounded retry/crash recovery, exact request snapshot, stale revision/decision/policy guards, atomic result/visibility/system audit; LOW publish, REVIEW flag, lỗi pending/manual; không HIGH auto-hold.
- Thêm backend staff metrics/manual approve-hide/requeue failed để vận hành khi AI/Admin offline; chưa có dashboard/appeal hoặc staff provisioning thật.
- Schema 0003 chỉ migrate/test trên DB tạm, DB demo hiện có chưa upgrade. 135 Social API tests, 130 V3/adapter tests, 48 worker final-subset tests và 9 Chrome tests pass; HTTP down/recover/manual smoke dùng predictor stub, không claim inference thật.
- Chi tiết commands/files/evidence/limits: `docs/archive/implementation_reports/T012_T017_WORKER_REPORT.md`.

## T010 — Social Web (2026-10-30)
- Thêm React app độc lập `ShieldVI_V3_Hybrid_Review/apps/social-web`: auth, public feed, post/detail/comment/reply, author edit/delete, pending/error UX và responsive full text.
- Bearer memory-only, cancellation/expiry/logout guards, idempotent draft retry; chỉ gọi Social API, registration tắt mặc định, chưa có AI/publish workflow.
- Production build PASS, 9 ca Chrome PASS với Social API thật và dữ liệu giả trên DB tạm; screenshot desktop/mobile và integrity 68 legacy + 30 Social API file không đổi. Không deploy hoặc sửa backend/checkpoint.

## T009 — Post/comment/reply/feed (2026-10-30)
- Thêm content CRUD, reply same-post/depth bound, feed/list phân trang và ownership/ancestor visibility; nội dung mới luôn pending, chưa gọi AI/publish tự động.
- Alembic `0002_content`, transactional moderation jobs + audit; idempotent create, revision/decision guards, soft delete/admin hide có reason và content rate limit.
- 87 test Social API pass, 111 test V3 pass (mỗi suite 1 warning); migration/live HTTP smoke pass với DB/tài khoản giả tạm; 68 file legacy giữ nguyên hash.
- Cập nhật OpenAPI/contract/DB/README/task; chưa bắt đầu Social Web hoặc worker/moderation workflow.

## T008 — Social API auth/database (2026-10-30)
- Thêm service `ShieldVI_V3_Hybrid_Review/services/social-api` độc lập, FastAPI factory, env config và Alembic users/sessions/auth rate buckets.
- Argon2id, revocable opaque Bearer sessions, register mặc định tắt, login/me/logout, server-side RBAC, privacy redaction/CORS/body/rate limits; chưa tạo user thật.
- 47 test social pass, regression V3 111 pass (mỗi suite 1 warning TestClient); CLI migration/live health/OpenAPI smoke pass trên DB tạm; 68 file legacy giữ nguyên hash. PostgreSQL chỉ kiểm tra SQL offline.
- Cập nhật auth contract/OpenAPI/schema và hướng dẫn chạy; không làm T009 hoặc sửa runtime/checkpoint V3.

## T016 — Policy/state machine MVP (2026-10-30)
- Chốt thiết kế `social-policy-draft-0.2`, shadow HIGH chỉ flag/manual, UNKNOWN pending/retry; chưa tạo active config hoặc bật auto-hold.
- Thống nhất enum social, actor transitions, edit/delete/appeal, revision guards, ancestor visibility và kill switch/rollback; ghi các quyết định demo và gate validation còn mở.
- Thêm acceptance vectors và 17 test thiết kế/tín hiệu V3 với score giả; regression V3 111 passed, 1 warning; 68 file legacy giữ nguyên hash. Không tuyên bố real inference hoặc social integration đã chạy.
- Chi tiết file/lệnh/evidence/giới hạn tại `tasks/integration/T016-policy-design.md`.

## v1 — Bộ tài liệu thiết kế trước khi code (2026-10-29)
- Giữ tài liệu starter và task/skill cũ để tương thích.
- Thêm 12 file tài liệu có thứ tự: Scope, Architecture, Policy, State, User Flow, DB, API, Security, Tests, Roadmap, Decisions.
- Thêm task T016–T019 và skill `$shieldvi-moderation-policy`.
- Cập nhật ví dụ contract có `schema_version`, `content_revision`, `ai_label` và cảnh báo score minh họa.
- Thêm `moderation_policy.example.json` ở chế độ shadow (chưa bật auto-hide).
- Chưa chạy backend hoặc frontend mới vì gói chỉ có tài liệu, không sửa source code.
