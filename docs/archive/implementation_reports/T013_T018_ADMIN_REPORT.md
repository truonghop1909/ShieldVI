# T013/T018 — Admin queue, decision, appeal và audit

Ngày 30/10/2026 (Asia/Saigon). **DONE cho demo local/private**, dựa trên Social API thật và DB tạm. Không triển khai T014/T019/T015, không chạy migration trên DB demo hiện có, không thay checkpoint/threshold 0.41 hoặc bật HIGH auto-hold.

## Kết quả

- Thêm React dashboard riêng ở `ShieldVI_V3_Hybrid_Review/apps/moderation-web`, mặc định cổng 5174. Tabs Cần xem xét/Reports/Appeals/Failed/Tất cả, lọc post/comment và phân trang. Queue ưu tiên held → failed pending → pending → appeal → repeated candidate → thường, rồi tuổi chờ/report count/ID; priority không phải verdict.
- Detail full text và parent context chỉ staff; hiển thị riêng AI label/score, policy risk, visibility, review, model/lexicon/threshold/analyzed_at/target/repeated evidence/limitations và job failure. Thiếu AI hiển thị thiếu dữ liệu, vẫn duyệt thủ công được.
- Approve/hide/restore, resolve appeal, claim 5 phút và retry failed yêu cầu reason + revision/decision version. Hai reviewer cùng version chỉ một thành công; claim của người khác còn hiệu lực trả 409. Nhận duyệt vô hiệu AI job đang chạy; kết quả cũ không ghi đè quyết định người duyệt.
- Social Web có `/my-moderation`: bài/bình luận chính mình, trạng thái/lý do, appeal và kết quả. Report form chỉ trên nội dung public người khác. Author không nhận reporter/reviewer identity hoặc body ancestor bị giữ/ẩn của người khác.
- Report dedupe theo reporter/content/revision, không tự hide/risk/HIGH. Appeal chỉ author trên hidden/held, một OPEN/revision, không tự restore. Resolve RESTORED→PUBLISHED hoặc UPHELD→HIDDEN, review RESOLVED. Appeal mở không bypass bằng manual restore/admin DELETE. Author edit đóng SUPERSEDED; author delete đóng AUTHOR_DELETED, terminal không restore.
- Audit read-only staff, phân trang, actor/type/role/time/reason/revision/decision/before-after/policy. Manual decision thêm model/lexicon/job/request nếu có, appeal/outcome hoặc false_positive feedback; AI offline null. Feedback chưa phải nhãn gold, không training.
- Bearer memory-only, cancellation/expiry/logout, 409 giữ bản thảo, không service key trong browser, không raw HTML/export API. Legacy dashboard và frontend không bị sửa.

## Schema và boundary

Social API sở hữu toàn bộ DB/auth/queue/report/appeal/visibility/audit. Moderation AI chỉ trả advisory schema 1.0 như T011; không import AI vào Social API, không ghi Social DB từ AI hoặc gọi ngược AI từ browser.

`0004_review` sau `0003_worker` thêm `content_reports`, `appeals`, `review_claims` và `content_audit.details_json`. API/worker startup kiểm tra đúng 0004, không auto migrate. SQLite mutation giữ BEGIN IMMEDIATE; PostgreSQL dùng thứ tự khóa content post→comment→appeal. Downgrade từ chối trước khi drop nếu có review history, không tự xóa appeal/report/audit. Trạng thái reviewer lease hết hạn được tính khi đọc queue/detail/author status, chưa có background sweeper đổi cột vật lý. Job AI đã vô hiệu khi claim không tự re-run sau expiry; nội dung tiếp tục ở manual queue.

[Contract endpoint/response/guard](../../architecture/API_CONTRACT.md), [database](../../architecture/DATABASE.md), [OpenAPI sinh từ server thật](../../../contracts/social-review.openapi.json).

## File thay đổi

Tất cả đường dẫn code dưới đây tính từ `ShieldVI_V3_Hybrid_Review/`:

| Nhóm | File |
|---|---|
| Backend sửa | `services/social-api/src/shieldvi_social/{models,content_store,moderation_routes,main,worker}.py`, `docs/modules/social_api.md` |
| Backend thêm | `services/social-api/src/shieldvi_social/{review_store,review_routes}.py`, `services/social-api/migrations/versions/0004_review.py`, `services/social-api/tests/test_review.py` |
| Social Web sửa/thêm | `apps/social-web/src/{App,components}.jsx`, `{api,utils}.js`, `styles.css`, `MyModeration.jsx`, `docs/modules/social_web.md` |
| Dashboard mới | `apps/moderation-web/{package.json,package-lock.json,vite.config.js,index.html,.env.example,.gitignore,README.md,playwright.config.js}`, `src/{main,App,ReviewDetail}.jsx`, `src/{api.js,styles.css}`, `tests/{review.spec.js,seed_demo.py,run_browser.py}` |
| Design | `docs/{API_CONTRACT,DATABASE,ARCHITECTURE,T013_T018_ADMIN_REPORT}.md`, `docs/CHANGELOG.md`, tasks T013/T018, `contracts/social-review.openapi.json`, `docs/baseline/T013_T018/` |

