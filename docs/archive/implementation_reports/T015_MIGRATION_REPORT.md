# T015 — Chuyển AI backend và research dashboard legacy

Ngày 30/10/2026 (Asia/Saigon). **DONE sau baseline/regression pass và yêu cầu T015 của người dùng.** Không train, đổi threshold/checkpoint, migrate DB hay deploy. HIGH auto-hold vẫn tắt.

## Layout và tương thích

| Trước | Sau T015 | Giữ tương thích |
|---|---|---|
| `app/` | `services/moderation-ai/app/` | Root `app/__init__.py` đưa import path vào cùng implementation; lệnh `uvicorn app.main:app` từ V3 root và monkeypatch/dependency overrides vẫn hoạt động |
| `frontend/` | `apps/moderation-web/legacy-v3/` | Root `frontend/package.json` chuyển tiếp build/dev/preview; cài bằng `run install:legacy` |
| `app/static` | `services/moderation-ai/app/static` | AI vẫn phục vụ `/dashboard/`, HTML/CSS/JS trùng byte trước/sau |
| Model/datasets/DB | **Giữ vị trí hiện có** | Default/relative model, review và summary paths neo V3 root; absolute env paths không đổi |

Dashboard Social đã tồn tại tại `apps/moderation-web`, nên đưa research React V3 vào **thư mục con** thay vì ghi đè app cha. Source/dependencies của hai Social UI không đổi. Dev ports: Social Web 5173, Social moderation 5174, research V3 5175; research URL phục vụ vẫn `/dashboard/` trên AI 8000. Research annotation DB không trở thành nguồn quyết định moderation Social.

Canonical AI có requirements riêng, không import Social API/Torch vào Social runtime. Root requirements chuyển tiếp cho lệnh cài V3 cũ; task dùng AI venv hiện có, không cài/train lại model. Model selection vẫn approved refined V1.1 như trước, threshold **0.41**. Engine/lexical/adapter/contract và lexicon data không đổi logic/byte. Predictor chỉ đổi đường dẫn; review/summary chỉ đổi cách neo file path, không schema/data.

Các compatibility entrypoints và snapshot rollback được giữ lại. Không retire/xóa lớp tương thích sau khi kiểm chứng.

## Gate trước khi chuyển

- Hai root không có Git metadata, `git status --short` báo không phải repository; không tạo Git/commit/push. Dùng source snapshot và hash manifests để review.
- Đã lưu **59 source/static/config files** vào [rollback-source](../../baseline/T015/rollback-source), không gồm node_modules/venv/cache hoặc model/DB. [Before manifest](../../baseline/T015/before-manifest.json).
- Đã ghi hash **52 model/dataset/database files**, gồm checkpoint/config và các DB hiện có; [protected manifest](../../baseline/T015/protected-manifest.json). Không copy/move/overwrite các DB/model.
- Baseline mới trước move: **139 legacy tests**, **177 Social API tests**, cả **3 frontend builds** pass. Legacy baseline build vào evidence riêng, không ghi đè static đang dùng.
- Move chỉ sau gate trên, kiểm tra absolute source/target nằm trong V3 workspace và target chưa tồn tại. Chuyển `app` và `frontend` cùng volume bằng Move-Item, không recursive delete. Move cả dependency directory frontend đang có, tạo lockfile từ cache, không tải dependency mới.

## File cập nhật

Đường dẫn tính từ V3 root:

- Move toàn bộ `app` sang `services/moderation-ai/app`; thêm `paths.py`, service README/requirements/.env.example/.gitignore. Sửa path trong predictor/database/review_store và comment static main; không sửa thuật toán/contract.
- Move frontend sang `apps/moderation-web/legacy-v3`; đổi Vite outDir sang static AI, dev port 5175, configLoader runner; thêm lockfile/README. React source giữ nguyên byte.
- Thêm import bridge `app/__init__.py`, npm wrapper `frontend/package.json`/README; cập nhật root README, requirements, `.gitignore`, `run_windows_dashboard.bat`.
- Cập nhật `scripts/{import_lexicon,check_dashboard,evaluate_social_policy}.py` để dùng canonical resource/provenance paths; không chạy import/download/train.
- Thêm `tests/test_migration.py` cho cwd/import/model/DB/static/Colab. Test model selection hiện có đổi assertion relative MODEL_PATH sang file tuyệt đối tại root, giữ cùng semantics file trước kia khi chạy từ root.
- Social tests chỉ đổi đường dẫn contract và cwd AI trong `run_fullstack`, `run_outage`, `run_worker_smoke`; Social runtime/source DB không đổi.
- Cập nhật hai notebook Colab: canonical paths, cwd service, build research app, explicit summary path; giữ Drive MODEL_PATH/REVIEW_DB_PATH V3. Giải nén vào thư mục mới, không xóa session cũ, kiểm tra ZIP traversal và hỗ trợ archive có một thư mục root bao ngoài.
- Design: task T015, MIGRATION/ARCHITECTURE/API_CONTRACT/RUN_LOCAL, CHANGELOG, report và evidence T015. Các baseline T007–T014/T019 giữ là snapshot lịch sử, không sửa hash/path lịch sử để giả pass.

## Kết quả sau chuyển

| Lệnh / kiểm chứng | Kết quả thực |
|---|---|
| V3 root, `STORE_SUMMARIES=0`, AI `.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider` | **143 passed**, 1 warning, 4.24s; gồm 139 legacy + 4 migration tests. [log](../../baseline/T015/legacy-pytest.txt) |
| Social API `.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider` | **177 passed**, 1 warning, 53.44s; [log](../../baseline/T015/social-pytest.txt) |
| `npm.cmd run build` ở research legacy-v3 | **PASS**, exit 0; [log](../../baseline/T015/after-legacy-build.txt) |
| Lệnh V3 cũ `npm.cmd --prefix frontend run build` | **PASS**, exit 0, đúng outDir service; [log](../../baseline/T015/compat-build.txt) |
| `npm.cmd run build` ở moderation-web và social-web | **PASS**, exit 0, asset hashes như baseline; [moderation](../../baseline/T015/moderation-build.txt), [social](../../baseline/T015/social-build.txt) |
| Fullstack 5 process, AI fixture khởi động với cwd service mới | **1 Chrome passed**, 12.6s, workflow register/moderate/outage/manual/appeal/restore/recovery; [log](../../baseline/T015/fullstack/browser-tests.txt), [process health](../../baseline/T015/fullstack/process-health.json), [cleanup](../../baseline/T015/fullstack/cleanup.json) |
| Dashboard Social regression trên DB tạm | **6 Chrome passed**, 10.8s; [log](../../baseline/T015/admin-regression/browser-tests.txt) |
| Social Web regression trên DB tạm | **9 Chrome passed**, 12.2s; [log](../../baseline/T015/social-regression/browser-tests.txt) |
| AI venv chạy `docs/baseline/T015/real_http_smoke.py` | **PASS với checkpoint CPU thật**, bản rollback-source và canonical server; [result](../../baseline/T015/real-http-smoke.json) |
| Notebook syntax/layout | **PASS** trong migration tests; compile code cells local, không chạy Google Colab |
| Rollback PowerShell launcher | Parser **PASS**, không khởi động rollback trên DB thật; snapshot backend đã được rehearsal HTTP với DB tạm |
| Hash/path checks | **59 source files map đầy đủ**, snapshot không đổi, **52 protected files không đổi**, lexicon/static/React V3 source byte-identical, Social UI source không đổi; [integrity](../../baseline/T015/integrity-check.json), [after manifest](../../baseline/T015/after-manifest.json) |

Baseline logs: [legacy](../../baseline/T015/before-legacy-pytest.txt), [Social API](../../baseline/T015/before-social-pytest.txt), [legacy build](../../baseline/T015/before-legacy-build.txt), [moderation build](../../baseline/T015/before-moderation-build.txt), [social build](../../baseline/T015/before-social-build.txt). Một phase test ngay sau move cũng pass 139 legacy trước khi thêm 4 migration cases. Warnings chỉ Starlette/httpx deprecation và NO_COLOR/FORCE_COLOR, không phải model fake fallback.

### Đối chiếu HTTP/model thật

Chạy hai AI process **tuần tự**, cùng weights và CPU hai threads, offline Hugging Face, CUDA tắt. Trước: source snapshot với MODEL_PATH tuyệt đối; sau: service canonical cwd và **không MODEL_PATH**, kiểm tra approved default selection. Không đọc/ghi review/summary DB thật; bật summary storage chỉ trỏ SQLite tạm.

