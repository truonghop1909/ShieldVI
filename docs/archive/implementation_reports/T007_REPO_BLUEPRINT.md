# T007 — Kiểm kê V3 và kế hoạch chuyển đổi

Ngày khảo sát: **30/10/2026 (Asia/Saigon)**. Phạm vi: chỉ khảo sát, baseline và thiết kế; chưa triển khai T008–T015.

## 1. Vị trí thực tế và hướng dẫn

- Workspace: `E:/lamDoAn/`.
- Mã nguồn đang chạy: `ShieldVI_V3_Hybrid_Review/` (gọi là **V3 root** bên dưới).
- Bộ thiết kế/task: `ShieldVI_SocialAI_Design_Docs_v1/` (gọi là **design root**).
- Đây là hai thư mục ngang hàng, chưa phải monorepo như đường dẫn tương đối trong thiết kế. Đề xuất dùng V3 root làm gốc triển khai tương lai để giữ nguyên lệnh legacy; tài liệu hiện tiếp tục ở design root. T007 không sao chép/gộp/di chuyển chúng.
- Tại lần khảo sát đầu không tìm thấy `AGENTS.md`. Sau đó người dùng bổ sung `design root/AGENTS.md`; đã đọc và đối chiếu lại T007. Quy tắc mới yêu cầu **T007 → T016 → task tiếp theo theo dependencies**, mỗi lượt một task; không tự triển khai chuỗi.
- Đã đọc `docs/governance/AGENTS_SOCIAL_ADDENDUM.md`, `docs/architecture/ARCHITECTURE.md`, `docs/architecture/MIGRATION.md`, `docs/architecture/API_CONTRACT.md`, `docs/architecture/DATABASE.md`, T007, T008, T015 và `.agents/skills/shieldvi-architecture-migration/SKILL.md` trong design root.
- `git status --short` ở workspace, V3 root và design root đều báo `fatal: not a git repository (or any of the parent directories): .git`. Chưa có commit/hash hoặc diff Git để làm mốc rollback. Không tự khởi tạo Git.

## 2. Kiểm kê nguồn

Đường dẫn trong bảng thuộc V3 root. [Manifest nguồn](../../baseline/T007/source-manifest.json) ghi **68 file**, kích thước và SHA-256 trước baseline: toàn bộ file trong `app/`, `frontend/`, `tests/`, `notebooks/`, `scripts/`, `models/` cùng file cấp root, loại trừ `node_modules`, `.venv`, `__pycache__`. Manifest bao gồm DB hiện có; datasets được kiểm tra riêng bởi bộ test snapshot. Manifest là mốc nội dung, không phải backup có thể phục hồi.