Không có Git metadata ở hai root nên `git status --short` trả “not a git repository”; không tạo Git. [Manifest source](../../baseline/T013_T018/source-manifest.json) và [integrity](../../baseline/T013_T018/integrity-check.json) hỗ trợ review. So với T012/T017, chỉ 6 file có sẵn trong manifest thay đổi, đều thuộc Social API; không file legacy nào đổi trong chặng này. So với T007, 68 file được kiểm tra, chỉ `app/main.py` khác do adapter T011 đã được ghi nhận trước; checkpoint `model.safetensors`, threshold config, lexicon, static build và các file gốc còn lại giữ hash.

## Bằng chứng kiểm thử

| Lệnh / phạm vi | Kết quả thực |
|---|---|
| V3 root: `services/social-api/.venv/Scripts/python.exe -m pytest services/social-api/tests -q -p no:cacheprovider` | **158 passed, 1 warning**, 48.33s; [log](../../baseline/T013_T018/social-pytest.txt) |
| Backend subset `python -m pytest tests/test_review.py -q -p no:cacheprovider` | **23 passed, 1 warning**, 13.04s; nằm trong suite 158, không cộng trùng |
| V3 root, `STORE_SUMMARIES=0`, legacy `.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider` | **130 passed, 1 warning**, 2.46s; [log](../../baseline/T013_T018/legacy-pytest.txt) |
| V3 root: Social venv Python `apps/moderation-web/tests/run_browser.py` | **6 Chrome tests passed**, 11.7s; Social API + hai Vite app thật, SQLite tạm; [log](../../baseline/T013_T018/browser-tests.txt) |
| T010 browser runner, override artifacts sang `T013_T018/social-regression` | **9 Chrome tests passed**, 11.9s; auth/feed/post/comment/reply/edit/delete/expiry/retry/XSS regression; [log](../../baseline/T013_T018/social-regression/browser-tests.txt) |
| `npm run build` ở cả moderation-web và social-web | **PASS**, exit 0; [kết quả ghi từ tool output](../../baseline/T013_T018/frontend-builds.txt) |
| Moderation dependencies | `npm ci --offline --no-audit --no-fund`, 70 packages, exit 0; dùng cache/lock đã có, không thêm dependency AI |
| Integrity script, read-only schema | **PASS**; DB demo mặc định vẫn **0002_content**, chỉ SELECT `alembic_version`, không đọc account/body hoặc migrate |

23 backend cases gồm RBAC/IDOR, held/feed counts, ancestor context/restore, report dedupe/private reason, appeal author-only/resolve/concurrent reviewers, lease expiry nguồn QUEUED/APPEALED, stale AI finish, revision edit/delete, terminal tombstone, audit/provenance/feedback, invalid reason, ordering/pagination và downgrade giữ lịch sử. Migration suite có metadata match, giữ users/sessions, empty upgrade/downgrade và PostgreSQL offline SQL compilation.

6 review browser cases kiểm tra comment → manual hide → author appeal → restore → re-login audit, provenance/XSS text/mobile 320/390, offline manual + 409 giữ draft, report → Reports tab không auto-hide, non-staff/401/memory storage và lỗi queue/logout recoverable. [Ảnh desktop](../../baseline/T013_T018/browser/desktop-dashboard.png), [mobile detail](../../baseline/T013_T018/browser/mobile-detail.png) đã kiểm tra trực quan; assertions không có horizontal overflow. Hai bộ browser dùng tài khoản và mật khẩu ngẫu nhiên trong DB tạm, runner dừng đúng process tree do nó tạo.

Warning pytest là Starlette/httpx deprecation hiện có; browser cảnh báo NO_COLOR/FORCE_COLOR. Hai lỗi ban đầu là selector test và Python stdout encoding; đã sửa, chạy lại thành công. Test reason surrogate ban đầu bị httpx chặn ngay tại client; đã gửi escaped JSON để test tới server và toàn suite pass. Không diễn giải các lần lỗi ban đầu thành pass.

## Demo và giới hạn

[Hướng dẫn từng bước](../../modules/moderation_web.md). Lệnh từ V3 root:

```powershell
.\services\social-api\.venv\Scripts\python.exe apps/moderation-web/tests/run_browser.py --demo
```

Tạo DB tạm, migrate riêng, chạy hai UI/API trên cổng trống, in URL và mật khẩu tạm cho `fixture_author/viewer/mod/admin`. Ctrl+C dọn. Không cấp staff hoặc đổi DB demo hiện có. Bộ tự động đã chạy cùng ba server và fixture setup; chế độ giữ terminal `--demo` chưa thao tác tương tác bằng tay trong chặng này.

Real checkpoint/GPU/Colab inference **CHƯA CHẠY**, PostgreSQL server/load/fairness **CHƯA KIỂM CHỨNG**. Browser AI evidence và worker unit tests dùng dữ liệu/predictor tổng hợp; không phải đánh giá chất lượng AI hoặc gold labels. HIGH auto-hold vẫn tắt; không đổi 0.41. Audit/report/appeal retention và public hosting/provisioning staff thật chưa chốt; chỉ local/private synthetic theo T016. Chưa có bulk export, bulk decisions hoặc purge. Lịch sử appeal trong detail có giới hạn 20 author/50 staff, report detail 50; audit phân trang. Queue không cam kết SLA/không starvation giữa các nhóm khi tải lớn. T014/T019 chưa thực hiện.

DB demo hiện có vẫn 0002; trước khi dùng source mới với DB đó, người vận hành cần duyệt, dừng server/worker và backup rồi `alembic upgrade head` tới 0004 theo README. Không downgrade xóa lịch sử để chạy code cũ.