`/api/analyze` và internal `/api/v1/moderate/comment` cùng kết quả trước/sau (bỏ timestamp internal khi so sánh), OpenAPI bằng nhau, `/health` loaded model thật. Ba câu synthetic có scores **0.007649 / 0.283179 / 0.970688**, threshold 0.41, model **ViSoBERT V1.1 — ViCTSD**. Đây là kiểm tra tương đương migration, không phải đo accuracy mới hoặc dữ liệu gold. Không chạy lại toàn bộ ViCTSD để tune; xem kết quả T019.

Đã thử root/docs/redoc, toàn bộ static assets, research review batch → list → stats → CSV, analyze → recent khi STORE_SUMMARIES=1 và internal auth. Research HTML/JS/CSS trùng SHA-256. Hai server dừng đúng process tree do smoke tạo. Fullstack browser test vẫn dùng predictor tổng hợp có gắn nhãn test; không trộn nó với inference thật bên trên.

## Rollback không ghi đè source/data

Nếu cần quay lại AI trước T015:

1. Dừng AI server hiện tại; tạm dừng worker nếu cần giữ queue pending trong lúc thay endpoint. Giữ nguyên Social DB/schema, không downgrade hoặc mass unhide.
2. Giữ các absolute MODEL_PATH/REVIEW_DB_PATH/DB_PATH đang dùng, cùng service token. Kiểm tra snapshot/protected manifests; không chọn model/DB khác để thử trên dữ liệu thật.
3. Từ V3 root, chạy source snapshot qua app-dir thay vì overwrite file mới:

```powershell
# Giữ MODEL_PATH/REVIEW_DB_PATH/DB_PATH hiện hành; các default helper dùng repo root.
& ../ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/T015/run_rollback.ps1
```

Launcher dùng AI venv, cwd V3 root, root checkpoint hiện có nếu chưa set MODEL_PATH, DB cũ tại root nếu chưa set override; bind 127.0.0.1:8000. Snapshot chứa adapter/contract T014, nên worker tiếp tục nói cùng API. Không copy/xóa/restore model, DB, static mới hoặc lịch sử. **Đã rehearsal snapshot server cùng model thật với DB tạm**, chưa chạy rollback trên DB thật. Nếu PowerShell chặn script, dùng chính lệnh `python -m uvicorn app.main:app --app-dir <absolute-rollback-source> ...` sau khi đặt các env paths; không cần thay execution policy toàn máy.

Khi trở lại canonical, dừng snapshot server và dùng [lệnh service mới](../../modules/moderation_ai.md). Nếu muốn phục hồi hẳn layout cũ, giữ bản hiện hành riêng, review before-manifest và chỉ restore các source/config từ rollback-source khi được yêu cầu; không tự xóa service mới hoặc chép đè DB. Cơ chế chạy snapshot cho phép rollback trước khi phải thay file.

## Vận hành và giới hạn

[Runbook](../../guides/RUN_LOCAL.md), [AI service](../../modules/moderation_ai.md), [research React](../../modules/legacy_research_dashboard.md).

Default Social DB vẫn **0002_content**, kiểm tra read-only và hash không đổi. Social API/worker code hiện hành yêu cầu 0004; nếu dùng DB demo cũ, cần backup/verify, dừng process và có duyệt nâng schema riêng. T015 ở đây là migration **vị trí code**, không phải Social DB migration; user request không bị diễn giải thành overwrite dữ liệu.

Colab/GPU/Drive/protected proxy, clean npm install trong Colab và đóng gói ZIP thực tế **CHƯA CHẠY**. Notebook đã compile và cập nhật layout, không khẳng định hạ tầng Colab pass. Không tạo service-local AI venv mới; dùng venv ML có sẵn, service có requirements độc lập để operator cài khi cần. Legacy research endpoints giữ private/loopback vì không có Social auth; không public deploy. Không mở lại outage 600s ở T015: đã đo thật ở T014/T019; E2E sau chuyển vẫn kiểm tra 503/recovery/manual guard. HIGH auto-hold tắt, chưa có độc lập thread/policy gold; không auto-ban/delete.