| Nguồn | Vai trò thực tế / điểm cần giữ khi migration |
|---|---|
| `app/__init__.py`, `app/main.py` | FastAPI singleton, lifespan nạp predictor, API V3, mount dashboard nếu static index tồn tại lúc import. Không có auth/router social. |
| `app/predictor.py` | Lazy import Transformers/Torch; chọn checkpoint; tokenizer max length 128, batch 16, softmax nhãn 1; CUDA nếu có, CPU nếu không. |
| `app/engine.py` | Phân tích cả thread; target từ mention/reply/root fallback; repeated theo actor–target và thời gian; trả advisory. |
| `app/lexical.py` | Offline rule loader từ `app/data/lexicon/active.json`, Unicode/offset, biến thể Việt–Anh và teencode đã duyệt; không sửa xác suất model. |
| `app/schemas.py` | Pydantic request/response, review batch; text 1–8000 ký tự, 1–500 comments/thread, ID tối đa 120, timestamp có timezone, parent tồn tại/không vòng lặp/không ở tương lai, ID duy nhất. |
| `app/database.py` | Summary SQLite tùy chọn: `STORE_SUMMARIES=1`; `DB_PATH` mặc định `moderation_summaries.sqlite3`, tương đối theo cwd. |
| `app/review_store.py` | Human annotation SQLite: `REVIEW_DB_PATH` mặc định `shieldvi_reviews.sqlite3`, upsert theo thread/comment/reviewer, thống kê, export CSV. Reviewer ID do client gửi, chưa phải danh tính xác thực. |
| `app/data/lexicon/` | `active.json`, `reviewed_rules.json`, `candidates.json`, `manifest.json`, README và `sources/` (snapshots, từ gốc, license). Chỉ `enabled_reviewed` được thực thi; candidates pending không được tự kích hoạt. |
| `frontend/src/App.jsx` | Dashboard lab phân tích thread, nhập/xuất JSON/CSV, nhãn người duyệt, stats/history; state React. Gọi toàn bộ API V3 bằng URL cùng origin. Chưa phải social UI hay moderation workflow có phân quyền. |
| `frontend/src/utils.js`, `main.jsx`, `styles.css` | Chuẩn hóa input/timezone, validation, export, thông báo lỗi; React entry và CSS. |
| `frontend/index.html`, `package.json`, `vite.config.js` | React 18, lucide-react, Vite; base `/dashboard/`; build ra `../app/static`, `emptyOutDir: true`; dev port 5173, proxy `/api` và `/health` sang 8000. Chưa có package-lock ở frontend root. |
| `app/static/index.html`, `assets/index-BaiwjHcP.css`, `assets/index-B6t7Eu4q.js` | Build dashboard đang có, FastAPI phục vụ `/dashboard/`. Giữ nguyên trong T007; build baseline xuất sang design root. |
| `tests/` | 6 module test + `conftest.py`, chi tiết ở phần 4. `pytest.ini`: pythonpath `.`, testpaths `tests`. |
| `notebooks/08_ShieldVI_Dashboard_Colab.ipynb` | Luồng cũ V2: `/content/shieldvi_fullstack`, ZIP `ShieldVI_V2_Review_Fullstack.zip`; kiểm tra `frontend/package.json`, `app/main.py`, build static, uvicorn `app.main:app`. |
| `notebooks/09_ShieldVI_V3_Hybrid_Review_Colab.ipynb` | Luồng V3: `/content/shieldvi_v3`, ZIP `ShieldVI_V3_Hybrid_Review.zip`; kiểm tra lexical/review_store; npm install/build, model Drive, review DB Drive, check API version `0.3.0`, health, analyze, stats, proxy iframe. |
| `scripts/check_dashboard.py` | TestClient smoke health/dashboard; chạy nguyên script sẽ đi qua lifespan nạp model thật nếu checkpoint được chọn. T007 dùng smoke riêng không nạp model. |
| `scripts/import_lexicon.py` | Offline rebuild hoặc download tùy chọn; root phụ thuộc `parents[1]/app/data/lexicon`. Test rebuild chạy trên bản sao tạm. |
| `scripts/prepare_social_datasets.py` | Chuẩn bị dữ liệu, giữ tách toxicity/span/normalization và holdout; root `parents[1]/datasets`. Không phải dữ liệu tài khoản mạng xã hội. |
| `scripts/refine_model.py`, `refine_last_block.py` | Thí nghiệm train/refinement, cache theo output; base/train/valid/test/output qua CLI. Đã đọc các liên kết đường dẫn, không chạy train. |
| `models/visobert_head_refined/` | Checkpoint, tokenizer/config, threshold_config, báo cáo selection/audit và diagnostics. Không train hay sửa file. |
| `requirements.txt`, `requirements-dev.txt` | FastAPI/Pydantic, Torch, Transformers `4.57.3`, hub `0.36.2`, tokenizers `0.22.x`; dev thêm pytest/httpx. |
| `run_windows_dashboard.bat`, `README.md`, `.gitignore` | Script đặt cwd về root, `.venv/Scripts/python.exe -m uvicorn app.main:app`, localhost 8000; kiểm tra static, hỏi MODEL_PATH. README lệnh local/Colab và ràng buộc nghiên cứu. |
| `datasets/`, `examples/` | Dữ liệu raw/processed/prepared/review, manifest/license và demo không phải gold; tests đọc snapshot ở đây. Không chuyển thành DB social, không dùng nhãn gợi ý làm dữ liệu gold. |

### Checkpoint và threshold thực tế

