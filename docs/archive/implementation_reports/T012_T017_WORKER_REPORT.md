# T011 → T012/T017 — Adapter, worker bền vững và Admin offline

Ngày: 30/10/2026 (Asia/Saigon). Người dùng đã xác nhận **làm T011 trước rồi T012/T017** khi phát hiện adapter chưa tồn tại. Phạm vi gồm backend adapter/worker và manual fallback tối thiểu, không dashboard/T013 hoặc auto-hold HIGH.

## Kết quả

T011 thêm authenticated `POST /api/v1/moderate/comment` trong `V3 root/app/`, giữ các route V3 cũ và version 0.3.0. Adapter dùng engine/predictor/lexicon thật với profile conservative, không sửa model/threshold. Service token env bắt buộc, rate limit per-process và một slot inference mới; payload 1MiB, tối đa 50 context nodes/64000 ký tự. Không bảo mật hồi tố route legacy bằng service token mới; legacy vẫn chỉ nên đặt trong môi trường trusted/private như trước.

Contract `schema_version=1.0` nay có user_id/timestamp/parent/mentions pseudonymous, source và bounded context với parent closure. Response echo content/revision/request, finite raw toxicity score, model/lexicon version, analyzed_at, lexical/target/repeated evidence, advisory action và limitations. Không làm tròn score trước quyết định ngưỡng; repeated chỉ cho actor hiện tại có current content trong evidence. Không có context/timestamps/parent thật thì không bịa repeated. Golden JSON schemas/examples và hai bản Python vendored byte-identical bảo đảm hai backend không import code của nhau.

T012/T017 thêm worker CLI riêng, HTTP client timeout/auth/size/schema/correlation/evidence validation; không import Torch/Transformers vào Social API. Claim có lease/token, retry/backoff/jitter/Retry-After, xử lý worker crash, owner mới chống stale worker. Không giữ transaction trong inference. Input snapshot trong Social DB giữ request_id/payload nhất quán qua restart, xóa text snapshot khi terminal hoặc content edit/delete. Điều này là at-least-once inference, không cam kết exactly-once GPU compute; visible outcome/result/audit được commit tối đa một lần mỗi job.

Policy code version `social-policy-shadow-0.2` thực thi thiết kế T016: LOW→PUBLISHED/NOT_REQUIRED, REVIEW→PUBLISHED_FLAGGED/QUEUED; AI error→UNKNOWN/PENDING_MODERATION và retry/manual. Không tạo rule HIGH, không auto-hold/ban/delete vì score/từ khóa; không nạp example draft thành enforce config. Model 0.41 chỉ là prediction threshold, không threshold ẩn bài. Risk/visibility/AI label vẫn tách biệt.

Apply guard kiểm tra claim token/lease/status, request ID, content revision, decision version, policy snapshot và content còn pending. Edit/delete/manual decision invalidate job, snapshot và lease cũ. Result/visibility/job completion/system audit cùng transaction. Context lấy metadata thật, có parent closure, không fabricate mentions hoặc dùng future comments; text context cắt 1000 ký tự/node và ghi incomplete limitation. Response metadata/evidence không được phép dẫn tới hide.

## Vận hành không cần Admin trực liên tục

- Worker tự publish LOW và flag REVIEW khi có response hợp lệ; không cần admin online cho hai nhánh này.
- Retry mặc định tối đa 3 attempts, delay 5s/30s + jitter, connect/read timeout 3s/60s, lease 180s. Lỗi network/timeout/429/5xx/schema/correlation có retry bounded; 4xx khác tới manual queue ngay. Hết attempts giữ content pending, không âm thầm approve.
- `python -m shieldvi_social.worker --stats` và staff-only `GET /api/v1/moderation/jobs`: counts, queue_size, retry_attempts, expired leases, oldest wait, model availability (outcome trong 5 phút) và failed IDs/error codes. Không trả raw body/snapshot/service token.
- `POST /api/v1/moderation/decisions`: moderator/admin approve/hide với reason và expected revision/decision version. Không cần GPU/AI; không restore author-deleted. Tăng version/audit và vô hiệu job cũ.
- `POST /api/v1/moderation/jobs/{job_id}/retry`: staff requeue failed job sau khi sửa lỗi, reason và version guard; chu kỳ mới dùng request_id mới, giữ total_attempts/retry_count, không publish trực tiếp.
- Chỉ backend vận hành tối thiểu; chưa có dashboard/appeal UI hoặc provisioning tài khoản staff thật. Tất cả staff account trong test là fixture DB tạm. Không cam kết SLA, không mở Internet.

## Migration và dữ liệu

`0003_worker` thêm lease/token/counters/snapshot/hash/error vào moderation_jobs; moderation_results theo job PK; system audit actor_type/actor_identifier và nullable actor_id để không mạo danh author. Nâng 0002→0003 đã kiểm tra giữ identities/sessions/content. Startup web/worker yêu cầu 0003; **DB demo đang có chưa được nâng**, người dùng cần backup/dừng process rồi chủ động upgrade theo README.

Không đổi checkpoint, threshold config, dataset/test split, notebook, static/dashboard legacy hoặc runtime Social Web. Có chỉnh README frontend để dẫn tới hướng dẫn worker. Downgrade 0003 bị từ chối nếu có system audit vì 0002 không biểu diễn được actor null; không xóa lịch sử để ép downgrade. Rollback vận hành: dừng worker, giữ pending/jobs, dùng manual review; rollback schema cần backup pre-worker đã được xác minh.

## Files

V3 root:

- Thêm `app/moderation_adapter.py`, `app/moderation_contract.py`, `app/.env.moderation.example`, `tests/test_moderation_adapter.py`; sửa `app/main.py` để include router/middleware và chỉ redact validation trên endpoint mới. Legacy validation handler vẫn giữ hành vi cũ.
- Social API thêm `src/shieldvi_social/{ai_client,moderation_contract,worker_context,worker,moderation_routes}.py`, `migrations/versions/0003_worker.py`, `tests/{test_worker,ai_fixture,run_worker_smoke}.py`.
- Sửa Social API `models.py`, `content_store.py`, `main.py`, `pyproject.toml`, `.env.example`, `README.md`; httpx trở thành runtime dependency, đã có trong lockfile. Cài editable package trong venv service để CLI chạy được; không đổi môi trường legacy.
- `docs/modules/social_web.md` thêm liên kết worker; không sửa UI source/config/dependencies/build.

Design root: cập nhật task T011/T012/T017, API contract, DB/architecture, changelog và report này. Thêm schemas JSON; cập nhật request/response examples từ draft chưa implement thành contract validate được; giữ moderation_policy.example.json draft/enforcement-disabled. Evidence trong `docs/baseline/T011/` và `docs/baseline/T012_T017/`.

## Kiểm chứng thật

Từ V3 root:

```powershell
& ./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
```

Từ Social API root:

```powershell
& ./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
& ./.venv/Scripts/python.exe -m pytest tests/test_worker.py -q -p no:cacheprovider
& ./.venv/Scripts/python.exe -m pip check
& ./.venv/Scripts/python.exe tests/run_worker_smoke.py
```

| Kiểm chứng | Kết quả thật | Evidence |
|---|---|---|
| V3 + adapter | **130 passed, 1 warning**, 1.57s | [legacy-pytest.txt](../../baseline/T012_T017/legacy-pytest.txt) |
| Social API full suite | **135 passed, 1 warning**, 34.78s | [social-pytest.txt](../../baseline/T012_T017/social-pytest.txt) |
| Worker subset sau bổ sung metric counters | **48 passed, 1 warning**, 14.33s | [worker-pytest.txt](../../baseline/T012_T017/worker-pytest.txt) |
| Cross-service contract/adapter | PASS trong suite; adapter/lexicon/engine thật với predictor stub | test_worker.py |
| Live HTTP + worker CLI | PASS: AI down→retry→recover; profanity flagged; manual approve lúc AI down, worker không overwrite | [live-http-smoke.txt](../../baseline/T012_T017/live-http-smoke.txt) |
| Chrome hồi quy | **9 passed**, 10.6s, SQLite/schema mới; UI không đổi | [browser-tests.txt](../../baseline/T012_T017/browser-regression/browser-tests.txt) |
| Dependency check | No broken requirements | [dependency-check.txt](../../baseline/T012_T017/dependency-check.txt) |
| Protected files | 67/68 file mốc T007 giữ nguyên; chỉ app/main.py sửa có chủ đích. UI chỉ README đổi | [integrity-check.json](../../baseline/T012_T017/integrity-check.json) |
| Source review | 61 source entries trong app/tests/service, không venv/data thật | [source-manifest.json](../../baseline/T012_T017/source-manifest.json) |

T011 còn có mốc test riêng 128 pass trước khi triển khai worker: [log](../../baseline/T011/legacy-pytest.txt). Các warning là Starlette/httpx TestClient deprecation và NO_COLOR/FORCE_COLOR trong môi trường browser.

Kiểm tra **read-only** default Social DB hiện có chỉ đọc alembic_version: `0002_content`. Không đọc nội dung/tài khoản và không chạy migration/worker trên DB này. Cần nâng lên 0003 trước khi restart bản server mới. Checkpoint/threshold/lexicon/engine/data/static legacy trong manifest đều giữ nguyên SHA-256; Git vẫn không có metadata để tạo diff.

Tests bao gồm fail-safe/FP/profanity/quote, timeout/network/401/403/422/429/5xx, NaN/string score/schema/correlation/oversize, fake evidence, real parent closure, idempotency/duplicate/concurrent claim, expired lease/max attempts/crash recovery, request snapshot restart, late success/error sau edit/delete/manual approve/hide, version/policy guard, failed requeue/RBAC/reason, result storage rollback và downgrade bảo vệ system audit. Test clock tăng thời gian để mô phỏng outage, không khẳng định đã đo sự cố thực 10 phút.

## Giới hạn

- **Chưa nạp/chạy checkpoint thật**, GPU/Colab hoặc đánh giá chất lượng model. Mọi score trong tests/smoke là stub được đánh dấu; runtime adapter dùng predictor thật, không có fallback score giả.
- PostgreSQL mới compile SQL offline; chưa thử server/row-lock contention/hiệu năng thực. SQLite phù hợp dev, transaction nhỏ vẫn có writer serialization.
- Browser regression dùng dev server/fixture public, không phải E2E AI/model thật. Frontend build không chạy lại vì UI source không thay đổi; baseline build T010 vẫn là mốc hiện hành.
- Service rate limiter AI per-process, không phải quota distributed; endpoint legacy cũ chưa được retrofit auth. Cần private network/TLS và rate policy trước public deployment.
- Payload snapshot chỉ Social DB và được clear khi terminal; results chứa lexical fragments nên retention/privacy/backups trước production vẫn cần quyết định T019.
- Không auto-migrate DB thật, không tạo staff account thật, không deploy/push, không bắt đầu T013/T018. Git metadata vẫn không có; review qua file lists/manifest thay Git diff.

Hướng dẫn chạy: [Social API/worker README](../../modules/social_api.md).