1. `MODEL_PATH` nếu có được ưu tiên tuyệt đối; biến này không được đặt trong shell baseline.
2. Nếu không có biến: `app/predictor.py` chọn `V3 root/models/visobert_head_refined` khi có `model.safetensors` và `threshold_config.json` với `approval_status=approved`. Cả hai tồn tại; config hiện ghi `model_version = ViSoBERT V1.1 — ViCTSD`, `threshold = 0.41`.
3. Fallback hiện hardcode `/content/drive/MyDrive/visobert_toxic_final`; cả notebook 08/09 cũng đặt đường dẫn này. Đây là path legacy cần đưa vào cấu hình ở giai đoạn migration, không thêm hardcode mới.
4. `threshold_config.json` của bản refined ghi source checkpoint `C:/Users/admin/Downloads/visobert_toxic_final`. Đã kiểm tra thư mục source này tồn tại, chưa kiểm chứng load/inference. Các báo cáo/README model cũng tham chiếu path Downloads và cache output.
5. Predictor đọc threshold từ checkpoint, chỉ fallback `0.41` nếu không có config. Không được giả định mọi MODEL_PATH tùy ý đều có ngưỡng 0.41. T007 không đổi config/path/selection.
6. Conservative dùng cùng threshold cho moderation và repeated; `research_synthetic` dùng repeated threshold **0.03** riêng. Không đưa chế độ nghiên cứu này vào chính sách social.

**Khác biệt thiết kế:** V1 là baseline yêu cầu nhưng runtime hiện auto-select bản refined V1.1 đã approved. Trước test model thật T011/T012, ghi rõ MODEL_PATH/model_version/hash của bản được chọn; không tự ép về V1 hoặc âm thầm đổi bản refined.

### DB thực tế

- `shieldvi_reviews.sqlite3` đang tồn tại; đã mở **read-only** để xác nhận schema `human_reviews` (và `sqlite_sequence`), không đọc/xuất nội dung người duyệt. Có `UNIQUE(thread_id, comment_id, reviewer_id)`, nhãn clean/toxic/uncertain, score, lexical flag và timestamp. Không có bảng users/posts/comments hay quyết định hiển thị.
- `analyses` trong `app/database.py`: analyzed_at, thread_id, profile, comments_count, flagged, risk_level, risk_score_heuristic; mặc định tắt lưu và không lưu text.
- Nhãn review không lưu text gốc, nhưng lexical evidence trả về có `matched_form` (một đoạn text); không được diễn giải là response hoàn toàn không có dữ liệu văn bản.
- Notebook 09 đặt `REVIEW_DB_PATH=/content/drive/MyDrive/shieldvi_v3_reviews.sqlite3`. Notebook 08 không cấu hình review DB riêng. SQLite trên Drive là dev/demo, cần backup và kiểm thử I/O riêng.

## 3. Toàn bộ route hiện hành

Nguồn: `app/main.py`, schemas và route enumeration trong [smoke.txt](../../baseline/T007/smoke.txt). Không tìm thấy router khác trong app.

| Method/path | Hành vi / bảo toàn | Test hiện có |
|---|---|---|
| `GET /` | JSON service/docs/health/analyze/notice | Smoke T007: 200 |
| `GET /health` | 200 với ready hoặc model_unavailable; model_loaded/path/details | Missing-model test + smoke 200; không chứng minh model ready |
| `POST /api/analyze` | AnalyzeRequest thread → AnalyzeResponse, summary tùy chọn; thiếu model 503; schema lỗi 422 | Mock API, lexical, repeated, profile, validation |
| `POST /api/reviews/batch` | Upsert annotation, trả saved/thread_id/reviewer_id | Temporary DB + score validation 422 |
| `GET /api/reviews` | Lọc thread_id/reviewer_id, tối đa 5000 rows mặc định | Temporary DB |
| `GET /api/reviews/stats` | Counts/FP/FN/uncertain; đây là so sánh nhãn nghiên cứu | Temporary DB |
| `GET /api/reviews/export` | CSV BOM, attachment; tới 100000 rows, escape formula prefix | Temporary DB export; không có test riêng mọi trường hợp formula injection |
| `GET /api/recent` | Khi tắt: storage_enabled=false; bật: limit clamp 1–100 | Smoke nhánh tắt; nhánh bật chưa có test riêng |
| Mount `/dashboard` | StaticFiles html khi index tồn tại lúc import; `/dashboard/` và assets | Smoke 200 index, JS, CSS; chưa test trình duyệt |
| `GET,HEAD /openapi.json`, `/docs`, `/docs/oauth2-redirect`, `/redoc` | FastAPI tạo tự động | Smoke 200 trừ oauth2-redirect chỉ kiểm kê |

Hiện không có `/api/v1/*`, register/login, feed, social CRUD, admin role, durable moderation jobs. Route review legacy không xác thực; không được dùng reviewer_id làm quyền moderator hay đưa nguyên route này thành API social công khai.

## 4. Test và baseline thực chạy

| File | Số case sau parametrization | Phạm vi |
|---|---:|---|
| `tests/conftest.py` | fixture | FakePredictor 0.9 cho marker test, 0.02 cho text khác; dependency override; ép path checkpoint không tồn tại để không load model thật. |
| `tests/test_api.py` | 8 | Repeated với parent/hai thời điểm, single insult, self/missing parent, duplicate IDs, không echo marker, research profile, thiếu model 503/health false. |
| `tests/test_engine.py` | 4 | Không target chính mình, không dùng gold labels/target do client gán, cùng timestamp không repeated, root fallback low không cảnh báo conservative. |
| `tests/test_lexical.py` | 8 | Việt–Anh/obfuscation/context, không tự gán toxic, temporary SQLite review upsert/list/stats/export, invalid review score. |
| `tests/test_lexicon_data.py` | 67 | False positive/context/Unicode/offset, nguồn hash/license, offline rebuild trên bản sao, pending không load, không network, lexical không thay score/threshold/repeated. |
| `tests/test_model_refinement.py` | 7 | Hàm lọc holdout/duplicate/conflict, metric/gate và chọn approved checkpoint bằng fixture; **không train**. |
| `tests/test_social_datasets.py` | 17 | Tách normalization/span/toxicity, validation span, holdout, gated download/path confinement, hash/count snapshot, demo không gold. |

### Lệnh và kết quả

Chạy từ V3 root bằng môi trường `.venv` sẵn có, không cài/nâng dependency:

```powershell
$env:STORE_SUMMARIES='0'
& ./.venv/Scripts/python.exe -m pytest -v -p no:cacheprovider
```

**111 passed, 1 warning in 1.42s**, exit 0. [Output đầy đủ](../../baseline/T007/pytest.txt). Warning: Starlette TestClient deprecation với httpx. Python **3.12.10**, pytest **9.2.0**. Các test DB dùng tmp_path; STORE_SUMMARIES tắt để không ghi summary DB hiện hành.

Từ `V3 root/frontend/`, đổi outDir để không xóa/ghi `app/static`:

```powershell
npm.cmd run build -- --outDir ../../ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/T007/frontend-build --emptyOutDir false
```

Lần đầu **FAIL**, exit 1: EPERM ghi `frontend/node_modules/.vite-temp/vite.config.js.timestamp-*.mjs`. [Output lỗi](../../baseline/T007/frontend-build.txt). Đã thử lại bằng config loader không bundle file tạm:

```powershell
npm.cmd run build -- --configLoader runner --outDir ../../ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/T007/frontend-build --emptyOutDir false
```

Lần thử lại **PASS**, exit 0: Vite **6.4.5**, 1578 modules, 3.68s. Node **v24.19.0**, npm **11.17.0**. [Output thành công](../../baseline/T007/frontend-build-retry.txt), [build kiểm chứng](../../baseline/T007/frontend-build/index.html). Đây là build có override config loader/outDir; lệnh build mặc định ghi static legacy chưa được chạy. Không có lockfile frontend root nên chưa kết luận clean install tái lập được.

Smoke bổ sung bằng inline Python/TestClient: override `app.main.default_model_path` sang `__T007_missing_checkpoint__` không tồn tại, `STORE_SUMMARIES=0`; GET `/`, `/health`, `/api/recent`, `/dashboard/`, hai assets đang có, `/openapi.json`, `/docs`, `/redoc` đều 200; enumerate toàn bộ routes. Không gọi reviews trên DB hiện có. [Output smoke và GPU probe](../../baseline/T007/smoke.txt): Torch **2.15.0+cpu**, CUDA **False**.

**Chưa kiểm chứng:** real checkpoint load/inference (có file model nhưng chưa chạy), GPU/Colab/Drive, giao diện trong browser, clean npm install, production/security/E2E và nhánh summary DB bật. CPU inference có thể dùng được; thiếu CUDA không đồng nghĩa model không thể chạy. Không dùng kết quả mock hay báo cáo model có sẵn để khẳng định độ chính xác thực tế.

Đối chiếu cuối: [integrity-check.json](../../baseline/T007/integrity-check.json) xác nhận cả **68 file** trong manifest giữ nguyên SHA-256, không thêm file nguồn trong các cây đã kiểm kê. Ba file build tách biệt trùng byte với static legacy. Các link trong blueprint và task đã được kiểm tra tồn tại. Cache Python/dependency không thuộc phạm vi manifest.

## 5. Boundary và quyền sở hữu đã chốt cho kế hoạch

| Thành phần tương lai | Sở hữu | Không được làm |
|---|---|---|
| `services/social-api` | Users/roles/auth, posts/comments/replies/feed, Social DB, job/results, moderation policy/visibility, reports/appeals/actions/audit | Import Torch/ViSoBERT, đọc AI SQLite trực tiếp, tin role/reviewer_id client gửi |
| Worker thuộc Social API | Claim job bền vững từ Social DB; gửi context tối thiểu; áp kết quả qua cùng domain/transaction guard | Cấp quyền AI ghi Social DB; chạy inference GPU trong web background task không bền vững |
| `services/moderation-ai` (ban đầu vẫn là `app/`) | Predictor/lexicon/target/repeated và AI annotation/audit riêng | Đọc Social DB, gọi ngược Social API, thay post/comment status hoặc khóa tài khoản |
| `apps/social-web` | UX người dùng, chỉ gọi Social API | Giữ service token hoặc gọi AI trực tiếp |
| `apps/moderation-web` | Queue/quyết định/appeal/audit qua Social API với moderator/admin | Ghi quyết định social qua review DB legacy |

Social DB độc lập: users, posts, comments(parent cùng post), moderation_jobs/results/actions, reports, appeals theo `docs/architecture/DATABASE.md`; SQLite dev rồi PostgreSQL qua migration. AI giữ SQLite review/summary riêng và metadata hạn chế. Không join/copy user DB sang AI; request chỉ có ID opaque/pseudonymous và text/context cần thiết. Nhãn nghiên cứu AI và quyết định hiển thị social là hai nghiệp vụ khác nhau, không đồng bộ hai chiều.

Tạo comment + job trong cùng transaction. Giữ pending/failed khi AI timeout/lỗi; không coi lỗi là sạch. Mọi đổi trạng thái có actor/time/reason/audit. Kết quả về muộn chỉ áp khi revision/job còn hợp lệ và chưa có quyết định moderator mới hơn.

## 6. Contract trao đổi và khoảng trống cần đóng ở T011/T012

Endpoint **dự kiến**, chưa implement: worker → `POST /api/v1/moderate/comment`, schema version `1.0`, private backend authentication, không browser/public key.

- Request example hiện có: `schema_version`, `request_id`, `content_id`, `content_revision`, `text`, `context.post_id/parent_text/recent_comments`, `language_hint`.
- Response example hiện có: `schema_version`, `request_id`, `model_name`, `model_version`, **`model_threshold`**, **`toxicity_score`**, `ai_label`, `lexical_signals`, `target_evidence`, `suspected_repeated_harassment`, `suggested_action`, `decision_authority=advisory`, `limitations`.
- Quy ước đề xuất: lấy tên field cụ thể trong JSON examples làm cơ sở schema. `API_CONTRACT.md` đang mô tả `model_score`/`threshold` khác tên examples; cần thống nhất tài liệu/schema ở T011 trước khi viết client, không tạo hai bộ tên tùy ý.
- Bổ sung response correlation `content_id/content_revision`, `lexicon_version`, thời điểm phân tích và evidence có provenance. Response hiện chưa có đủ các field truy nguyên mà ARCHITECTURE yêu cầu. AI label/score chỉ advisory, không phải status social; không map score >=0.41 thành xóa/ẩn tự động.
- `parent_text` đơn thuần và mảng `recent_comments` rỗng chưa đủ cho engine V3: cần comment_id, pseudonymous user_id, timestamp có timezone, parent_id và mention do platform xác nhận; phải có parent closure trong cửa sổ context để hợp lệ với AnalyzeRequest. Không tạo timestamp/target giả. Không đủ context thì repeated=false/unknown cùng limitation, không bịa bằng chứng từ một text.
- Adapter sẽ map comment + context đã validate vào engine `conservative`, chọn kết quả cho content hiện tại và trả evidence giới hạn. Giữ `/api/analyze`, `/health` và các schema cũ nguyên vẹn.
- T011/T012 cần schema request/response/error và tests: unsupported version, payload/length limits, missing model 503, service auth, invalid context, correlation/revision, duplicate request. Đề xuất initial budget cấu hình: connect timeout 3s, read timeout 60s, tối đa 3 attempts với backoff/jitter; đo model thật rồi điều chỉnh, không hardcode trong UI.
- Idempotency theo request_id + content_id/revision; cùng key khác payload phải lỗi conflict. Retry network/timeout/429/5xx theo chính sách có giới hạn, 4xx validation/auth không retry mù. Claim/lease job chống hai worker; không tạo quyết định trùng và không ghi đè quyết định người duyệt.
- State trong ARCHITECTURE/DATABASE dùng `pending_moderation/approved/needs_review/hidden/failed_review`, còn `moderation_policy.example.json` có `risk_tier` và `PUBLISHED/PUBLISHED_FLAGGED/HELD_FOR_REVIEW/PENDING_MODERATION`. Chưa có mapping thực thi; phải thống nhất policy/state trước T009/T012, không âm thầm coi hai enum tương đương. T007 giữ nguyên các bản draft và ghi rõ khác biệt này.

## 7. Checklist migration theo đúng thứ tự MIGRATION.md

Đây là kế hoạch, tất cả bước sau baseline còn **chưa thực hiện**. Cập nhật theo `AGENTS.md` vừa bổ sung và `tasks/README_SOCIAL.md`: **T016 (policy/state machine) là task tiếp theo sau T007**, trước các bước triển khai bên dưới. Bảng giữ thứ tự chuyển đổi kỹ thuật của MIGRATION.md; danh sách T008 ở mục 8 chỉ là dự kiến, không phải chỉ định bắt đầu T008. T016 chưa được thực hiện trong lượt cập nhật này.

| Bước | Task / việc làm khi được yêu cầu | Cổng kiểm chứng và rollback |
|---|---|---|
| 1 | T007: kiểm kê, git status/blocker, pytest, build, giữ hash/outputs | Baseline ở trên; chưa có Git, cần snapshot/backup thực trước triển khai migration. |
| 2 | T008: thêm `services/social-api/`; reserve `apps/social-web/` cho T010 (chỉ scaffold sớm nếu task sau yêu cầu) | Chạy độc lập khỏi V3, env/port/DB riêng; rollback bằng dừng service mới. |
| 3 | T008 auth/users/roles/migrations, rồi T009 posts/comments/replies/feed | Auth/RBAC/IDOR, DB test riêng, same-post parent, validation/pagination, migration upgrade/rollback thử trên DB bản sao; pytest V3 vẫn đạt. |
| 4 | T010: Social Web gọi Social API, không gọi AI | Register/login/create post/comment/reply và responsive UI; không đụng V3 dashboard. |
| 5 | T011: thêm adapter endpoint vào AI **legacy** `app/` | Contract/schema/auth/size limit, missing-model và mock tests; `/api/analyze`/health/dashboard giữ tương thích; rollback tắt endpoint mới. |
| 6 | T012: durable job/worker, timeout/retry/idempotency/revision guard, private AI client | Mock lỗi/duplicate/stale result, crash/retry recovery; test model thật tại môi trường được phép; có thể dừng worker giữ pending. |
| 7 | T013: moderation-web qua Social API, hoặc link dashboard V3 lúc đầu | Role gate, queue/decision/reason/audit/appeal; annotation V3 không đổi social status. Port mới từ env, tránh xung đột dev 5173 legacy. |
| 8 | T014: E2E, auth/security, DB migration rehearsal và backup/restore | Legacy regression + social E2E; kiểm tra CORS/CSRF theo auth, rate limit, IDOR, revision/concurrency; chỉ chuyển bước 9 khi đạt gate. Commit theo giai đoạn khi có Git và được yêu cầu. |
| 9 | T015: chuyển tối thiểu `app/` → `services/moderation-ai/app/`, `frontend/` → `apps/moderation-web/` | Trước move có regression baseline, sau move chạy lại pytest/build/API/static/model thật. Giữ bản legacy phục hồi tới khi xác minh xong; không xóa source trước gate hồi quy. |
| 10 | T015: xác minh checkpoint/API V3 sau migration, chỉ retire legacy khi có xác nhận | Chưa đủ gate thì chạy lại bản legacy từ backup với DB/model cũ; không xóa checkpoint/DB/history. |

Phụ thuộc đường dẫn cần sửa **ở T015**, không phải T007: app imports/cwd/uvicorn; predictor `parents[1]/models`; lexical `__file__/data`; script import_lexicon/check_dashboard; test imports và dataset roots; Vite outDir/base/proxy và FastAPI mount; notebook 08/09 ZIP layout/assertions/cwd/npm/startup/model/review DB/proxy; batch launcher và README. Chốt nơi static cuối cùng và URL `/dashboard/` trước move để không build vào nhầm service. Đường dẫn DB phải cấu hình tường minh để đổi cwd không tạo DB mới rỗng.

## 8. File dự kiến cho T008 — chỉ đề xuất, chưa tạo

Tất cả path mới dưới **V3 root** theo đề xuất gốc triển khai; không dùng package Python tên `app` ở top-level chung vì có thể che legacy `app`.

| Path dự kiến | Mục đích |
|---|---|
| `services/social-api/pyproject.toml` | Dependency riêng (FastAPI, persistence/migrations, password hash, auth, test), không Torch/Transformers. |
| `services/social-api/.env.example`, `.gitignore`, `README.md` | Tên biến config/DB/origins/secret và lệnh chạy; không secret thật; service-local venv/DB ignore. |
| `services/social-api/src/shieldvi_social/__init__.py`, `main.py`, `config.py` | App factory, env validation, health, CORS cụ thể; chạy package riêng. |
| `services/social-api/src/shieldvi_social/db.py`, `models/user.py`, `models/__init__.py` | Session/transaction và users/roles/status; SQLite dev, constraint/index phù hợp PostgreSQL. |
| `services/social-api/src/shieldvi_social/security.py`, `dependencies.py` | Password hash, token/session validation, server-side role gate; chốt auth transport trong T008 rồi test tương ứng. |
| `services/social-api/src/shieldvi_social/schemas/auth.py`, `schemas/__init__.py`, `routes/auth.py`, `routes/users.py`, `routes/__init__.py` | Register/login/me, response không password_hash, không cho client tự cấp role. |
| `services/social-api/alembic.ini`, `migrations/env.py`, `migrations/script.py.mako`, `migrations/versions/0001_users.py` | Versioned migration users, upgrade/downgrade dev/test. |
| `services/social-api/tests/conftest.py`, `test_auth.py`, `test_permissions.py`, `test_migrations.py` | DB test độc lập; password/token/expiry/duplicate identity/RBAC, reject public role escalation; migration test. |
| `design root/tasks/social-api/T008-auth-database.md` | Ghi file thực sửa, lệnh/output/blocker khi được yêu cầu T008. |

T008 chưa tạo post/comment/job hay Social Web; đó là T009/T010/T012. Không sửa `app/`, `frontend/`, checkpoint, DB legacy, threshold, notebook hay baseline tests để triển khai auth mới. Dừng sau T007 cho tới yêu cầu tiếp.
