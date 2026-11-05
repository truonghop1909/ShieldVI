
## CURRENT AUTHORITY — real evaluation criteria restored, historical DONE preserved

Latest PartsA/B/C + follow-up override earlier synthetic-only/CPU permission for new work. **T028 real-evaluation criteria: BLOCKED** until permitted200real threads, the same human's manual Round1/Round2, privacy/leakage checks and evaluation lock. Earlier synthetic T028 DONE is historical scope evidence, not real completion. All other confirmed DONE records are retained. Current machine-readable criteria: `tasks/CURRENT_AI_SCOPE.json`; evidence: `reports/ai_update/independent_readiness_20261103/`.

Wikimedia collector PAUSED by user; no further contact/path questions in this session, no fake identity or browser impersonation. Research other public licenses; do not ingest unclear rights. Continue independent synthetic development, preparation/local registry/integration/reporting. New training and production changes are not authorized. Distinguish preparation/development DONE from blocked real-world acceptance; dependencies remain visible.

# AUTO_PROGRESS — 02/11/2026

## Trạng thái thực tế

- Hiện hành 03/11/2026: đã sửa docs T028 sang AI-authored synthetic/G2-S; T028 TODO để kiểm acceptance mới. Bộ 200/2.048 và bản training 1.994/54 đã có. T028 real-world cũ trở thành tùy chọn, không còn blocker contact/nhãn người cho scope mới.
- DONE trong phiên: **T021–T027 (7 task)**. T020 đã DONE trước phiên.
- BLOCKED hiện hành: **T029 (1)** — readiness code G2 còn theo scope real cũ cần đồng bộ, G3/resource chưa đạt. Các trạng thái real-world BLOCKED phía dưới là lịch sử, không áp dụng G2-S mới.
- WAITING_APPROVAL: **0**. T028 TODO theo scope mới; T029 BLOCKED như trên; T030–T033 TODO. Không tự đổi task đã DONE hoặc thực hiện train.
- Thứ tự một-task-mỗi-lượt cũ được người dùng cho phép vượt qua trong phiên này; không mở quyền train/deploy/external upload.

## Task và bằng chứng

### T021 — DONE
5 immutable threads validated; 150 NEEDS_REVIEW rows and 21 semantic counterexamples. No gold labels invented; no fixtures copied twice. Initial tmp_path permission/setup errors resolved using workspace basetemp.

Files: scripts/ai_regression_data.py, tests/test_ai_regression.py, tests/fixtures/ai_update/counterexamples.json, datasets/fixtures/genz_regression/reviewer_needed.csv, scripts/ai_task_progress.py
Tests: pytest tests/test_ai_regression.py -q --basetemp reports/ai_update/test_tmp/T021_2: 4 passed, 1 warning

### T022 — DONE
Standalone typed multi-tag context signals, mixed apology+attack preserved; original fixture recovery cases and raw model invariance verified. Target/repeated integration remains T024/T025.

Files: services/moderation-ai/app/context_signals.py, tests/test_context_signals.py
Tests: Context/regression subset 32 tests passed inside 128-test combined run

### T023 — DONE
4 new local reviewed slang rules plus vkl; original djt reused after duplicate-alias guard caught attempted duplicate. Offline rebuild reproducible; email/domain and benign NPC protected. No model score/policy changes.

Files: services/moderation-ai/app/lexical.py, services/moderation-ai/app/data/lexicon/reviewed_rules.json, services/moderation-ai/app/data/lexicon/active.json, services/moderation-ai/app/data/lexicon/candidates.json, services/moderation-ai/app/data/lexicon/manifest.json, tests/test_lexicon_update.py
Tests: Combined context/regression/lexicon suite: 128 passed, 1 warning

### T024 — DONE
Separate attack-target inference with mapped textual/platform references, conflict abstention, low parent/history candidates; no legacy target redefinition. Test exposed overly broad addressed-reply cue; restricted to second-person addressee.

Files: services/moderation-ai/app/target_signals.py, tests/test_target_signals.py
Tests: pytest target/context/engine: 39 passed, 1 warning

### T025 — DONE
Versioned v2 engine qualifies evidence using context + grounded recipient + profile model threshold; 0.03 stays research-only. Legacy v1 behavior kept for compatibility. Recovery-only turns excluded; previous genuine attacks remain.

Files: services/moderation-ai/app/signal_engine.py, services/moderation-ai/app/context_signals.py, services/moderation-ai/app/target_signals.py, tests/test_signal_engine.py
Tests: signal/target/context/internal legacy regression: 60 passed, 1 warning

### T026 — DONE
Typed /api/v2/analyze and research UI show raw model/context/attack target/human authority separately. Legacy /api/analyze and Social internal 1.0 unchanged; Social v3 promotion remains T032-gated. UI build isolated, not deployed.

Files: services/moderation-ai/app/main.py, services/moderation-ai/app/schemas.py, services/moderation-ai/app/signal_engine.py, apps/moderation-web/legacy-v3/src/App.jsx, tests/test_api_v2.py, contracts/analysis_response_v2.schema.json, docs/ai-update/V2_COMPATIBILITY.md, reports/ai_update/T026/real_smoke.json
Tests: Full backend: 243 passed, 1 warning; npm build isolated output: PASS, 1578 modules; Real CPU model: 5 fixtures API v1/v2 HTTP200, scores and labels identical

### T027 — DONE
Local ingest prepared 1645 synthetic NEEDS_REVIEW records, 418 unique normalized texts; raw text preserved, exact/near-duplicate thread components audited. Empty train/validation/test partitions correctly enforce verification/license/development gates; not ready for training.

Files: scripts/prepare_ai_update_data.py, tests/test_ai_data_ingestion.py, datasets/ai-update/review_v1/dataset_manifest.json, datasets/ai-update/README.md
Tests: Data ingestion 7 tests passed; timezone-instant guard corrected and checked; all source rows accounted for

### T028 — BLOCKED
Safe evaluation tooling and manifest prepared, but zero rights-approved independent real conversations and zero human VERIFIED_SOLO blind labels were supplied. Synthetic/dev/trained-on texts are rejected (including disguised/near duplicates); no benchmark metric published.

Files: scripts/evaluate_ai_update.py, tests/test_independent_evaluation.py, datasets/ai-update/evaluation_manifest.json, reports/ai_update/T028/evaluation_gate.json
Tests: Full backend regression: 261 passed, 1 warning; Evaluation CLI returned expected exit 2 / BLOCKED; metrics=null

## Kiểm tra cuối

- Backend: **265 passed, 1 warning**, exit 0. Log: reports/ai_update/final/pytest.txt.
- Build research Dashboard: PASS, 1578 modules; output riêng reports/ai_update/frontend_build_final. Không ghi đè static đang phục vụ; chưa chạy browser UI E2E.
- Real-model CPU: API v1/v2 5 fixture × 30 comment; điểm và nhãn raw giống nhau. Xem reports/ai_update/T026/real_smoke.json.
- 31 checkpoint/config/tokenizer/holdout/fixture/SQLite hashes so với T020 không đổi; task Social giữ nguyên.
- Hai literal test và nhãn UI mới từng bị transport PowerShell đổi Unicode thành dấu hỏi; sửa encoding, giữ nguyên assertions; lần fail và lần pass đều giữ trong log cuối.

## Resume

Root: ShieldVI_V3_Hybrid_Review. Đọc AGENTS, đúng task/skill, trạng thái tại hai TASK_ORDER và reports/ai_update/auto_session.json; không làm lại task đã DONE.
Ưu tiên tiếp tục T028 sau khi có dữ liệu thật ẩn danh với quyền dùng, tách blind evaluation, và người dùng gán nhãn độc lập (VERIFIED_SOLO, annotator_id, reviewed_at). Các nguồn synthetic/dev/đã train bị loại khỏi blind evaluation. Không tạo gold giả hoặc dùng 150 fixture thay thế.
Command kiểm tra: .venv/Scripts/python.exe -X utf8 -m pytest tests -q -p no:cacheprovider --basetemp reports/ai_update/test_tmp/<new-run-id>. Tạo parent test_tmp trước; không dùng lại basetemp chứa dữ liệu người dùng.
Command gate: .venv/Scripts/python.exe -X utf8 scripts/evaluate_ai_update.py --manifest datasets/ai-update/evaluation_manifest.json --output reports/ai_update/T028/evaluation_gate.json. Hiện exit 2/BLOCKED là đúng, không phải metric PASS.
API mới /api/v2/analyze dùng context/target/evidence v3. /api/analyze và Social /api/v1/moderate/comment vẫn legacy; tích hợp Social v3 phải chờ T032 và dependencies. UI source đã cập nhật nhưng build test nằm riêng, chưa deploy.
Không train, đổi checkpoint/0.41, chỉnh test độc lập, upload ra ngoài, xóa DB, git push hoặc deploy. Yêu cầu T028 V2 sau đó cho phép đọc API/thu nội dung từ nguồn đã audit ALLOWED, theo chính sách truy cập; không có quyền train hay thu nguồn UNKNOWN/RESTRICTED. Các gate T029/T031 vẫn cần duyệt nếu sau này đủ dependency.

## T028 V2 active request — 02/11/2026

Only T028-A..F now authorized, including permitted Internet collection. Old runner is suspended; do not advance T029-T033. Audit A done: old 30/313 dataset not found. Collector must use audited rights and a user-supplied Wikimedia operator contact. Counts/checkpoints live in datasets/real_conversations/manifests/progress.json.

## T028 V2 — checkpoint cuối phiên 02/11/2026

- Task hiện tại: T028 **BLOCKED**; không còn code đang làm dở. Dừng theo yêu cầu riêng T028, không chạy T029–T033.
- A DONE (bộ cũ 30/313 không tìm thấy); B BLOCKED (operator contact); C IN_PROGRESS (tool đã test, dữ liệu thật/kiểm PII người còn thiếu); D/E DONE (công cụ); F BLOCKED (chưa nhãn/kiểm nguồn/privacy/completeness/lock). Main T028 chưa DONE.
- Số thực tế: 0/200 thread; 0 allowed thread; 0 invalid; 0 duplicate; 0 comment; 0 labeled; 0 unlabeled/UNCERTAIN; 1 nguồn có metadata giấy phép đã xác minh; 0 nguồn đại diện nội dung; Batch 01 đang bị chặn, 0 batch hoàn thành. Không đưa các record của unit/browser test vào số liệu.
- Đã tạo/sửa: `scripts/real_dataset/` (schema, HTTP cache/retry/rate/budget, collector/resume, PII/HMAC, SQLite, validation/lock, review API/UI); 7 wrapper Python nêu trong README; `tests/test_real_dataset_pipeline.py`; `datasets/real_conversations/README.md`, `ANNOTATION_GUIDE.md`, `SOURCE_AUDIT.md`, `QUALITY_REPORT.md`, manifests/schema/exclusions và audit reports; `.gitignore`; file T028, hai TASK_ORDER, AUTO_PROGRESS.
- Test: `python -X utf8 -m pytest tests -q -p no:cacheprovider --basetemp reports/ai_update/test_tmp/T028_full_release` → **299 passed, 1 warning**, exit 0 (34 test mới); `node --check scripts/real_dataset/review_ui/app.js` exit 0. Chrome E2E trên dataset test tạm PASS: full text, autosave, round 2, CSV, no XSS, 0 model request. Không có build cần chạy cho UI static HTML/CSS/JS này. Preview QA đã dừng.
- Collector thật: `python -X utf8 scripts/collect_real_threads.py --through-batch 1 --max-pages 1 --max-requests 3 --max-seconds 30` → exit 2, BLOCKED trước network vì thiếu contact. Hai probe metadata trước đó xác minh Wikipedia CC BY-SA 4.0/API; không thu hội thoại.
- `validate_real_dataset.py` và `anonymize_threads.py` exit 0 trên dataset rỗng; quality status **EMPTY_DATASET**, independent_evaluation_ready=false. Đây không phải PASS tiêu chí đủ dữ liệu. Chưa có evaluation_lock hay nhãn gold.
- Integrity: reports/ai_update/T028_v2/session_verification.json → 31/31 model/config/threshold/holdout/fixture/SQLite gốc không đổi; 4 source khác snapshot lịch sử nhưng đều có mtime trước audit T028; giữ nguyên, không rollback. T028 không sửa service model/inference. ViCTSD supervised splits chỉ được đọc để lập exclusion; không sửa dữ liệu. Checksum development nguồn cũng được giữ. Không train/push/deploy/upload. Mạng chỉ cho các nguồn đã audit, với contact thật.
- Bằng chứng: `reports/ai_update/T028_v2/pytest_full_release.txt`, `browser_result.json`, `UI_REVIEW_TEST_ONLY.png`, `collector_attempt.txt`, `validate_actual.txt`, `session_verification.json`; dữ liệu thống kê thật: `datasets/real_conversations/manifests/progress.json`, `reports/quality.json`.
- Việc tiếp theo: cần người dùng cung cấp contact thật (email/HTTPS URL dự án/tài khoản Wikimedia) để header nhận diện người vận hành. Không tự mượn danh tính. Set `SHIELDVI_COLLECTOR_CONTACT`, chạy `scripts/collect_real_threads.py --through-batch 4`; có giới hạn mỗi lượt và chạy lại để resume. State/salt/cache trong raw là riêng tư, không xóa. Giấy phép chưa xác minh thì không collect; thiếu số lượng/coverage thì báo thiếu, không tạo giả.
- Để gán nhãn sau thu thập: `.venv/Scripts/python.exe -X utf8 scripts/review_real_dataset.py --port 8010`, mở http://127.0.0.1:8010/; dùng cùng reviewer ID hai lượt. SQLite riêng tự tạo trong `datasets/real_conversations/annotations/`, không dùng DB moderation/Social. Chi tiết trong README/ANNOTATION_GUIDE tại thư mục dataset.
- Chưa hoàn thành: thu đủ nguồn/hội thoại có quyền, phủ chủ đề/phong cách, kiểm PII và completeness thủ công, hai lượt human labels, khóa độc lập và benchmark. Không cần hai người cho solo nhưng không thể báo IAA. Không tự đổi T029–T033 khỏi TODO.

## Synthetic 200 — yêu cầu riêng

- Trạng thái: DONE; dataset synthetic riêng, T028 vẫn BLOCKED và không được thay bằng dữ liệu này.
- Đã sinh và kiểm tra: 200/200 hội thoại, 2048 bình luận; 4/4 batch hoàn thành. Nhãn tham khảo AI, không phải human gold.
- Nhãn: {"CLEAN": 1798, "TOXIC": 196, "UNCERTAIN": 54}; exact duplicate=0, near-comment=0, near-thread=0.
- File: scripts/synthetic_data/ (catalogue + compiler/validator), scripts/generate_synthetic_conversations.py, scripts/validate_synthetic_conversations.py; datasets/synthetic_conversations/ (JSON từng thread, 4 manifest batch, comments.csv, annotations.csv, manifest.json, README, quality_report); tests/test_synthetic_conversations.py.
- Checkpoint: datasets/synthetic_conversations/manifest.json; resume bằng `.venv/Scripts/python.exe -X utf8 scripts/generate_synthetic_conversations.py --through 200`. Không ghi đè thread đã tồn tại nếu khác catalogue; không xóa dữ liệu người duyệt.
- Đã chạy compiler validation cấu trúc/parent/time/target/repeated và duplicate/near-duplicate cho 200 thread. Test pytest và audit cuối được bổ sung khi kết thúc.
- Việc kế tiếp: người dùng xem và rà nhãn; chưa train, UNCERTAIN giữ riêng. Không chạy T029–T033; không gọi API ngoài hay sửa model/0.41/test/DB.

## Synthetic 200 — kiểm chứng cuối phiên

- **DONE theo yêu cầu sinh synthetic riêng**: 200 JSON, 2.048 comment, 4 batch × 50, comments.csv/annotations.csv/manifest/README/quality_report. Không phải task T028/T029 và không đổi các TASK_ORDER AI/Social.
- Các mốc thực tế đã chạy và lưu sau mỗi batch: pilot 10/113 PASS → batch 1: 50/513 → batch 2: 100/1.013 → batch 3: 150/1.548 → batch 4: 200/2.048. Batch mới lần lượt có 513/500/535/500 comment.
- Nhãn tham khảo AI: CLEAN 1.798, TOXIC 196, UNCERTAIN 54. 10 chủ đề × 20; 3–6 người/thread, 10–18 comment/thread. 98 thread không có TOXIC; 85 comment repeated có ID bằng chứng cùng actor/target; không dùng làm real-world gold.
- Exact duplicate 0, near-comment 0 (char5 Jaccard ≥0.85, min 35 ký tự), near-thread 0 (≥0.60). 156 chuỗi category khác nhau, tối đa 6 thread cùng chuỗi; vẫn có thiên lệch vai và khung can ngăn/công kích. Phần lớn thread ngắn, 87,79% CLEAN; cần người xem và rà nhãn, không tuyên bố đại diện mạng xã hội.
- Kiểm thử: `.venv/Scripts/python.exe -X utf8 -m pytest tests/test_synthetic_conversations.py -q -p no:cacheprovider --basetemp reports/ai_update/test_tmp/synthetic_200_subset` → **16 passed, 1 warning**, exit 0.
- Regression: `.venv/Scripts/python.exe -X utf8 -m pytest tests -q -p no:cacheprovider --basetemp reports/ai_update/test_tmp/synthetic_200_full_final` → **315 passed, 1 warning**, exit 0; chạy offline.
- `.venv/Scripts/python.exe -X utf8 scripts/validate_synthetic_conversations.py` → PASS; resume `generate_synthetic_conversations.py --through 200` → PASS, các JSON/batch cũ khớp checksum. Lỗi so sánh khóa số của manifest khi resume đã được sửa trong compiler, có test kiểm snapshot không đổi và từ chối ghi đè thread bị chỉnh.
- JSON/CSV audit độc lập giữ mọi trường, 2.048 dòng mỗi CSV, không rơi dòng khi nối khóa. 31/31 file model/config/0.41/holdout/fixture/SQLite gốc không đổi. Exact overlap với nguồn synthetic/development cũ: 0. Dataset thật T028 vẫn 0 thread, không khóa, file task vẫn BLOCKED; không sửa tập test, train, gọi API ngoài, push/deploy hoặc DB.
- Bằng chứng: `reports/synthetic_conversations/{pytest_subset.txt,pytest_full.txt,validate_final.txt,generate_resume_final.txt,final_audit.json}`; source: `scripts/synthetic_data/scenarios_01..04.txt`, compiler `pipeline.py`; wrapper generate/validate; test `tests/test_synthetic_conversations.py`.
- Việc kế tiếp do người dùng quyết định: đọc JSON/CSV và rà nhãn tham khảo. Không tự train hoặc mở T029. UNCERTAIN không được đổi ngầm thành nhãn nhị phân. Để xác minh lại, chạy validator; để tái xuất/resume chạy generator mốc 200, nó từ chối ghi đè thread khác nội dung nguồn. Giữ nhãn người sửa trong bản review riêng/version mới.

## Synthetic reviewer — yêu cầu giao diện duyệt riêng

- **DONE**: thêm chế độ synthetic vào UI/API local dùng chung; launcher `scripts/review_synthetic_dataset.py` (mặc định 8011), adapter `scripts/synthetic_data/review_store.py`, `review_app.py`; tái sử dụng ReviewStore và UI hiện có, không tạo service AI khác.
- Hiển thị 200 thread/2.048 comment đầy đủ, nhãn/lý do AI gốc riêng với biểu mẫu người; lọc UNCERTAIN/TOXIC/CLEAN/chưa xác nhận, tìm tiêu đề/topic/ID, tự lưu bản nháp, xác nhận từng comment, history và hai lượt cùng người.
- Nhãn người/tiến độ ở `datasets/synthetic_conversations/human_review/`, source JSON/CSV/manifest bất biến. Bắt buộc lý do sửa label/metadata, ghi chú UNCERTAIN, revision và source SHA; repeated cần bằng chứng lượt trước đã được chính người đó duyệt. Không tự chấp nhận nhãn AI hoặc bản nháp.
- Xuất backup CSV có revision và JSONL chỉ nhãn đã xác nhận của reviewer đang chọn. Bản JSONL giữ AI gốc, nhãn người, dấu ai_assisted_review=true/synthetic/human_gold=false/evaluation_eligible=false/training_ready=false và thông tin partial-thread/context. Không khóa synthetic thành T028.
- File sửa chung: `scripts/real_dataset/store.py` (model annotation cấu hình được), `review_app.py` (profile/adapter/export), `review_ui/{index.html,app.js,style.css}`; `.gitignore`, README synthetic và AUTO_PROGRESS. Không sửa source inference/model/backend Social.
- Test liên quan: `python -X utf8 -m pytest tests/test_synthetic_review.py tests/test_real_dataset_pipeline.py -q -p no:cacheprovider --basetemp reports/ai_update/test_tmp/synthetic_review_subset` → **45 passed, 1 warning**, exit 0.
- Regression toàn backend cuối: `python -X utf8 -m pytest tests -q -p no:cacheprovider --basetemp reports/ai_update/test_tmp/synthetic_review_release` → **327 passed, 1 warning**, exit 0, offline. Warning Starlette/httpx có sẵn. UI static, `node --check scripts/real_dataset/review_ui/app.js` PASS.
- Chrome/Playwright trên bản sao tạm: PASS 200 thread, full text >5.000 ký tự, XSS không thực thi, lọc/sửa có lý do/autosave/resume/export, giữ nhãn AI gốc và chế độ blind thật không lộ nhãn AI; 0 page error/0 model request. Không ghi nhãn thử vào dataset người dùng. Server QA đã dừng.
- Bằng chứng: `reports/synthetic_conversations/review_tests.txt`, `review_pytest_full.txt`, `review_browser_result.json`, `REVIEW_SYNTHETIC_TEST_ONLY.png`; audit cuối/server state được lưu cùng thư mục.
- Việc tiếp theo: người dùng mở URL local, nhập reviewer ID và tự duyệt. Không train, đổi checkpoint/0.41, sửa held-out, hoặc bắt đầu T029; T028 thật vẫn BLOCKED. Xem phần hướng dẫn mới trong README synthetic.

Synthetic reviewer — kiểm tra bàn giao: `reports/synthetic_conversations/review_final_audit.json` PASS; 200 JSON và hai CSV nguồn khớp toàn bộ checksum, 31/31 file model/test/SQLite gốc giữ nguyên. 12 test reviewer mới nằm trong 327 test PASS. Thêm test repeated không được dựa vào bản nháp AI chưa được người xác nhận. Server local đang mở ở http://127.0.0.1:8011/ (trạng thái/PID/lệnh dừng trong review_server_state.json); production hiện 0 nhãn người/0 bản nháp, không có nhãn thử. DB reviewer mới tách riêng, không reset dữ liệu. T028 thật vẫn 0 thread/BLOCKED, không đổi TASK_ORDER hay bắt đầu task train.

## Reviewer synthetic — sửa ô chọn nhãn bị mờ

- DONE: tái hiện Chrome với trình duyệt mới tại 8011, reviewer trống khiến toàn bộ ô và nút xác nhận disabled. Điều kiện trước đây không được giải thích rõ.
- Chỉ chế độ synthetic dùng sẵn `solo_01` nếu chưa có mã lưu; giữ nguyên mã người dùng đã chọn. Có nút Áp dụng mã/Enter, chỉ báo mã và lượt đang dùng; xử lý mã sai, lỗi lưu và tránh áp dụng trùng khi blur/click cùng lúc. Không tự lưu/xác nhận nhãn AI, không đổi quy trình blind thật.
- File sửa: `scripts/real_dataset/review_ui/{index.html,app.js,style.css}`, README synthetic và AUTO_PROGRESS. Backend/model/source JSON/CSV/DB nhãn cũ không bị chỉnh.
- Kiểm tra thực tế trên server đang chạy: trước sửa reviewer="", label_disabled=true, confirm_disabled=true; sau sửa reviewer=solo_01, label_disabled=false, confirm_disabled=false.
- Test: `node --check scripts/real_dataset/review_ui/app.js` PASS; `python -X utf8 -m pytest tests/test_synthetic_review.py tests/test_real_dataset_pipeline.py -q -p no:cacheprovider --basetemp reports/ai_update/test_tmp/synthetic_gray_fix` → **46 passed, 1 warning**, exit 0.
- Chrome trên bản sao tạm PASS: fresh storage mở thao tác ngay, Enter/nút Áp dụng đổi mã, mã sai không khóa người đang dùng; lọc/sửa/lý do/autosave/resume/xuất vẫn hoạt động, không auto-confirm, không có page error/model request; chế độ blind thật giữ nguyên. QA servers đã dừng, server người dùng 8011 giữ chạy.
- Bằng chứng: `reports/synthetic_conversations/gray_fix/{pytest.txt,review_browser_result.json,REVIEW_SYNTHETIC_TEST_ONLY.png,final_audit.json}`. Hướng dẫn người dùng Ctrl+F5 ở http://127.0.0.1:8011/ để nhận JS mới.

## Lựa chọn người dùng — dùng trực tiếp nhãn AI, không gán lại

- **DONE phần chuẩn bị dữ liệu**: người dùng không có thời gian gán nhãn và đã yêu cầu dùng bản AI gán sẵn. Đây là lựa chọn mới, thay khuyến nghị reviewer bắt buộc trước đây; không tiếp tục yêu cầu người dùng duyệt 200 thread. Giao diện review vẫn tùy chọn, không tự đánh dấu AI thành người duyệt.
- Đã thực sự xuất `datasets/synthetic_conversations/training_ai_labels_v1/{train.jsonl,train.csv,excluded_uncertain.jsonl,manifest.json,README.md}`. 2.048 nguồn = **1.994 training** (1.798 CLEAN=0, 196 TOXIC=1) + **54 UNCERTAIN** giữ riêng, không ép thành CLEAN.
- Provenance: synthetic/label_source=synthetic, review_status=AI_REFERENCE_ACCEPTED_BY_USER, manual_review_performed=false, human_gold=false, evaluation_eligible=false. Không giả VERIFIED_SOLO, không ghi đè SQLite nhãn người, dataset thật hoặc tập test.
- Code: `scripts/synthetic_data/training_export.py`, wrapper `scripts/prepare_synthetic_training.py`; source schema/quality/checksum được kiểm trước xuất, resume kiểm hash và từ chối ghi đè bản bị sửa. Không nới gate của `prepare_ai_update_data.py` hoặc evaluation độc lập.
- Test: `.venv/Scripts/python.exe -X utf8 -m pytest tests/test_synthetic_training_export.py tests/test_synthetic_conversations.py -q -p no:cacheprovider --basetemp reports/ai_update/test_tmp/ai_label_export` → **22 passed, 1 warning**, exit 0; gồm 6 test xuất mới. Lệnh prepare_synthetic_training.py chạy thật thành công, chạy lại idempotent PASS.
- Không train, gọi model/API, đổi checkpoint/0.41, sửa source 200 thread/CSV gốc hoặc T028. Không tạo validation/test. Toàn bộ bản này chỉ là nguồn bổ sung training bằng nhãn AI, chưa tự được loader cũ hardcode đường dẫn nạp vào.
- Resume: dùng bản train.csv/JSONL đã chuẩn bị, không yêu cầu lại nhãn người. Nếu người dùng yêu cầu train ở bước tiếp theo thì cấu hình thí nghiệm/loader/check leakage riêng; chưa coi task T029 hoặc T028 hoàn tất và chưa tự chạy train.
- Bằng chứng: `reports/synthetic_conversations/ai_label_export_tests.txt`, `ai_label_export_audit.json`, manifest bản xuất. Nhãn AI vẫn có thể sai; không tuyên bố đã có human gold hay metric thực tế.

## T029 — 03/11/2026, làm theo task

- **BLOCKED / PREPARED_NOT_TRAINED**. User yêu cầu làm theo task sau khi chấp nhận nhãn AI. Theo T029/G2/G3 chỉ chuẩn bị script/config trước, không tự chạy CPU/GPU train. T028 vẫn BLOCKED; T030–T033 không bắt đầu.
- Đã nối exporter AI với 6.942 original train; 1.994 synthetic; tổng 8.936 (22,31%). Exact/near char5 ≥0.90/min40 trên validation/test text và train gốc không phát hiện overlap; 54 UNCERTAIN tách riêng. Không sửa heldout, không dùng test label để chọn model.
- File: configs/t029_candidate.json; scripts/{prepare_t029_training.py,train_t029_candidate.py}; tests/test_t029_preparation.py; notebooks/T029_Train_Candidate_Prepared.ipynb (chưa chạy); docs/ai-update/T029_TRAINING_PREPARATION.md; reports/ai_update/T029/{prepared/,preflight.json,approval_PROPOSED.json,pytest.txt,base_smoke.json}; task T029/hai TASK_ORDER/AUTO_PROGRESS.
- Cấu hình đề xuất: original V1; 3 epochs; batch8 × accum2; LR2e-5; weight_decay0.01; max_length128; seed20261103; patience1; synthetic weight1; threshold0.41; GPU Colab với giới hạn3.600s; output candidate mới. Receipt approved=false/cost_acknowledged=false, không giả người dùng đã duyệt hyperparameters/runtime.
- Test liên quan: 17 passed, 1 warning, exit0; log reports/ai_update/T029/pytest.txt. Không optimizer trong tests. Preflight BLOCKED đúng: G2/T028 chưa có real verified lock, G3 chưa có receipt đúng SHA, CUDA unavailable; packages baseline compatible. V1 forward inference CPU tách riêng không phải training.
- Resume: đọc docs/ai-update/T029_TRAINING_PREPARATION.md và config; hoàn tất G2/T028, duyệt đúng G3/resource, chuẩn bị mới ở môi trường Colab. Không copy manifest Windows để giả đã có approval Colab. Không dùng synthetic thay blind real data hoặc yêu cầu user gán lại synthetic. Không tự chạy script legacy train_synthetic_experiment.py đang hardcode bộ100 và head-only.

T029 — kiểm tra cuối 03/11/2026: **344 passed, 1 warning**, exit0; log `reports/ai_update/T029/pytest_full_release.txt`. Lần regression đầu phát hiện notebook training thiếu bootstrap canonical/ZIP an toàn theo quy ước repository; đã bổ sung import adapter từ service thật, kiểm ZIP không thoát thư mục và giữ session cũ, không thay test để PASS. V1 smoke thật PASS, optimizer_steps=0. `reports/ai_update/T029/final_audit.json` PASS: 31/31 model/config/threshold/heldout/fixture/SQLite gốc không đổi; source/data chuẩn bị đúng hash; notebook chưa chạy, receipt approved=false. Chưa có candidate hoặc cải thiện validation để nghiệm thu. T029 BLOCKED/PREPARED_NOT_TRAINED; không chạy T030.

## Tiếp tục T028 — 03/11/2026

- User yêu cầu thực hiện T028, không chạy T029. Đã kiểm task/skill/state, thử collector thật: exit2 trước network vì không có operator contact; 0/200 thread, 0 comment, 0 verified human labels, 0 batch. Không đánh dấu DONE.
- Đã đọc lại chính sách Wikimedia và khảo sát nguồn chính chủ ViHSD/ViTHSD/VOZ-HSD/ViHOS để tìm bộ có nhãn người sẵn. Nguồn gated không được vượt hoặc chấp thuận thay user; nhãn AI/span/comment-only không tự biến thành gold hội thoại. Chỉ khảo sát metadata, không tải corpus. SOURCE_AUDIT được bổ sung căn cứ và URL.
- Test pipeline/evaluation: **44 passed, 1 warning**, exit0; log reports/ai_update/T028_resume_20261103_tests.txt. Quality EMPTY_DATASET/independent_ready=false; report reports/ai_update/T028_resume_20261103.json. Không sửa source/model/test/DB/synthetic.
- Input còn thiếu đã hỏi: contact thật (email/HTTPS project URL/Wikimedia user) được phép gửi trong header Wikimedia. Không tìm email riêng từ config/credentials, không mượn email tác giả nguồn. Khi nhận được input, set env cho đúng tiến trình, resume collector theo batches 20→50→100→200; giữ state/salt. Nhãn người và kiểm nguồn/privacy/completeness là gate riêng sau thu thập. Không yêu cầu gán lại synthetic đã được user chọn dùng AI labels.
- Trạng thái T028 giữ BLOCKED; T029 vẫn BLOCKED, không có training. Chưa có thay đổi điều kiện G2/G3 hoặc task Social.

## T028 đổi scope theo yêu cầu người dùng — 03/11/2026

- Chỉ sửa docs: T028 mới là AI tự viết/gán nhãn synthetic/G2-S, manual review tùy chọn, không yêu cầu contact Wikimedia hoặc bộ hội thoại thật. Quyết định này thay scope real-world cũ; không tiếp tục hỏi contact cho T028 mới. Hồ sơ/collector/real manifests giữ nguyên làm tùy chọn lịch sử.
- Tái sử dụng bộ 200 hội thoại/2.048 comment đã có, 1.994 training nhị phân +54 UNCERTAIN; không sinh trùng hoặc đọc dữ liệu đó làm blind test. Giữ AI provenance, không giả human gold/VERIFIED_SOLO, không sửa test ViCTSD gốc.
- T028 đặt TODO để nghiệm thu scope mới; không tự DONE. T029 vẫn BLOCKED do runtime G2 cũ cần đồng bộ và G3/resource chưa duyệt, không train. Docs chỉ rõ cần kiểm artifact thực theo G2-S thay vì sửa cờ real manifest.
- Đồng bộ task T028/T029/T030, hai TASK_ORDER, AGENTS/skill AI, annotation/experiment/release/Colab docs, hướng dẫn chuẩn bị T029 và README dataset. Lịch sử task T028 cũ được giữ nguyên trong mục gập. Không sửa source Python/config/checkpoint/database/JSON dataset hoặc trạng thái Social.
- Bước kế tiếp: thực thi nghiệm thu T028 theo scope mới và đồng bộ readiness runtime có test; không gọi crawler hoặc yêu cầu gán nhãn thủ công. G3/training/deploy vẫn cần phạm vi phê duyệt riêng.

T028 doc revision validation: local links/status indices/history PASS; 8 runtime/data/config SHA giữ nguyên; `pytest tests/test_migration.py -q -p no:cacheprovider --basetemp reports/ai_update/test_tmp/T028_doc_revision` → **4 passed, 1 warning**, exit0. Report: reports/ai_update/T028_doc_revision_20261103.json. Không đổi code train/readiness, config, model hoặc dataset; chỉ docs và report kiểm tra.

## ACTIVE — Autonomous REAL + GenZ500 → T033, 03/11/2026

Latest attachment authorizes continuous T028–T033 safe work and supersedes previous single-task/synthetic-only instructions. T028 is again REAL 200 and stays BLOCKED/PARTIAL until real requirements pass; synthetic never counts as real. Collector attempt exit2 before network (contact missing), REAL=0. No further contact question required to proceed with fallback.

Synthetic fallback target500: preserve original200/2048 and all source/review/checksum files; extend in datasets/synthetic_conversations/genz_v2 as a new schema version, import200 with lineage and author300 genuinely new microplots. Pilot20 then30/50 batches; categories and needs_human_review per latest request; train vs development split by family; API-clean export; no external LLM calls. Session state: reports/ai_update/autonomous_20261103/progress.json. Request attachment SHA stored there.

Do not stop after each batch. After dataset, carry out independent T029 preparation/smoke, T030 real-model development comparison, T031 local registry/rollback, T032 tests/builds, T033 evidence report. GPU/resources/paid services/production remain gated. Do not fake candidate training or human gold. Next: code GenZv2 schema/validator and write20 new pilot thread source rows.

GenZ v2 checkpoint 220/500: 2251 comments, 5 batch manifests; validation PASS, exact/near duplicate 0; REAL remains0/BLOCKED. Next checkpoint 250. Source catalogue scripts/synthetic_data/genz_catalogue; all original200 snapshots untouched.

GenZ v2 checkpoint 250/500: 2551 comments, 6 batch manifests; validation PASS, exact/near duplicate 0; REAL remains0/BLOCKED. Next checkpoint 300. Source catalogue scripts/synthetic_data/genz_catalogue; all original200 snapshots untouched.

GenZ v2 checkpoint 300/500: 3051 comments, 7 batch manifests; validation PASS, exact/near duplicate 0; REAL remains0/BLOCKED. Next checkpoint 350. Source catalogue scripts/synthetic_data/genz_catalogue; all original200 snapshots untouched.

GenZ v2 checkpoint 350/500: 3551 comments, 8 batch manifests; validation PASS, exact/near duplicate 0; REAL remains0/BLOCKED. Next checkpoint 400. Source catalogue scripts/synthetic_data/genz_catalogue; all original200 snapshots untouched.

GenZ v2 checkpoint 400/500: 4065 comments, 9 batch manifests; validation PASS, exact/near duplicate 0; REAL remains0/BLOCKED. Next checkpoint 450. Source catalogue scripts/synthetic_data/genz_catalogue; all original200 snapshots untouched.

GenZ v2 checkpoint 450/500: 4577 comments, 10 batch manifests; validation PASS, exact/near duplicate 0; REAL remains0/BLOCKED. Next checkpoint 500. Source catalogue scripts/synthetic_data/genz_catalogue; all original200 snapshots untouched.

GenZ v2 checkpoint 500/500: 5115 comments, 11 batch manifests; validation PASS, exact/near duplicate 0; REAL remains0/BLOCKED. Next checkpoint None. Source catalogue scripts/synthetic_data/genz_catalogue; all original200 snapshots untouched.

GenZ500 complete: 500 threads /5115 comments, 200 imported+300 new; 11 batch manifests. AIlabels4667 CLEAN/369 TOXIC/79 UNCERTAIN, human0. Train440threads4398 eligible rows; development60threads isolated by family. New preparation11340 rows (6942 ViCTSD+4398 synthetic), ratio38.78%, no exact/near held-out/challenge overlap. T029 BLOCKED: no CUDA/exact resource approval, optimizer0. Root350PASS, Social177PASS in service venv (root venv initially lacked Alembic); all3frontend buildsPASS. Proceed independent T030/T031/T032/T033 per latest user authorization.

GenZ500 complete: 500 threads /5115 comments, 200 imported+300 new; 11 batch manifests. AIlabels4667 CLEAN/369 TOXIC/79 UNCERTAIN, human0. Train440threads4398 eligible rows; development60threads isolated by family. New preparation11340 rows (6942 ViCTSD+4398 synthetic), ratio38.78%, no exact/near held-out/challenge overlap. T029 BLOCKED: no CUDA/exact resource approval, optimizer0. Root350PASS, Social177PASS in service venv (root venv initially lacked Alembic); all3frontend buildsPASS. Proceed independent T030/T031/T032/T033 per latest user authorization.

T028 BLOCKED: REAL0/200; missing genuine operator contact. DatasetB synthetic500/5115 complete, 11 successful batch manifests; cannot count as REAL. Source/labels/gold not invented.

T029 BLOCKED: GenZ research data PREPARED_NOT_TRAINED:11340 rows=6942 ViCTSD+4398 synthetic; synthetic38.78%, holdouts and challenge no exact/near overlap. New config configs/t029_genz500_candidate.json; prepared reports/ai_update/T029/genz500_prepared. Preflight actual blockers: matching G3 resource receipt absent; CUDA unavailable. G2-S eligibility passes without changing real evaluation gate. Original config/default real protocol preserved. No optimizer/candidate.

T030 BLOCKED: Development subtask complete: frozen60 synthetic threads/620 comments;617 known AI labels,3 UNCERTAIN excluded. Real V1 CPU scores at0.41: macroF1=.739974, toxicP=.465116/R=.571429; raw scores/labels invariant. Hybrid target11/11 emitted correct but24/35 abstained; repeated0/7 versus legacy diagnostic2TP/2FP/5FN. Full historical B1/B2 ablation lacks pre-update lexical/context snapshot; real benchmark absent. CandidateN/A. Do not claim improved. Artifacts reports/ai_update/T030/genz500.

T031 BLOCKED: Local preparation COMPLETE: configs/model_registry.local.json, opt-in app/model_registry.py; validates artifact hashes/.41, explicit shadow and V1 fallback. Not imported by production main or default selector. Real V1 fallback/API smoke PASS after deliberately injected primary-load failure;503->200 recovery, legacy/v2 raw equal. Candidate absent, no candidate-versus-baseline tradeoff/release decision; activation remains unapproved. Local registry proof reports/ai_update/autonomous_20261103/local_registry_smoke.json.

T032 DONE: Authorized independent integration verification complete for existing runtime/contracts, not a new candidate release. Social177PASS on disposable migrated SQLite. Five-process Playwright E2E1PASS: create/moderation/outage/retry/manual review/appeal/recovery; browser sends0directAI requests, logs5files no private synthetic markers, all owned processes exited. AI predictions in fullstack are explicit fixture scores; separate registry smoke uses real V1 legacy/v2 API and503->200 recovery. Three web buildsPASS isolated outputs. No live DB migration or HIGH auto-hide activation. Evidence reports/ai_update/autonomous_20261103/e2e_v2 and *_tests/build_*.txt.

GenZ v2 checkpoint 500/500: 5115 comments, 11 batch manifests; validation PASS, exact/near duplicate 0; REAL remains0/BLOCKED. Next checkpoint None. Source catalogue scripts/synthetic_data/genz_catalogue; all original200 snapshots untouched.

T030 supplementDONE (synthetic development scope): original T020 B0captured responses found; actual B0–B3 replay150fixed regression comments, frozen weights/input hashes and byte-identical legacy engine verified. B2 uses cached original per-text lexicon, no old-module claim on new texts. Raw149known classifier unchanged, evidence26→7comments with fewer non-attack-reference examples; no target/event gold precision on these5. Separate GenZ challenge failures remain unchanged. Newscript scripts/evaluate_regression_ablation.py; artifacts reports/ai_update/T030/regression_ablation. Notebook now prepared for GenZ500 config, unexecuted. Canonical E2E seed contract path fixed (identical fileSHA), guard still requires temporary DB.

## CURRENT HANDOFF —03/11/2026, request complete to safe execution limit

DatasetB COMPLETE500threads/5115comments=200legacy2048+300new3067;11successfulbatch manifests; labels4667CLEAN/369TOXIC/79UNCERTAIN,5115AI/human0; technicalduplicates0, semantic/naturalness unverified. Train440threads4398binary rows (UNCERTAIN/reviewflags excluded), development60threads620comments; frozen lock intact. Preparation11340rows=6942ViCTSD+4398synthetic,38.78%; no exact/near held-out/challenge matches.

T030/T032/T033 DONE (declared development evaluation, independent integration verification, evidence handoff). T028/T029/T031 BLOCKED (REAL0/contact/rights/gold; CUDA/G3; candidate nottrained/activation notapproved). No task IN_PROGRESS. No optimizer, external paidAPI, upload, checkpoint/threshold/test overwrite, liveDB/reset, push or deploy.31protected hashes and200legacythread/2CSV checksums unchanged.

Actual final tests: root358PASS/1warning (handoff_root_tests.txt); Social177PASS/1warning in servicevenv; browserE2E1PASS after canonical contract-path fix;3frontend buildsPASS isolated. RealV1 CPU development620commentsPASS at0.41; MacroF1=.739974 on617knownAI labels, target11/11emitted but24/35abstained; repeated0/7. B0–B3 replay150oldfixtures separate uses T020cachedrealV1, original per-textlex forB2 and byte-identical legacyengine; no fresh-gold claim. Fallback smoke realV1 and503→200PASS.

Resume root E:/lamDoAn/ShieldVI_V3_Hybrid_Review. Read reports/ai_update/autonomous_20261103/progress.json and docs/ai-update/final-report/README.md. Dataset datasets/synthetic_conversations/genz_v2; CLI scripts/generate_genz_dataset.py --through500 is idempotent. New config configs/t029_genz500_candidate.json, prepared reports/ai_update/T029/genz500_prepared; train runner default preflight refuses execution without exactGPU/cost receipt/CUDA. Notebook prepared for500 but unexecuted. Next requires legitimate REAL operator/source/rights and actual human protocol, or approved CUDA runtime for candidate. Do not substitute AI labels for realgold or alter frozen challenge after viewing errors.

## ACTIVE — GAME_RANK_30 context recovery, synthetic-only T028

User explicitly replaces REAL prerequisite with self-authored synthetic data. T028 IN_PROGRESS; GenZ500 unchanged;12newthreads/120AI comments generated in datasets/fixtures/context_recovery_v1 before app rules change. GAME30 user reference frozen:4TOXIC(c08,c11,c15,c18),26CLEAN; not gold. Authorship metadata audit repaired1repeat flag without label/text/target changes; first generation preserved. No train. Next capture originalV1 before scores/signals, then context/assessment/API/UI changes and regression report including losses.

## CURRENT — GAME_RANK_30 synthetic context recovery COMPLETE

Latest request replaces REAL prerequisite: T028synthetic-only DONE; no real/contact/manualgold required. AI12threads/120comments created before rule edits in datasets/fixtures/context_recovery_v1; original500/5115unchanged. GAME30userreference frozen separately,4TOXIC(c08,c11,c15,c18)/26CLEAN,notgold. No expectedlabel changes; initialmetadata audit repaired1repeat flag without text/label/target edits.

Actual beforeV1CPU890comments, aftercache+actualV1API30GAME: raw4TP/5FP/21TN/0FN unchanged; contextual assessment4TP/0FP/26TN/0FN. Main rootcause served oldstatic index-B6t7Eu4q.js called /api/analyze; source wasV2but bundle stale. Newlocalbundle callsV2 with raw/assessment/policy/reply-target separated; c21ACK and clause-scoped new-attack recognition added. ExactGAMErepeat evidence4comments; no c21/c23. Restart backend/hardrefresh required for user session; no existing process killed.

Tests actual: root417PASS/1warning(handoff_tests.txt);Social177PASS/1warning;DashboardChrome replayPASS;Social5processfixtureE2E1PASS;DashboardbuildPASS;actualV1afterAPI/PydanticPASS(static200/legacy200). jsonschema runtimevalidator missing; schema generated from typedmodel. Initial rulepass4regressions+quote case fixed, storedattempt1/firsttests. One newtest had accidentalUnicodewrite corruption; restored intended text, expectedclass unchanged. One collector tempfile WinError5 transient; freshbasetemp recheckPASS, no collector/testexpected edits.

Final0newerrors/abstentions vsraw and0newcontext errors on890developmentcomments. Residuals explicitly retained: GenZ16FP/9FN/0of7repeated events recovered;4otherfixtures4FP/1FN. New120assessmentallcorrect onAIrefs; not human/realworld accuracy. TargetGenZcorrect11→13of35, coverage37.14%, no targeterrors; no target/eventgold for4otherfixtures. No hide of residuals, no test/threshold tuning.

31protectedartifacts+200oldthreads/2CSV+500GenZ/exports/frozenlocks unchanged; no modeltraining/checkpoint/default0.41/realDB change/push/productiondeploy. Humanlabels not autosaved. T022/T024/T025/T026 confirmedDONE retained with follow-up evidence;T029/T031 stillBLOCKED(CUDA/G3,candidate) and not started. T030/T032/T033 earlierhandoff remains historical.

Resume rootE:/lamDoAn/ShieldVI_V3_Hybrid_Review. Currentprogress reports/ai_update/context_recovery_20261103/progress.json; report docs/ai-update/CONTEXT_RECOVERY_GAME_RANK_30.md. Source scripts/evaluate_context_recovery.py(beforeimmutable;afterreusesactualscores), scripts/audit_context_recovery_evidence.py, scripts/smoke_context_dashboard.mjs; original fixture unchanged. Prior autonomous progress.json/ARTIFACTS are historical; do not overwrite their hashes to look current. Next user step restartbackend onlocalport andCtrl+F5, or supply approvedCUDA config for a separately authorized train; do not auto-startT029.

## ACTIVE — finish remaining tasks, bounded CPU alternative

User asks to run all tasks and revise blockers. Inventory found onlyT029/T031 notDONE. Authorize feasible research scope: frozen V1 encoder, train head only, max4CPUthreads/900seconds/localcost0, new checkpoint, one run; validation-only selection then separate finaltest audit, no tuning after test. GPU/fullfine-tune and production remain unperformed. T029IN_PROGRESS,T031TODO; configs/t029_genz500_cpu_head.json and reports/ai_update/all_tasks_cpu_20261103/progress.json. No old data/config/checkpoint overwritten.

T029 DONE for revised head-only CPU scope: real534optimizersteps/3epochs/400.94s,11340trainingrows. Encoder/base/source unchanged, original0.41 unchanged, reloaderror0. Validation .76370125→.75304166 (worse), no activation or repeated training. Newcandidate models/candidates/T029_genz500_head_cpu_20261103_r03. T031 IN_PROGRESS: evaluate actual candidate once on finaltest, synthetic diagnostics and local registry/fallback/rollback; reject if gates fail. FullencoderGPU NOT_RUN.

## CURRENT HANDOFF — all remaining tasks COMPLETE under revised feasible scope

Latest user: run all tasks and revise blockers. RemainingT029/T031 executed; all27existingtaskfilesnowDONE, including14AI-updateT020–T033. T001–T006filesabsent, not recreated/claimed. Prior confirmedDONE states preserved. No BLOCKED/WAITING/IN_PROGRESS remains in the current task inventory.

T029actual boundedlocalCPUhead training:11340rows=6942ViCTSD+4398AI synthetic,3epochs/534optimizersteps/400.94seconds,4threads/cost0,encoder96,975,360paramsfrozen/head592,130paramsadapted. Candidate models/candidates/T029_genz500_head_cpu_20261103_r03; newconfig configs/t029_genz500_cpu_head.json; sources/encoder/V1 hashesunchanged/reloaderror0/threshold0.41. FullencoderGPUtraining NOT_RUN. CPUrecord quotes latestrequest and binds config/preparedSHA, explicitly doesnot claim manualhyperparameter/GPUcostapproval.

T031reviewDONE: actual3models compared on2000ViCTSDvalidation/1000historicaltest/890already-vieweddevelopmentcomments. Validationoriginal.763701→candidate.753042(worse); test.738958→.748633(better), no retrain/selection/gatechangeaftertest.1newGenZFP(SGZ500_0242_C02,“t ngồi thảm được, ghế chiếm chỗ quá”,score.447190). GAME30and4attackevidence preserved. DecisionREJECT_PROMOTION_KEEP_EXISTING_DEFAULT. Explicitlocalshadowload, implicitcandidate selectiondenied; deliberatecandidate-loaderfault fallbackrealV1; rollbackASGI503→200; legacy/V2/internalSocial1.0API200, rawsamepermodel. No default/prod/policy/realDBactivation. Registry configs/model_registry.cpu_r03.local.json.

Evaluationruntimeoptimized after direct attempt stopped duringvalidation beforetestpredictions; preserveddirect_forward_attempt*. Finalscoreuses identicalencoderSHA/tokenizationchecked eachbatch and actual3heads; fullforwardprobesmaxdifference1.79e-7, no heldoutscorewithin1e-5of.41. Gate frozen beforetest, componentinference reuse disclosed, not fabricated/simulation.

Final434rootPASS/1warning; CPUpreflight25(overlapping)PASS. No frontend/Socialsourcechanges thisrun; earlierintegrationevidence retained, newcandidate actualisolatedAPI/fallbacksmoke added.31protectedhashes+200legacythreads/2CSV+GenZ500/frozenexports+12contextfixtures/userref+ViCTSDheldouts+liveSQLite unchanged. No downloads/paidAPI/GPUcost/reset/push/deploy/auto-hide.

Resume E:/lamDoAn/ShieldVI_V3_Hybrid_Review. Currentprogress reports/ai_update/all_tasks_cpu_20261103/progress.json; report docs/ai-update/final-report/CPU_HEAD_COMPLETION.md; actualtrainingreport insidecandidate; candidate_evaluation.json/evaluation_protocol.json/ARTIFACTS incurrentreports. Keep existingdemo/default; candidate rejectedforpromotion. FullGPU remains optionalunexecuted and separately gated. Do not silently convert thishead-onlycompletion into fullfine-tuning or production readiness. No nexttask auto-started.


## Follow-up r04 — revise refused work and continue

**Follow-up status: IN_PROGRESS.** Prior task DONE and r03 rejection are preserved. One additional bounded CPU head-only research attempt:4threads/900seconds/cost0. New config lowers synthetic loss .5→.1 and LR3e-5→1e-5, increases distillation .5→1.0. Encoder/data/0.41 stay fixed. Historical validation-only selection; no test rescore or example-specific tuning. This exploratory follow-up after the old test was inspected is not fresh independent evaluation. Original quality gates remain frozen; no production promotion.

Evidence: `reports/ai_update/candidate_revision_20261103/predeclared_experiment.json`; current progress in `tasks/AUTO_PROGRESS.md`. Completion requires actual optimizer/reload/integrity evidence and a validation verdict.


## CURRENT FOLLOW-UP r04 — COMPLETE, promotion disabled

Actual bounded CPU follow-up completed: 356optimizersteps/2epochs/431.84s, encoderfrozen, newcheckpoint r04. ValidationMacroF1 original0.763701/r03.753042/r040.756865; toxicP0.613065/R0.525862. Decision **REJECT_PROMOTION_KEEP_EXISTING_DEFAULT**, unchanged original gates. No new test/challenge inference or promotion; historical evaluation is not freshblind. Prior27task DONE states preserved. Follow-up status COMPLETE for execution/review, not model acceptance.

Root448PASS/1warning;40preflightPASS.31protectedhashes+all200/500source datasets+12contextfixtures/userreference/validation/test/SQLite/defaultV1.1 unchanged. No paidGPU/fullencodertraining/upload/download/push/deploy. Files: scripts/review_t029_validation.py, tests/test_t029_validation_review.py, configs/t029_genz500_cpu_head_r04.json; task/index/progress and3AI docs updated; newcandidate/reports separate.

Current evidence reports/ai_update/candidate_revision_20261103/; report docs/ai-update/final-report/CANDIDATE_REVISION_R04.md. Resume from this section, not historical IN_PROGRESS/BLOCKED notes above. No remaining task ready in the27existing files; next: Stop this recipe; retain default and negative result. Do not relax gates or rescore test.


## CURRENT requested training r05 — IN_PROGRESS

User explicitly asks to load new dataset and train: “hãy nạp dataset mới để train mô hình đi”. One bounded local CPU classifier-head continuation from approved V1.1, encoder frozen; max4threads/900s/cost0. DatasetGenZ500 train split +ViCTSD original; keep development/test/labels/default unchanged. Newrun T029_genz500_head_cpu_20261103_r05; evidence reports/ai_update/train_genz500_r05_20261103/. Previous DONE states and r03/r04 negative decisions are preserved. No GPU/full-encoder training or promotion.


## CURRENT requested training r05 — COMPLETE

Explicit latest train request executed: new GenZ500 dataset,11340rows=6942ViCTSD+4398AI references; warmstart approvedV1.1 classifier, frozenV1-compatibleencoder. Actual 534steps/3epochs/474.17s; selectedepoch2; config5e-6/synweight.1/distill1/max4CPUthreads900s/cost0. Saved models/candidates/T029_genz500_head_cpu_20261103_r05; reloadedprobeerror0.0. No fullencoder/GPU training.

ValidationMacroF1 original0.763701/default0.760205/r050.755418; candidateP0.646067/R0.495690. DecisionREJECT_PROMOTION_KEEP_EXISTING_DEFAULT; gates unchanged, no test/challenge scoring and no freshblind claim. Training completion doesnot imply promotion; defaultV1.1 remains active. Prior taskDONE and negative r03/r04 evidence preserved.

42relatedpytestPASS/1warning; actualposttrainreload/source/data/integritychecksPASS;31protected artifacts +200legacy/500GenZ/contextreference/validation/test/SQLite unchanged. No externalAPI/download/paidGPU/reset/push/deploy. Follow-upstatusCOMPLETE. Current report docs/ai-update/final-report/GENZ500_TRAIN_R05.md; resume evidence reports/ai_update/train_genz500_r05_20261103/progress.json. Next: keep default, review measured validation and remaining release evidence before any model adoption.

## CURRENT local demo restart — READY

Requested “giờ hãy chạy lại”: started localhost-only hidden demo processes. Approved default V1.1: http://127.0.0.1:8020/dashboard/; experimental r05 comparison: http://127.0.0.1:8021/dashboard/. Both /health ready/model_loaded=true, dashboard200 and actual POST/api/v2/analyze200 on one new neutral smoke input. Startup smoke only, not new benchmark/regression performance evidence. STORE_SUMMARIES=0, offline loading, OMP/MKL4threads. No training, checkpoint/default overwrite, threshold change or production deployment. r05 remains rejected for promotion. State, parent/uvicorn PID and logs: reports/demo/restart_20261103_164006/server_state.json. CIM TCP inventory returned no matching sockets despite working HTTP; PID recorded from owned startup logs. Prior training decisions unchanged.


## CURRENT camping regression follow-up — IN_PROGRESS

User pasted camping30 demo. Existing synthetic references and actual V1.1/r05 API before outputs are frozen in reports/ai_update/camping_context_20261103/. Fix context/target/repeated with general rules; no training, checkpoint/threshold/data changes. Prior DONE states preserved; completion requires paired regression and actual local demo smoke.


## CURRENT camping context follow-up — COMPLETE

Pastedcamping30reproduced at actual V1.1:8020/r05:8021; frozen existing AI references, not human gold. General clause patterns + abuse-endorsement disambiguation + APOLOGY_ACCEPTANCE distinguish accepting apology from self-blame. Contextv3/repeatedv4 qualifies grounded context attacks independently of raw0.41, additive attack_instance_basis. Existing target-v3/legacyengine/lexicon unchanged. Actual after:30/30reference labels bothmodels; exact U04→U03evidence[c09,c12,c15,c18], no apology/recovery added; c18notDEFENSE,c25acceptsapology. All rawscores/legacyfields unchanged.

Full540PASS/1warning, UIbuildPASS, servednewUI/actuallegacy+V2API200. Paired890originalV1cachedscores:1improvement/0newlabelerrors/1eventchange/no newCLEAN-reference evidence. Existing developmenterrors remain documented; no freshblind claim.31protected hashes+all datasets/test/SQLite/V1/V1.1/candidates unchanged. No train/promotion/deploy/auto-hide. Prior DONE and r03/r04/r05promotion rejections preserved.

Current report docs/ai-update/final-report/CAMPING_CONTEXT_RECOVERY.md. Evidence reports/ai_update/camping_context_20261103/; currentownedPIDs in demo_after_server_state.json, older demo PID files superseded. RefreshCtrl+F5 at8020or8021 and reanalyze. No other task started.


Current independent-readiness progress: old30/313 NOT_FOUND; real valid0, collector paused/no network.6source options audited, none admitted as T028. Manual quarantine/UI and same-reviewer Round2 freshness tests pass; leakage boundary expanded toGenZ500+context12. T029 config/data preparation actual11340rows, preflightBLOCKED(real/approval/GPU), no training. Evidence reports/ai_update/independent_readiness_20261103/.


## CURRENT independent-readiness session — safe scopes complete, real criteria BLOCKED

Current task criteria (historical DONE status lines remain untouched):

| Task | Scoped status |
|---|---|
| T022 | DONE — Indirect attack/context development on frozen synthetic references |
| T024 | DONE — Target inference from actual attack clauses and available participant metadata |
| T025 | DONE — Repeated-evidence regression; missing targets still abstain, no promised perfect recall |
| T027 | DONE — Source/inventory audit, paused collector guard, anonymized quarantine and human review preparation |
| T028 | BLOCKED — Independent real200 cohort |
| T029 | BLOCKED — New training |
| T030 | DONE — Synthetic development evaluation tooling and before/after |
| T031 | DONE — Actual local registry/shadow/fallback/rollback mechanics using existing candidate |
| T032 | DONE — 574root/177Social regressions and isolated5process integration E2E |
| T033 | DONE — Provisional technical report with missing evidence explicit |

8safe scopesDONE; T028real/T029trainingBLOCKED. T029preparationDONE, no training. Existing synthetic T028DONE and completed CPU runs remain historical, not real evidence. Data valid0/200/human labels0; old30/313NOT_FOUND;6source options audited/no corpus admitted; collectorPAUSED/0networkrequests/no more contact/path questions.

Synthetic890/known886 only: FP20→18,FN9→6,MacroF1.889700→.909296; target30→34/54correct(P1.0,R.5556→.6296); repeatedTP2→3/10,FP0,FN8→7. No new label errors;18FP/6FN/20targetabstentions/7repeatedmisses remain. No human-gold/real-world claims.

574rootPASS/177SocialPASS,5processfixtureE2E/browserPASS(tempSQLite/cleanup/privacy), real-reviewChromePASS(no submissions), actualregistryshadow/fallback/rollbackPASS(nativeexit0), actualV1.1/r05live5threads/90comments each rawinvariantPASS. Current codecontext-v4/target-v4/repeated-v4; default/V1/0.41/checkpoints/source labels/test/liveDB unchanged.

Files: context_signals.py,target_signals.py,signal_engine.py,contractschema; real_dataset collector/core/store/intake/leakage/review_app/validation/UI; reusable evaluate_synthetic_signals.py, training preflight guards/config, local registry/config, tests/template/docs. Evidence reports/ai_update/independent_readiness_20261103/; report docs/ai-update/final-report/INDEPENDENT_READINESS.md. Current criteria tasks/CURRENT_AI_SCOPE.json. Human UI8010; demo8020V1.1/8021experimentalr05 reloaded code only. Current PID states in this evidence directory; prior PID files superseded.

Next only when real permitted material exists: source/privacy/leakage verification and supported adapter, then same-human Round1/Round2 and evaluation lock. No new training without all prerequisites and explicit approval. No push/deploy/production changes; no other ready requested task remains.


## Synthetic experiment r06 — historical execution timeline (completed below)

Latest attached request authorizes actual free-resource synthetic training separately from blocked real T028/T029 acceptance. Reuse canonical500 without changing original text/AI labels/splits; derive a three-way family view, no real training due unreverified local-copy rights. One new CPU frozen-encoder/full-classifier-head candidate, max4threads/900s/cost0. Different from r05: synthetic-only, class balancing, synthetic validation early stopping, originalV1 base. Real/general training remains disabled; exact r06 config/receipt is the only local exception. Evidence reports/ai_update/synthetic_experiment_r06_20261103/.

r06dataset checkpoint:20/500threads exported, lastbatch20, immutable source text/AI labels reused; schema/globalduplicate/family auditPASS; no new prose or human labels.

r06dataset checkpoint:70/500threads exported, lastbatch50, immutable source text/AI labels reused; schema/globalduplicate/family auditPASS; no new prose or human labels.

r06dataset checkpoint:120/500threads exported, lastbatch50, immutable source text/AI labels reused; schema/globalduplicate/family auditPASS; no new prose or human labels.

r06dataset checkpoint:170/500threads exported, lastbatch50, immutable source text/AI labels reused; schema/globalduplicate/family auditPASS; no new prose or human labels.

r06dataset checkpoint:220/500threads exported, lastbatch50, immutable source text/AI labels reused; schema/globalduplicate/family auditPASS; no new prose or human labels.

r06dataset checkpoint:270/500threads exported, lastbatch50, immutable source text/AI labels reused; schema/globalduplicate/family auditPASS; no new prose or human labels.

r06dataset checkpoint:320/500threads exported, lastbatch50, immutable source text/AI labels reused; schema/globalduplicate/family auditPASS; no new prose or human labels.

r06dataset checkpoint:370/500threads exported, lastbatch50, immutable source text/AI labels reused; schema/globalduplicate/family auditPASS; no new prose or human labels.

r06dataset checkpoint:420/500threads exported, lastbatch50, immutable source text/AI labels reused; schema/globalduplicate/family auditPASS; no new prose or human labels.

r06dataset checkpoint:470/500threads exported, lastbatch50, immutable source text/AI labels reused; schema/globalduplicate/family auditPASS; no new prose or human labels.

r06dataset checkpoint:500/500threads exported, lastbatch30, immutable source text/AI labels reused; schema/globalduplicate/family auditPASS; no new prose or human labels.

R06TRAINING started after60relatedPASS; one explicitly authorized synthetic-only4CPU/900s run, no real training or model/default change. Candidate training_report.json is live progress; do not call complete before actual optimizer/reload evidence.

r06actual training complete:207steps/3epochs/79.75s, encoder unchanged, reloaderror0, selectedepoch3on306syntheticvalidation. Evaluation pending; no activation.


## r06 completed — EXPERIMENTAL, not independent acceptance

5experimental milestonesDONE: reuse/validate500threads(5115comments;CLEAN4667/TOXIC369/UNCERTAIN79), prepare4398synthetic-only rows, actual CPUhead training207steps/3epochs/79.75s, actual V1/r05/r06 comparison, checkpoint/report/progress. No new utterances generated. Encoder frozen; threshold0.41/V1/default/oldcheckpoints/test/SQLite preserved; one-run scope consumed.

Raw MacroF1 validation V1.688581/r05.670259/r06.823834; challenge V1.779884/r05.787645/r06.828798. Validation/challenge already viewed in rule research, synthetic_reference only, not human gold/real-world evidence. R06 challenge FP9/FN5; target9/20correct(P1,R.45), repeatedTP0/FP0/FN5. No claim these errors are solved; no production activation.

Tests: actual full root `python -m pytest -q --basetemp reports/ai_update/test_tmp/r06_final` →591PASS/0FAIL/one deprecation warning. Earlier notebook migration failure fixed and rerun; final_tests.log retains evidence. No changed expected labels. No frontend edits/build. Hash audit integrity.json preserves27historical task statuses and source/model/test hashes.

Files changed: scripts/prepare_t029_training.py, scripts/train_t029_candidate.py, new scripts/synthetic_data/experiment.py, scripts/evaluate_synthetic_candidate.py, tests/test_synthetic_experiment.py, configs/t029_synthetic_only_cpu_r06.json, notebooks/T029_Synthetic_Experimental_R06.ipynb; new datasets/synthetic_genz/ and models/candidates/T029_synthetic_only_head_cpu_20261103_r06/; reports/ai_update/synthetic_experiment_r06_20261103/; task/scope progress and docs/ai-update/final-report/SYNTHETIC_R06_EXPERIMENT.md. Existing runtime AI/backend/frontend unchanged in this experiment.

T028realBLOCKED0/200,humanlabels0; old30/313NOT_FOUND (previous audit). Formal T029/T030 real criteria still BLOCKED; historical DONE preserved. FullGPU notebook prepared/unexecuted. WikimediaPAUSED. Next: review saved results / target-repeated regression or permitted real data plus same-human Round1/Round2; no automatic new train or promotion. Resume context and safe validation commands: reports/ai_update/synthetic_experiment_r06_20261103/README.md; machine state progress.json; current authority tasks/CURRENT_AI_SCOPE.json.


## Repeated recovery follow-up — IN_PROGRESS

Five r06 events traced; frozen original references and before sources captured. Four failures lack context constructions; one root attack lacks grounded target. Regression tests added before runtime changes; no training/default changes, T028 real remains BLOCKED.


## Repeated recovery follow-up — REPEATED_FIX_VERIFIED

Five formerly missed r06 events now recovered with exact reference evidence in focused tests (86PASS); four context families plus bounded reciprocal root exchange. Broad cached890comment replay: no new label errors, FP18 unchanged/FN6to4; recomputed event TP2to8/10, FP0, evidence20/20 correct. Root regression running; no fresh challenge read yet. Historical aggregate counts will be audited against archived outputs before final report.


## Repeated recovery follow-up — T030_SYNTHETIC_VERIFIED

Locked rule challenge12threads/74comments: actual V1/r05/r06 inference, no post-score rule changes, exact/near overlap0. Old challenge repeated0to5/5 (evidence10/10); fresh2to4/6, precision1/recall0.6667, evidence8/8, two misses retained. Raw V1/r05/r06 comparison plus context-only/target-repeated-only/full ablation saved. T028 real and formal acceptance remain unmet.


## Repeated recovery follow-up — T031_LOCAL_VERIFIED

Separate local registry candidate_r06 verified by SHA; actual model shadow and injected candidate-loader failure fall back to V1. Isolated ASGI200->503->200 rollback; exact attack evidence b/d excludes intervention/apology c/e. Implicit candidate selection refused, default unchanged. Production release remains unapproved/dependency BLOCKED.


## Repeated recovery follow-up — T032_SAFE_INTEGRATION_VERIFIED

177Social testsPASS using service own venv (root venv lacked Alembic, retained failure log). Five-process browser E2E PASS on disposable SQLite/accounts: Dashboard/review/appeal/offline/retry/recovery;2actual retry attempts,1resolved synthetic appeal, owned processes cleaned up, log privacyPASS. AI in browser E2E is a fixture, not real-model accuracy; actual r06/V1 ASGI tests recorded separately. No live DB migration/frontend code change.


## Repeated recovery follow-up — T033_IN_PROGRESS

Final locked-source regression610PASS/177SocialPASS/browserE2EPASS/actual registryPASS. Preparing technical report with raw-vs-hybrid comparison, ablations, 2fresh repeated misses, source-label/hash checks and current T028-T033 acceptance table. Historical aggregate note corrected using archived metrics:33/54target and2/10validated events before, not stale34/3 summary; DANCE emission has no grounding reference and is omitted, not counted TP.


## Repeated recovery follow-up — COMPLETE_SAFE_SCOPE


## Current verified follow-up — repeated/context/target v5

T028 BLOCKED(real0/200,humanlabels0); T029 formalBLOCKED(r06 experimental already trained, no r07); T030/T031/T032/T033 PARTIAL (safe synthetic/local work verified; missing independent acceptance, no production authorization). Historical DONE preserved; current scope tasks/CURRENT_AI_SCOPE.json.

Five event regression red5FAIL before fix; old challenge repeated0/5→5/5, evidence10/10correct. Fresh post-freeze12threads/74comments:2/6→4/6, precision1/recall.6667, evidence8/8correct;2misses retained, no post-score rule changes. Canonical500/5115 unchanged. Broad890replay known886 FP18→18/FN6→4; repeated2/10→8/10,FP0,evidence20/20; no new label errors. Old prose34target/3events superseded by archived/recomputed33/54and2/10; DANCE lacks grounding refs and cannot count as TP.

Tests610rootPASS/177SocialPASS/browserfiveprocessE2EPASS; actual r06 shadow/fallbackV1/ASGI200→503→200PASS. Browser uses fixtureAI/disposableSQLite, actual models tested separately. Model/default/V1/0.41/test/SQLite/reference labels unchanged; no training/deploy. Runtime context_signals.py/target_signals.py/signal_engine.py+contract defaults; two new test files, reusable evaluate_repeated_recovery.py,12new fixture JSONs/manifest, isolated registry, real-cohort development exclusions, report/progress/task notes. Full file inventory/hashes in reports/ai_update/repeated_recovery_20261103/ARTIFACTS.json.

Report docs/ai-update/final-report/REPEATED_RECOVERY_V5.md; evidence/reproduction reports/ai_update/repeated_recovery_20261103/README.md. Next: real permitted source/human rounds for acceptance; new predeclared holdout before further rule tuning. Do not train r07, recreate500, change default or call synthetic human gold.



## Stabilization/readiness — TWO_MISSES_AUDITED

Both misses are known coverage/safety limits, no technical bug proven: unseen metaphor and66minute gap beyond30minute root exchange. No rule/label edits, no challenge re-inference; preserve4/6/evidence8/8.


## Stabilization/readiness — T028_TOOLS_VERIFIED

47protocol testsPASS; local Chrome UI readinessPASS with0review submissions/no AI predictions. Same-human Round2 rejects stale Round1 revisions at API lock; no runtime fix needed. Real valid0/200, manual intake quarantine is not an admitted cohort. Manual-source promotion still needs verified source receipt/supported adapter; no labels requested or fabricated.


## Stabilization/readiness — VERSION_AND_EVIDENCE_FROZEN

Frozen r06/ViSoBERT/V1.1/r05, context-v5,target-v5,repeated-v5, manifests/schema/evaluation/E2E/tests in READINESS_LOCK.json(1306hashes). Read-only verifierPASS; no runtime/model modifications. Latest stabilization tests will be attached by separate attestation, never reseal this lock.


## Stabilization/readiness — T028_PROVENANCE_TECHNICAL_FIX_VERIFIED

API empty-source URL reproduced500before fix; min_length1 now returns422before quarantine/key writes.48review testsPASS. Original1306file lock unchanged; new tooling-v2 lock appends5proofs, updates only intake/test hashes. Models/context/target/repeated/data/manifests/evaluations remain unchanged; no new gold or network.


## Stabilization/readiness — T030_AND_T032_FROZEN

T030 V1/r05/r06 raw/ablation/confusion/FPFN/target/repeated reports and T032 API contracts/browserE2E/review/appeal/failure recovery/rollback evidence frozen by1311SHA lock. No new performance inference. Independent real metrics remain BLOCKED. New full root620PASS/0FAIL/one deprecation warning;48review tests included. Prior177Social/browser/actual shadow results preserved and hash-verified, not rerun this stage.


## Stabilization/readiness — FINAL_HANDOFF_COMPLETE


## Stabilization & Evaluation Readiness — DONE safe scope

Two residual repeated events audited: unseen cục_chì metaphor;66minute gap beyond30minute reciprocal window. No technical bug proven; no rule/label changes or re-inference to obtain6/6. Preserve old5/5/fresh4/6(P1,R.667,evidence8/8).

READINESS_LOCK_T028_v2.json seals1311files(model/rule versions, datasets/manifests/reference labels, raw/ablation/confusions/FPFN/target/repeated and integration evidence). Read-only verificationPASS; no resealing. Latest620rootPASS/0FAIL/1warning,48review protocolPASS included; Chrome empty-corpus UIPASS/0submissions/0AI. Prior177Social/browserE2E/actual shadow+rollback preserved and hash-verified, not rerun. Protected259artifacts/V1/default/0.41/test/SQLite unchanged.

T028/T029formalBLOCKED; T030/T031/T032/T033PARTIAL. Technical T032, frozen T030synthetic and provisional T033 handoffDONE; independent acceptance still absent. Real0/200/humanlabels0, collectorPAUSED. Manualintake/anonymization/CSRF/provenance checks and same-humanRound1/Round2 tested; manual inbox still needs verified receipt/supported adapter before source admission. StaleRound2 cannot lock after Round1 revision. Empty-source URL API500 reproduced, one-line min_length1 fix now422/no key/inbox writes; original lock preserved, tooling-v2 lock with SHA lineage. No labels requested/fabricated, no r07/train/deploy/default switch.

Report/checklist/architecture/dataset/training/comparison/error analysis/demo: docs/ai-update/final-report/FINAL_READINESS_REPORT.md. Evidence/reproduction: reports/ai_update/stabilization_20261103/README.md; lock READINESS_LOCK_T028_v2.json, latest-test/report binding READINESS_ATTESTATION.json. New code scripts/verify_ai_readiness_lock.py; scripts/real_dataset/intake.py(min_length1fix); new tests test_ai_readiness_lock.py/test_real_review_lock_readiness.py; AI/Social/frontend/model unchanged. Current authority tasks/CURRENT_AI_SCOPE.json. Next: permitted/source-verifiable real200, privacy/leakage, same-human two rounds and evaluation lock; then predeclared independent evaluation and formal sign-off. No automatic training.



## Fresh10 recovery — IMPORTED_AND_PRIORITY_CAUSES_VERIFIED

Imported10input/10analysis JSONs and original two CSVs verbatim,200comments/195binary/5UNCERTAIN, synthetic_reference not human gold. Replayedv5 exactly: finalTP15/FP6/FN7/TN167,target5/22,repeated2/7. Test09c17 bare khong_co_nghia DEFENSE overrides rawTOXIC; Test10c14 ngò→ngo ATTACK, addressed replyU05. Baseline lockPASS. No code fix yet; proposed changes will be opt-in experiment, frozenv5/default unchanged.


## Fresh10 recovery — DEVELOPMENT_VALIDATED_AND_EXPERIMENT_FROZEN

Opt-inv6: Fresh10TP18/FP1/FN4/TN172,MacroF1.931861,target16/22,repeated6/7,P1/R.8571,evidence15/15precision and15/19coverage; Test03/Test08full evidence. New-label-errors0. Old890regression metrics/target/repeated exactly unchanged. Initial development regressions retained in development_v1, fixed generally before freeze. Nine reference-review notes preserve originallabels. v5/default/readiness unchanged; experiment now frozen before new holdout authoring.


## Fresh10 recovery — POSTFIX_HOLDOUT_EVALUATED

Six new AI-authored threads/48comments afterexperimentfreeze; one actualr06forwardcache, no post-score code changes. Metrics, misses, false alerts and evidence retained verbatim in postfix_holdout_metrics.json. Not human gold/independent real; default and readiness unchanged.


## Fresh10 recovery — REPORT_SCOPE_FIXED_AND_REFROZEN

Two red failures reproduced reporting/assignment bug. 28 targeted tests PASS after generic reporting-scope fix, endorsed/direct quoted attacks retained. Fresh195 remains TP18/FP1/FN4/TN172; old890 metrics unchanged, no new label errors. Original experiment lock/source/48comment first-holdout outputs preserved; first holdout now development, including its new FP. context/target/repeated-v6.1-research refrozen before another small challenge, default-v5/readiness unchanged.


## Fresh10 recovery — VALIDATED_HANDOFF

648 root tests PASS/0FAIL/1deprecation warning; 28 targeted tests included. Fresh10 TP15→18/FP6→1/FN7→4,Macro.830105→.931861,target5→16/22,repeated2→6/7,evidence15/15 correct and15/19 coverage. Old890 regression unchanged. Initial48comment challenge exposed new apology FP, preserved then converted to development; reporting fix now FP1/FN0 there. New post-v6.1-freeze24comment challenge TP5/FP1/FN1/TN17,Macro.888889,target5/6,repeated1/2,P1/R.5,evidence2/2correct, no post-score changes. One metaphor miss and one raw-score FP remain; not human gold/independent real. Readiness1311filesPASS, no model/default/train/deploy. Opt-in research code only; live v5 still unchanged. T028/T029formalBLOCKED,T030–T033PARTIAL. Report docs/ai-update/final-report/FRESH10_RECOVERY.md; new exclusion extension pending a future lock revision.


## Fresh10 local demo — 04/11/2026

RUNNING at http://127.0.0.1:8023/dashboard/; actualr06 + context/target/repeated-v6.1-research, CPUoffline4threads/threshold.41, canonicalapp process-local opt-in binding only. Defaultv5/source/static/checkpoints/readiness unchanged; no training/deploy. Dedicated demo reviewDB, summariesdisabled, internalSocialAPI unavailable. Actual HTTP/UIassets/3thread60comment inference PASS: Test09c17TOXIC→U03,Test10c14CLEAN/noattack,Test07two reciprocalpairs correct. Readiness1311hashesPASS. Browser opened; browserE2E not rerun. Launcher and evidence reports/ai_update/fresh10_demo_20261104/README.md; smoke_result.json. Keep server running for user. FormalT028/T029BLOCKED,T030–T033PARTIAL unchanged.


## NOV10 audit — IMPORTED

NOV10:10inputs/10analysis JSONs, two original reference CSVs and source docs byte-preserved; user aggregate stored separately because no evaluation file was present. Synthetic development only; no reference/model/rule edits.


## NOV10 audit — ROOT_CAUSE_REPLAYED

NOV10 v6.1 cached replay exactly matches all10wire exports/200comments, not a v5 assumption. Per-comment predicate/qualification traces and8event timelines saved. No rule changes. Target/event metrics remain0/22and0/8; detailed audit now available for distinguishing linguistic coverage from runtime problems.


## NOV10 audit — RUNTIME_CONFIRMED_AND_RULES_UNCHANGED

Actual instrumented canonical ASGI r06 probes63comments PASS: Test12/15/20 each calls contextv6.1 exactly20times and scores match exports with maxdiff0. Positive control creates B→A repeated evidence, so pipeline not globally disabled. All7attack predicate families have0hits across NOV10/200comments; target rejects attack_candidatefalse. Eight referencepairs span10–20min but have0instances; no technical fault proven, no redtechnical tests fabricated or rule change. New diagnostic tests26PASS plus priorFresh28PASS; small new challenge will be authored only after frozen hash receipt.


## NOV10 audit — AUDIT_COMPLETE_WITH_OPEN_COVERAGE_AND_QUOTE_BUG

Root677PASS/0FAIL/1warning; actualASGI r06 probes63commentsPASS, exactwire10/10. NOV10 all7attackpredicatefamilies0hits before/aftermasking; targetearlyreturn→0instances→0/8events, not globaldisable/timewindow. NOV10 metrics unchangedTP7/FP3/FN15/TN174,Macro.694160,target0/22. OldFresh10+890regression unchanged. Newpostfreeze24commentchallenge:23binaryTP6/FP1/FN0/TN16,Macro.946387,target5/6,repeated1/2,evidence2/2correct/2of4coverage; found narrativequote scopebug, supplementalred2FAIL/1PASS retained, NOTfixed.24adjudicationcandidates pending, no referencemodification. Explicitversionedoverlay excludes10/10NOV10; defaultlockedloader unchanged. No model/rule/train/default/deploy/readiness changes. AuditDONE; coverage/quoteimplementationOPEN; T028/T029formalBLOCKED,T030–T033PARTIAL. Report docs/ai-update/final-report/NOV10_ROOT_CAUSE_AUDIT.md; resume evidence README, no need to rerun inference.


## Controlled v6.2 — QUOTE_FIXED_AND_ADJUDICATION_PREPARED

Two migrated quote red expectations first2FAIL, nowPASS on separatev6.2; oldv6.1/source/outputs unchanged.18quote/control testsPASS; spansNFD/NFC, assignment outsidequote, attribution, nouncau vs addresseecau and freshattacks afterquote preserved. Quote-only paired replay all7cohorts: no new labelerrors; old/Fresh10/NOV10 metrics unchanged, previouslyseenNOVaudit24 Macro.946387→1.0. Initial nounmask caused2safe-cue regressions, preserved in phase1_quote; fixed by retaining original safe semantics, verified phase1_quote_verified. Phase1source snapshot saved.24adjudication cases exported CSV/HTML with full20commentcontext, empty decisions/reviewer, no humanreview/gold/reference changes. Proceed bounded indirectresearch with negativecontrols before freeze.


## Controlled v6.2 — INDIRECT_CONTROLS_VERIFIED_AND_V62_FROZEN

Separatev6.2 quote fixes/control expectationsPASS;45targeted tests incl43processor/2adjudicationPASS.7developmentcohorts no new labelerrors. NOV10 Macro.694160→.719137,target0→2/22,repeated0→1/8; Fresh10/old890 unchanged. Otherseen challenge gains retained; no reference edits. Initial nounmask/safe-cue and content-view failures fixed and archived before freeze. HTMLv1JS escape failure retained; adjudication_v2 parse/emptyexportPASS,24fullcontexts/blankownerdecisions/nohumanlabels. V62_LOCK now freezes code/tests/model/reference/readiness before authoring a new challenge. Default/runtime/V1/r06/0.41 unchanged; no training/deploy.


## Controlled v6.2 — POSTFREEZE_CHALLENGE_SCORED_ONCE

New6threads/36comments authored after V62_LOCK, source references and manifests frozen before actualr06 CPUoffline scoring. First-pass classification/target/repeated/FPFN/evidence results retained; no post-score rule or label changes. Same-author synthetic only, not human gold/independent real. See postfreeze_challenge/first_pass_metrics.json; review all failures before conclusions.


## Controlled v6.2 — STABILIZED_EXPERIMENTAL_NO_PROMOTION

722standardrootPASS/0FAIL/1deprecationwarning; v6.2 originalquote expectationsPASS while sealedv6.1 historicalred behavior retained.45targeted testsPASS incl43processor/2adjudication; finaltimestampedannotationexport2testsPASS,24ownerdecisions/reviewer fieldsblank/nohumanreview. Frozen36commentchallenge v6.1→v6.2 Macro.731744→.911330,TP3→6,FP0→0,FN5→2,TN28→28,target1→6/8,repeated0→2/3,P1/R.667,evidence4/4correct and4/6coverage; two unseen metaphor/exclusion misses retained, no post-score edits. NOV10 Macro.694160→.719137,target0→2/22,repeated0→1/8,evidence2/2correct but2/21coverage; Fresh10/old890 unchanged. Source/reference/default/readiness1311SHA remain unchanged;6newseen challenge threads +NOV10 verified excluded by explicitversionedoverlay, defaultloader unchanged. No modeltraining/defaultactivation/deploy; T028/T029BLOCKED,T030–T033PARTIAL. All remaining FP/FN/ambiguous references/emitted target/evidence errors saved. Latest owner review artifact adjudication_v3/NOV10_ADJUDICATION.html.


## Controlled v6.2 — HANDOFF_COMPLETE_EXPERIMENTAL

All5authorized safe phases complete with documented remainingmisses and no formal task promotion.722rootPASS, samequoteassertionsPASS on v6.2 (sealedv6.1 untouched), originalsource/reference/model/readiness SHAverified. Owner adjudication prepared24fullcontexts/blankdecisions in adjudication_v3; no humanlabels/gold created. Locked36commentchallenge scoredonce, no rule/test editsafterfreeze;2FN/1missedevent retained. Report docs/ai-update/final-report/CONTROLLED_V62_RESEARCH.md; changelog/lock/errors/exclusion/preflight/inventory/reproduction in evidence directory. RemainT028/T029BLOCKED,T030–T033PARTIAL; no default/Dashboard/model/training/deploy changes.


## T034–T043 — MERGE_COMPLETE

Verified source pack13SHA entries, imported10tasks with20implementation fields, commonrules/dependencies/acceptance/execution/resume files created; sourcepack/27historicalstates preserved. Current tasks allNOT_STARTED, nextT034 actualarchitecture/contracts; no implementation claimed. Git metadata absent. Canonical architecture audited: SocialAPI auth/content/schema0004/durableworker/review/appeal, AIdefaultV1.1/.41/v5, Social/AdminReact, source/dataset/training/registry tooling. New user authorizes safe local tasks incl gated T041CPU smoke; no r07/paid/private/default/deploy. Evidence reports/task_rollout_20261104/.


## T034 — IN_PROGRESS

Architecture/contracts drafted from audited canonical services; schema/status/revision tests running, no model/DB/default changes.

Evidence: 


## T034 — DONE_VERIFIED

Architecture/sequence/transport ADR/contracts/budgets/failure+compatibility plan complete. SSE authenticated fetch chosen over extraWebSocket; public-post+membership visibility preserved.13contract testsPASS including malformed identity/time, privacy fields, ordering/stale versions; no runtime/model/DB changes.

Evidence: docs/realtime_moderation/ARCHITECTURE.md, contracts/realtime_event.schema.json, reports/task_rollout_20261104/T034_tests_final.log


## T035 — IN_PROGRESS

Implement additive canonical-app live routes, engine-scoped transactional event hooks and opt-in worker wrapper. Reuse frozen content/idempotency/jobs/retry/review; explicit extension schema on disposableDB only.

Evidence: 


## T035 — DONE_VERIFIED

Additive canonical Social extension implemented: explicit membership+postvisibility, existing idempotent comment/job transaction, atomic durable minimal events, auth SSE/poll/replay, worker hooks/retry/restart/stale handling.26newcontract/integration testsPASS; fullSocial203PASS/1deprecationwarning. Initial2failures retained: bulkSQL stale invalidation event gap fixed; expiryfixture corrected to satisfy existingDBconstraint. SQLite rollback/deactivation/concurrentPOST/privacy verified; AIresponses are unitfixtures, not claimed realmodel. Base0004/source/readiness1311SHA remain unchanged.

Evidence: services/social-api/src/shieldvi_social/live_app.py, services/social-api/src/shieldvi_social/live_store.py, services/social-api/src/shieldvi_social/live_routes.py, reports/task_rollout_20261104/T035_social_regression.log, docs/realtime_moderation/RUN_LOCAL.md


## T036 — IN_PROGRESS

Implement additive authenticated incremental AI adapter using approved default-v5, bounded model/text score cache, typed context/target/attack-instance evidence and context-dependency stale guard in existing worker. No v6.1/v6.2 default activation.

Evidence: 


## T036 — DONE_VERIFIED

Additive default-v5 incremental adapter/client implemented; per-model/text LRU raw cache, typed context/target/instances/evidence,1800s horizon and worker snapshot dependency CAS. Explicit live-provenance-v1 subtractive report/quote gate preserves base-v5 flags/raw/assessment, prevents inherited pure-apology instanceFP; fresh outsidequote attack retained.15AIunit+4worker testsPASS, full737root/207SocialPASS. Actual approveddefaultV1.1 CPU2threads smoke6→3neuraltexts, scoresinvariant, grounded[b,c]; measured274.6676→222.9778ms(single sample). Original apps/weights/default/0.41/readiness baseline untouched; experimental selector rejected by liveclient.

Evidence: docs/realtime_moderation/INCREMENTAL_AI.md, contracts/live_moderation_response.schema.json, reports/task_rollout_20261104/T036_actual_benchmark.json, reports/task_rollout_20261104/T036_root_regression.log, reports/task_rollout_20261104/T036_social_regression.log


## T037 — IN_PROGRESS

Build additive live.html React entry in existing social-web using current auth/content APIs and authorized fetchSSE, original pages/build outputs untouched. Need two independent Chrome sessions and reconnect/offline/stale/privacy evidence.

Evidence: 


## T037 — DONE_VERIFIED

12 real Chrome two-client workflow checks PASS with temporary SQLite, authenticated SSE, actual default-v5 rules and explicitly non-neural raw fixture. Includes offline reconnect regression fixed via snapshot retry, AI503 recovery, idempotent lost ACK, edit/delete, reload, XSS and RBAC. Dedicated production build PASS. Actual neural incremental timing is separately retained under T036.

Evidence: apps/social-web/src/live.jsx, reports/task_rollout_20261104/T037_browser_result.json, reports/task_rollout_20261104/T037_build_final.log, reports/task_rollout_20261104/T037_cleanup.json


## T038 — IN_PROGRESS

Reusing existing ReviewDetail, staff RBAC/manual audit/appeals; building isolated live moderator entrypoint.

Evidence: 


## T038 — DONE_VERIFIED

33 related backend tests PASS; 8 Chrome E2E checks PASS in three authenticated contexts: same actor-target repeated evidence, preserved moderator draft, manual hide, author appeal, restore, audit and clarification. Source/rules/model defaults unchanged. Old dashboard retained. Dedicated build PASS. Search/thread/risk/time filters explicitly page-scoped; Studio trainer maps to existing admin, no role migration.

Evidence: docs/realtime_moderation/MODERATOR_LIVE.md, reports/task_rollout_20261104/T038_browser_result.json, reports/task_rollout_20261104/T038_backend_tests_fixed.log, reports/task_rollout_20261104/T038_build_final.log


## T039 — IN_PROGRESS

Implementing bounded immutable imports, provenance quarantine, dataset versions and exact/near leakage checks, reusing real_dataset utilities and admin RBAC.

Evidence: 


## T039 — DONE_VERIFIED

17 related backend tests PASS and 6 real Chrome Studio checks PASS; immutable UTF8 CSV/JSON/JSONL imports, mapping, preview/export, rights/PII/formula quarantine, pinned exact/near leakage audit, duplicate replay, explicit lineage and thread splits. Dedicated build PASS. ZIP unsupported and rejected; real source verification remains manual and quarantined; no human gold or training claimed.

Evidence: docs/ml_studio/DATASETS.md, reports/task_rollout_20261104/T039_backend_final.log, reports/task_rollout_20261104/T039_browser_result.json, reports/task_rollout_20261104/T039_build.log


## T040 — IN_PROGRESS

Reusing solo ReviewStore for blind two-round annotation, CAS, same authenticated reviewer, stale-Round2 invalidation and immutable synthetic-reference exports.

Evidence: 


## T040 — DONE_VERIFIED

20 related backend tests PASS; 6 Chrome annotation workflow checks PASS after fixing verified navigation race. Blind context, autosave CAS, same reviewer two rounds, stale R2 invalidation, append-only history and immutable child snapshots verified. Synthetic browser entries remain reference, not human gold. Real-review minimum gap300seconds and source quarantine remain enforced. Dedicated build PASS.

Evidence: docs/ml_studio/ANNOTATION.md, reports/task_rollout_20261104/T040_backend_fixed.log, reports/task_rollout_20261104/T040_browser_result.json, reports/task_rollout_20261104/T040_build.log


## T041 — IN_PROGRESS

Implementing durable isolated CPU head-only training, bounded config, dataset/model SHA preflight and cancellation; current user specifically authorizes one eligible synthetic smoke, not r07/default promotion.

Evidence: 


## T041 — DONE_VERIFIED

7 backend tests PASS, 6 real Chrome checks PASS and build PASS. Actual retained synthetic-only V1 frozen-encoder CPU-head run:18threads/36comments, train22/validation10/test4,1epoch/3optimizersteps,2threads,trainer3.36s,reloaderror0.0,base/encoder/sources unchanged. Tiny synthetic validation Macro-F1=1.0 is workflow evidence only. Durable queued/running/cancel/crash/restart guards tested; no model/default/threshold/lock mutation. Training authorization for this smoke consumed; do not automatically rerun it during final regression.

Evidence: docs/ml_studio/TRAINING.md, reports/task_rollout_20261104/T041_backend_service_final.log, reports/task_rollout_20261104/T041_browser_result.json, reports/task_rollout_20261104/T041_retained.json, reports/task_rollout_20261104/T041_run_manifest.json


## T042 — IN_PROGRESS

Preparing paired synthetic locked-holdout evaluation and hashed local registry/shadow/rollback without activation; reuse retained actual T041 candidate, no new training.

Evidence: 


## T042 — DONE_VERIFIED

4 backend guard tests PASS,5 Chrome checks PASS and build PASS. Actual paired V1/r06/T041 inference on same4 locked synthetic holdout comments; raw/final confusion/P/R/F1 reported separately, error exports and hashes retained. Target/repeated/evidence reference denominators absent on this cohort: null, not invented. Actual fault-injected local shadow fallback to V1+neural probes PASS. Promotion denied server-side, v1_1 default unchanged; no training.

Evidence: docs/ml_studio/EVALUATION.md, reports/task_rollout_20261104/T042_browser_result.json, reports/task_rollout_20261104/T042_evaluation.json, reports/task_rollout_20261104/T042_backend_tests.log, reports/task_rollout_20261104/T042_build.log


## T043 — IN_PROGRESS

Running broad regression, read-only readiness verification and real approved-default neural HTTP/browser workflow; preparing reproducible Windows demo/start-stop and final acceptance/evidence report.

Evidence: 


## T043 — DONE_VERIFIED

Final737AI/root+244Social Python tests PASS/0FAIL (one deprecation warning per suite),4frontend transport tests PASS,original and opt-in builds PASS. Actual approved-default V1.1 neural HTTP/worker/SQLite E2E:8checks/3contexts PASS; four-context auto-login/Studio tabs/Windows stop script PASS. Enqueue SQL/ACK/queue/inference/fanout measured on4synthetic messages; tiny local sample, not SLO.1311 readiness files and13source-pack entries unchanged;27historical statuses preserved. Five canonical handoff guides/report complete. No extra training, promotion, deploy or production changes.

Evidence: docs/ai-update/final-report/T034_T043_FINAL_REPORT.md, docs/ai-update/final-report/REALTIME_DEMO_GUIDE.md, reports/task_rollout_20261104/T043_root_regression.log, reports/task_rollout_20261104/T043_social_final.log, reports/task_rollout_20261104/T043_transport_tests.log, reports/task_rollout_20261104/T043_browser_result.json, reports/task_rollout_20261104/T043_interactive_check.json, reports/task_rollout_20261104/T043_performance.json, reports/task_rollout_20261104/T043_readiness_final.log


## T034?T043 final handoff

10 DONE_VERIFIED local tasks; no new task BLOCKED/WAITING_APPROVAL. FormalT028/T029 BLOCKED and T030?T033 PARTIAL unchanged. Final737root+244Social+4transport PASS/0FAIL; read-only readiness1311PASS. One actual synthetic CPU-head smoke retained, no further automatic training. Next: operator demo/review; later permitted real intake/privacy/solo R1/R2 and formal evaluation. Commands/resume: AUTO_RESUME_T034_T043.md. Final report docs/ai-update/final-report/T034_T043_FINAL_REPORT.md; SHA inventory reports/task_rollout_20261104/ARTIFACTS.json.


## T043 demo startup follow-up ? VERIFIED

User log ended in KeyboardInterrupt. Latest interrupted demo demo_482f0f3de007f13d had only one owned Social process and empty API startup log; no evidence of model failure. Added flushed stage/wait progress, monotonic90second readiness deadline, service/exit/log diagnostics, direct loopback HTTP without environment proxies, readable model/browser failure and clean Ctrl+C handling.

Validation:3pytest startup tests PASS (DEMO_STARTUP_FIX_tests.log); actual four-context auto-login/Studio/stop smoke PASS with real default model (DEMO_STARTUP_FIX_e2e.log; demo_9f5f32d579c29855/interactive_check.json). AI readiness21.5s in this run. Injected KeyboardInterrupt at first HTTP readiness wait PASS: no traceback, owned Social process stopped (DEMO_STARTUP_FIX_interrupt.json). No training, checkpoint/default/threshold or production DB changes; confirmed task states unchanged. Source/evidence SHA revision: DEMO_STARTUP_FIX_20261104.json; original ARTIFACTS.json remains the previous handoff snapshot.


## Documentation consolidation — 04/11/2026

Đã gom 38 tài liệu vào docs/, gộp ghi chú frontend compatibility và bỏ trang demo
chỉ trỏ tới guide hiện hành. Điểm vào: docs/README.md; bản đồ: docs/ORGANIZATION.md.
Root chỉ giữ README dẫn mục lục và AGENTS cho công cụ. Task/skill và metadata
license/dataset/model giữ đúng vị trí. Không đổi runtime, model, dataset hay DB.

Kiểm tra: toàn bộ liên kết và đường dẫn cũ trong tài liệu, metadata skill,
checksum 62 bản gốc trong hai ZIP, trùng nội dung và 37 trạng thái task; readiness
verifier PASS 1311 file, lock không sửa/reseal. Không chạy frontend build hoặc
training vì chỉ đổi tài liệu. Lệnh/evidence: reports/docs_cleanup_20261104/
validate_docs.py, VALIDATION.json, readiness.log và FILES_SHA256.json. Manifest
SHA cũ là lịch sử trước di chuyển; bản đồ/hash đợt này lưu riêng.

## T043 demo schema startup follow-up — 04/11/2026 VERIFIED

User session demo_7eb09180784a6b87 stopped during database preparation:
SQLite exists, cleanup owned_count=0, no service logs. Evidence shows operator
interruption before service launch, not a verified model or migration error.
The two schema subprocess calls lacked progress, persistent logs and deadlines.
Launcher now reports Base/Live schema separately, retains stdout/stderr in named
logs, bounds each step to90seconds and stops owned processes on timeout/Ctrl+C.
No production DB, model, threshold or training changes; task statuses unchanged.

Verification:7 startup tests PASS (real child success/error/timeout/cancellation
plus HTTP deadline/proxy checks). Actual InteractiveCheck PASS with4 automatic
browser logins and stop script, retained root demo_7f5a4490a6d17280. Base schema
1.2s, Live schema1.1s, AI28.6s. Readiness verifier1311PASS, original lockSHA
unchanged. Evidence: reports/task_rollout_20261104/DEMO_SCHEMA_FIX_tests.log,
DEMO_SCHEMA_FIX_e2e.log, DEMO_SCHEMA_FIX_readiness.log and
DEMO_SCHEMA_FIX_20261104.json. Next: operator reruns demo launcher and waits
for DEMO_READY without Ctrl+C during startup.

## T034 Social Feed v2 — IN_PROGRESS, 04/11/2026

Verified and merged the new source pack; audit Social Feed gaps before runtime changes.

Evidence: reports/social_feed_v2_20261104/MERGE_MANIFEST.json

## T034 Social Feed v2 — DONE_VERIFIED, 04/11/2026

Audited actual post/comment APIs, authenticated SSE, worker/context, Studio and Social Feed UI gaps. Added transport ADR, state mapping, RBAC and acceptance trace.13 contract tests PASS; original model/readiness/runtime untouched.

Evidence: docs/realtime_moderation/REPO_AUDIT.md, reports/social_feed_v2_20261104/T034_contract.log

## T035 Social Feed v2 — IN_PROGRESS, 04/11/2026

Verify durable post/comment/reply and five authenticated demo accounts using disposable SQLite; reuse canonical transaction and worker.

Evidence: 

## T035 Social Feed v2 — DONE_VERIFIED, 04/11/2026

14 actual temporary-SQLite tests PASS, including five authenticated actors creating a post and comments/reply with one durable job each, publication privacy, same-key races, replay and RBAC. Demo seeds five normal accounts plus staff; canonical API reused.

Evidence: services/social-api/tests/test_live_api.py, reports/social_feed_v2_20261104/T035_backend.log

## T036 Social Feed v2 — IN_PROGRESS, 04/11/2026

Verify post/parent context and existing target/repeated, stale snapshot and approved processor guards; no model/rule edits.

Evidence: 

## T036 Social Feed v2 — DONE_VERIFIED, 04/11/2026

5 Social worker tests and15 incremental analyzer tests PASS. Explicit new test verifies post text, parent chain and current reply in AI payload without account names/email; existing stale/forged-target/experimental-processor guards pass. No model or rule changes.

Evidence: reports/social_feed_v2_20261104/T036_worker.log, reports/social_feed_v2_20261104/T036_incremental.log

## T037 Social Feed v2 — IN_PROGRESS, 04/11/2026

Implement Social Feed entry, post cards/composer, automatic public-feed refresh, comment metadata and five-session browser verification.

Evidence: 

## T037 Social Feed v2 — DONE_VERIFIED, 04/11/2026

Social Feed/cards/post composer and serialized public-feed refresh implemented; reply context/metadata rendered, post retries reuse idempotency key. Build PASS. Actual seven-context Chrome check PASS: five authenticated users discover a new post, comment/reply, receive AI/repeated and manual review/appeal updates without reload/duplicates. Two failed attempts retained (initial send timeout; Windows Proactor accept WinError64 on retry); demo-only Selector loop passed.

Evidence: apps/social-web/src/live.jsx, reports/social_feed_v2_20261104/T037_build.log, reports/social_feed_v2_20261104/T037_feed_e2e.log, reports/social_feed_v2_20261104/T037_feed_e2e_retry1.log, reports/social_feed_v2_20261104/T037_feed_e2e_retry2.log, reports/task_rollout_20261104/demo_5a35dbbdda80d3dc/social_feed_result.json

## T038 Social Feed v2 — IN_PROGRESS, 04/11/2026

Reusing verified moderator live review/appeal; add durable post/comment deep links and verify reauthentication, exact evidence and role checks.

Evidence: 

## T038 Social Feed v2 — DONE_VERIFIED, 04/11/2026

Added authenticated moderator deep links and exact comment context restoration after login.22 related backend tests PASS, Moderator build PASS, actual seven-context Chrome9checks PASS including five actors, repeated evidence, manual hide/appeal/restore, deep-link reauth, reconnect, XSS and >30comment thread. All owned demo processes stopped.

Evidence: reports/social_feed_v2_20261104/live_regression.log, reports/social_feed_v2_20261104/T038_build.log, reports/social_feed_v2_20261104/T038_feed_e2e.log, reports/task_rollout_20261104/demo_1a59f364c7adc9e5/social_feed_result.json

## T039 Social Feed v2 — IN_PROGRESS, 04/11/2026

Revalidate existing immutable Dataset Center imports, rights/PII/leakage guards and actual browser upload/export without duplicating implementation.

Evidence: 

## T039 Social Feed v2 — DONE_VERIFIED, 04/11/2026

Reused existing Dataset Center;14 validator/API tests PASS and6 actual Chrome upload/mapping/preview/export/idempotency/rejection checks PASS on a fresh synthetic-only Studio. No source rights or human gold fabricated.

Evidence: reports/social_feed_v2_20261104/T039_backend.log, reports\task_rollout_20261104\demo_6a5b68a80812e8d6\T039_browser_result.json

## T040 Social Feed v2 — IN_PROGRESS, 04/11/2026

Revalidate solo Round1/Round2, history, derived immutable snapshots and stale Round2 invalidation. Browser automation labels only synthetic test entries.

Evidence: 

## T040 Social Feed v2 — DONE_VERIFIED, 04/11/2026

6 annotation backend tests and6 actual Chrome tests PASS: full context, one authenticated reviewer, two rounds, autosave/history, immutable child snapshot and stale Round2 export rejection. Automated synthetic test annotations are not human gold.

Evidence: reports/social_feed_v2_20261104/T040_backend.log, reports\task_rollout_20261104\demo_6a5b68a80812e8d6\T040_browser_result.json

## T041 Social Feed v2 — IN_PROGRESS, 04/11/2026

Reverify retained actual head-only CPU smoke/candidate and concurrent Social ACK evidence; rerun lifecycle/resource/preflight guards without redundant training.

Evidence: 

## T041 Social Feed v2 — DONE_VERIFIED, 04/11/2026

7 guard/lifecycle tests PASS. Retained actual CPU frozen-encoder smoke/checkpoint/source SHA reverified (not rerun), including authenticated UI execution and47ms Social ACK during that actual training. Candidate remains experimental, threshold.41; no new training authorized/needed for existing receipt.

Evidence: reports/social_feed_v2_20261104/T041_backend.log, reports/social_feed_v2_20261104/T041_receipt_reverified.json, reports/task_rollout_20261104/T041_browser_result.json, reports/task_rollout_20261104/T041_concurrency.json

## T042 Social Feed v2 — IN_PROGRESS, 04/11/2026

Verify existing paired V1/r06/T041 evaluation hashes and recompute confusion/Macro-F1; rerun registry and no-promotion guards without training.

Evidence: 

## T042 Social Feed v2 — DONE_VERIFIED, 04/11/2026

4 registry/evaluation guards PASS. Historical actual paired inference on the same4 synthetic holdout comments reverified against registry/model/dataset SHA; confusion counts and Macro-F1 recalculated. Target/repeated reference denominators remain absent/null. No claim of new inference or real-world evaluation; default/no-promotion gates unchanged.

Evidence: reports/social_feed_v2_20261104/T042_backend.log, reports/social_feed_v2_20261104/T042_report_reverified.json, reports/task_rollout_20261104/T042_evaluation.json

## T043 Social Feed v2 — IN_PROGRESS, 04/11/2026

Run full regression and final actual five-account Social Feed/Moderator E2E including owned AI stop/restart/retry. Prepare current demo/acceptance report and integrity checkpoint.

Evidence: 

## T043 Social Feed v2 — DONE_VERIFIED, 04/11/2026

Final744root/startup+247Social Python tests PASS,4transport tests PASS, both UI builds PASS. SSE scheduling RED→GREEN and full10-check7-context Social Feed/AI offline-recovery E2E PASS; original8-check3-context actual neural E2E PASS. All owned processes stopped;1311readiness files unchanged. Retained actual training/evaluation receipts reverified, not rerun. No production/default/training changes.

Evidence: docs/realtime_moderation/SOCIAL_FEED_V2_ACCEPTANCE.md, reports/social_feed_v2_20261104/root_regression_utf8.log, reports/social_feed_v2_20261104/social_regression_sse_final.log, reports/social_feed_v2_20261104/T043_sse_red.log, reports/social_feed_v2_20261104/T043_sse_green.log, reports/social_feed_v2_20261104/T043_feed_e2e_sse_fix.log, reports/social_feed_v2_20261104/T043_original_e2e.log

## T043 startup diagnosis - 05/11/2026

Reported demo_58665ca349fb9d4a received Ctrl+C about2seconds after Social API launch; API log empty, no verified startup exception. Fresh InteractiveCheck PASS: Social2.5s, AI8.1s,7auto-login contexts and stop script; all10owned subprocesses stopped. No runtime source/model/training/production change, task states retained. Evidence: reports/demo_startup_20261105_check.log, reports/demo_startup_20261105_verified.json and reports/task_rollout_20261104/demo_2c9eb13b081ee26e/interactive_check.json. User should wait for DEMO_READY without interrupting; origin of the reported cancellation is unverified.


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


## T037 comment composer discoverability - 05/11/2026

User opened the correct live URL but could not see a composer after selecting
Xem bai va binh luan. Read-only active-demo audit found published posts and no
comment POSTs. Browser RED reproduced textarea outside viewport (ratio0).
Live UI now scrolls selected detail into view and focuses the composer after
snapshot load, including reopening the same post. Explicit label/id avoids
nested textarea content changing the accessible label after typing. Background
updates neither steal focus nor clear draft text. No API permission/policy change.

Actual Chrome5checks PASS: viewport/focus, comment persistence+real approved
AI analysis, same-post refocus, draft/focus retention, mobile viewport. Initial
red and first follow-up failure retained; final unchanged expectations PASS.
Social build PASS;1311readiness PASS. Test DB/processes isolated and stopped;
user demo_4851e8216db58367/pointer retained, no default/model/train/production
changes or task-status overwrite. Reload the existing tab once; no demo restart
needed. Evidence: reports/demo_comment_ux_20261105_red.log,
demo_comment_ux_20261105_green.log, demo_comment_ux_20261105_green2.log,
demo_comment_ux_20261105_build_final.log, demo_comment_ux_20261105_readiness.log,
demo_comment_ux_20261105_verified.json; all under reports/.


## T037 clickable composer and short-screen layout - 05/11/2026

Screenshot showed the Vi?t b?nh lu?n heading mistaken for a button and the
actual textarea below the viewport. Red Chrome probe verified that no button
with that name existed. Replaced heading with a real type=button/focus action,
moved composer immediately below post and above comments/pagination, added
placeholder/styling, and replaced competing smooth scrolls with a single
instant composer focus path. Reply also focuses composer; no auto-submit or
API/model/policy change. Existing expectations retained and strengthened to
require full textarea and submit visibility on1060x480viewport.

Actual Chrome7checks PASS: real write button, short-screen full visibility,
composer before pagination, post selection/same-post focus, persisted comment
with approved neural worker, draft/no-focus-steal and mobile. Social build
PASS;1311readiness PASS. Active user demo_8d1daf6059b99b03 retained, no user DB
mutation or demo stop. Original task statuses unchanged. Evidence:
reports/demo_comment_button_20261105_red.log,
reports/demo_comment_button_20261105_green.log,
reports/demo_comment_button_20261105_build.log,
reports/demo_comment_button_20261105_readiness.log,
reports/demo_comment_button_20261105_verified.json.


## T037 compact feed visual polish - 05/11/2026

Polished only the opt-in Social feed: compact post cards, initial avatars,
author/time grouping, post-count badge, small icon action, selected-post badge
and aria-current, responsive spacing and pagination only when needed. Kept
pseudonymous author IDs, authorization, polling/SSE, comment workflow and
backend/model/policy unchanged. No new styling-only unit tests.

Existing7actual Chrome comment checks PASS after styling; desktop1366x900 and
mobile390x780 screenshots inspected. Social build PASS in a new output folder.
Test DB/processes isolated and cleaned; live user demo_8d1daf6059b99b03 retained.
No model/training/dataset/production change or task-status overwrite. Refresh
current browser tab to see updated styling. Evidence:
reports/demo_feed_style_20261105_browser.log,
reports/demo_feed_style_20261105_build.log,
reports/demo_feed_style_20261105_verified.json;
screenshots reports/task_rollout_20261104/demo_b0a88f0856199726/feed_desktop.png
and comment_ux.png in the same directory.


## Live usernames and structured reply tags - 05/11/2026

Added opt-in live_identity metadata/schema and authenticated /api/live/feed;
message ACKs and snapshots expose server-derived author_username plus readable
parent reply_to_user_id/username. Permissions filter content before resolving
handles; hidden parent identity remains null, client identity spoofing rejected.
Core V1 APIs/schemas, worker snapshot/hash logic, AI inputs/rules/model/threshold
and readiness lock untouched. No DB migration or rewriting historical text.

Social feed/post/comments display usernames, Reply shows an @username chip
and original parent excerpt; saved comments name the reply recipient. Chip is
presentation over parent_id, not text inserted into authored body, and is not
an attack verdict. Moderator context and actor-target evidence show names while
retaining canonical IDs. Plain typed handles without Reply create no parent link.

Validation:254Social tests PASS (26related included),15incremental AI tests
PASS,4actual Chrome control groups/3sessions PASS, both frontend builds PASS,
1311readiness files PASS. Actual default neural results: clean reply recipient
correct with no target/instance;2direct attacks Bob-to-Alice correctly grounded;
repeated pair/evidence correct and clean reply excluded. Synthetic controls,
not human-gold quality evaluation. Screenshots inspected for Social identity.

Active user demo_8d1daf6059b99b03 was preserved/read-only, never restarted.
Backend currently running uses old loaded routes: operator must stop/relaunch
demo to load names API. UI falls back on404 during that interval. A normal
relaunch creates a fresh demo DB/accounts; old session data/logs stay in their
original report directory, not reset/deleted. No training/default/production
change or task-status overwrite. Evidence: reports/demo_identity_20261105_*.log,
reports/demo_identity_20261105_ai_verified.json,
reports/demo_identity_20261105_verified.json and demo_531e30a5c4f2f43f/ actual
browser/AI evidence under reports/task_rollout_20261104/.


## T038 staff quick conversation JSON testing - 05/11/2026

Added Test AI bang JSON tab beside live queue in Admin: paste/import/sample,
background progress/cancel, per-comment raw score vs assessment/context/lexicon/
policy/reply/target, repeated evidence, and JSON download. Hidden live queue
keeps SSE/state; editor survives tab switches. New owner-private staff-only
transient jobs call existing LiveAIClient/default-v5 with unchanged model/0.41.
No frontend service key, core API rewrite, content/dataset/gold-label writes or
training. Input contract caps50comments/128KiB/64000text chars; parent/time/ID
validation, one running job,120second run budget,15second max AI read timeout,
4MiB results,16recent jobs/30minute memory retention. Offline => FAILED, never
fake CLEAN; cancellation cooperative. Shutdown signals active jobs to stop.

Validation:11new backend tests PASS, full265Social tests PASS/1existing warning,
5actual Chrome checks PASS, Admin build PASS, readiness1311PASS. Actual default
neural sample5comments: c02 clean reply/no instance, c03/c05 directed at U01,
c04 intervention/no instance, repeated U02-to-U01 evidence c03/c05. Manual test
controls are not human gold or independent evaluation. Actual test DB still
contains only starter1post/0comments/1job/1result; no quick-test content persisted.
Desktop screenshot inspected; mobile screenshot saved. Active user demo and
pointer retained; test processes stopped. No deploy, model/default/checkpoint
or threshold change. Restart demo required for new Python routes; normal launch
creates a new session while original demo data stays in its report directory.

Evidence: reports/demo_quick_json_20261105_backend.log,
reports/demo_quick_json_20261105_social_regression.log,
reports/demo_quick_json_20261105_browser.log,
reports/demo_quick_json_20261105_build.log,
reports/demo_quick_json_20261105_readiness.log,
reports/demo_quick_json_20261105_verified.json;
actual screenshots/export under reports/task_rollout_20261104/demo_122a69ae101a68d2/.
Resume: Admin live.html -> Test AI bang JSON -> Nap JSON mau -> Phan tich hoi thoai.

## Responsive UI/UX request — 05/11/2026 — IN_PROGRESS

Scope: opt-in Social Live, Moderator Live/JSON and ML Studio. Read AGENTS,
README, T034–T043 and frontend/admin skills. React/Vite/CSS audited; frozen
legacy entrypoints excluded from edits by readiness lock. No API/business/model
or reference changes. Baseline120 measurements/5overflows retained in
demo_77a6b5d6c9fe3d7b. First responsive run132layout +9workflow checks PASS;
final charts/confirmation/realtime regression verification pending. Build both
apps PASS; transport4PASS; readiness1311PASS. Active user demo retained.
Report: docs/realtime_moderation/RESPONSIVE_UI_REPORT.md. Historical task states
and evidence remain unchanged; no new training authorized or executed.


## Responsive UI/UX — 05/11/2026 — DONE_VERIFIED (Live/Studio scope)

Final evidence supersedes the IN_PROGRESS checkpoint above. Optimized Social
login/feed/create/detail/account/comment/reply, Moderator queue/review/JSON,
Dataset/Annotation/Training/Evaluation Studio using shared tokens and native
controls. 44px touch targets, bounded reply indentation/expandable parent context,
mobile navigation/cards, desktop rails/panels, draft retention, hide/delete
confirmation and metrics-derived charts. No new dependency or framework rewrite.

Before:120layout checks,5overflow cases (evaluation320/360/375/390,moderator820).
Final:144/144layout +13responsive workflows PASS at12viewports,0overflow,
0undersized enabled measured controls,0page errors;60after screenshots saved.
Existing actual-backend browser regressions24PASS (composer7,identity4,JSON5,
hide/appeal/restore/audit8); startup13PASS; shared transport4PASS; both frontend
builds PASS; readiness1311PASS. No full backend-suite rerun claimed for CSS/UI.
T043 browser test explicitly accepts the newly required hide confirmation;
all original visibility/appeal/evidence assertions remain unchanged.

Training progress/charts/logs verified with browser-only named fixture: no
training/evaluation start or worker. Synthetic upload/annotation test artifacts
remain separate from datasets and human gold. Active demo_85046f8406365373/PID6456
and its DB/pointer retained. No API/business/model/default/0.41/lock changes or
deploy. Frozen legacy routes excluded from edits and responsive acceptance;
physical-device/virtual-keyboard testing remains unverified. Formal T028/T029
BLOCKED and T030–T033 PARTIAL preserved; historical T034–T043 states retained.

Report: docs/realtime_moderation/RESPONSIVE_UI_REPORT.md.
Source/evidence SHA inventory: reports/responsive_20261105_verified.json.
Before: reports/task_rollout_20261104/demo_77a6b5d6c9fe3d7b/.
Final: reports/task_rollout_20261104/demo_087f9ab44bf232fa/.
Regressions: reports/task_rollout_20261104/demo_9a8b1169d4c85243/.
Resume: refresh existing /live.html or /studio.html; use browser device emulation
or run --responsive-check. No restart/migration/training required for this UI.

## Visual responsive follow-up — 05/11/2026 — IN_PROGRESS

User-reported native Chrome resizing was not covered by prior viewport-only
tests. Root cause measured on genuine launcher session demo_a53a25230d622b48:
headed browser contexts fixed at1250x950; native window1650 or850 still CSS1250,
tablet filters remain3columns. CSS shell caps1480/1500/1440 also underuse wide
screens. Baseline70measurements/14new coverage violations retained; no old
receipt rewritten. Fixed headed viewport:null plus fluid opt-in shells/filter
tracks/desktop panels. Final native-window VisualCheck now running through
scripts/demo_realtime_studio.ps1. Both builds PASS; acceptance remains pending.
Report: docs/realtime_moderation/RESPONSIVE_VISUAL_FIX_REPORT.md.


## Native Chrome visual fix — 05/11/2026 — DONE_VERIFIED

Supersedes viewport-only responsive acceptance for the user-reported issue.
Measured genuine launcher BEFORE: native window1650/850 still CSS1250, fixed
1250x950 Playwright viewport; tablet filters3columns. Headed context now
viewport:null. Fluid Live/Studio shells, responsive filter tracks, bounded
queue/sidebar widths, desktop context/review panels, reading-text-only caps.
Frozen legacy/API/backend/model/0.41/readiness/reference states unchanged.

Final actual launcher session: reports/task_rollout_20261104/demo_8ffee4b4a52cc384.
70/70layout measurements across7populated Live/Studio states and10viewports,
10/10workflows PASS;0page errors/overflow/clipped fields. Native desktop width
verified;28native cases,14native-width/height-only emulation due Windows cap,
28mobile emulation. At1650 client/root/shell1635; at850 shell835 and Thread394.5.
Negative controls correctly reject1075px left root and clipped tablet filters.
70final screenshots assert PNG width and unchanged DOM width during capture.
Prior interrupted/harness/cropped-screenshot attempts retained and documented.

Both builds PASS; startup13PASS; actual launcher hide/appeal/restore/repeated/
audit E2E8PASS; readiness1311PASS. Studio training/evaluation run counts0;
only synthetic UI draft annotation, never human gold. User's original session
retained; final4-context VisualCheck demo remains running. Normal launcher
still opens5social accounts+Moderator+Studio, now with native resize.
Old fixed-viewport windows need a fresh launcher session, not only refresh.
Report: docs/realtime_moderation/RESPONSIVE_VISUAL_FIX_REPORT.md.
Evidence/SHA: reports/visual_fix_20261105_verified.json.
URLs: Social http://127.0.0.1:53351/live.html?thread=00810990-0e49-4c75-b4b2-cd820bc498f1
Moderator http://127.0.0.1:53352/live.html; Studio http://127.0.0.1:53352/studio.html.
Remaining limits: real phones/keyboard, other browsers/DPI/zoom unverified;
legacy unchanged; formal T028/T029 BLOCKED, T030-T033 PARTIAL preserved.

## Project report brief — 05/11/2026 — DONE_VERIFIED

Created docs/ai-update/final-report/ShieldVI_Tom_tat_de_tai_2_trang.docx from
current MVP/architecture, local T034–T043 implementation, r06 experiment,
formal readiness limits and native-window visual evidence. Covers topic,
objectives/scope, requirements, verified results, limitations and prioritized
development. Distinguishes local technical acceptance from independent human
gold; r06 candidate metrics are explicitly synthetic, never production proof.
Word repagination confirms exactly2pages, complete text on both pages, A4/TNR12;
only7short keyword phrases bold. DOCX ZIP/XML validation PASS. Word file saved
and owned automation closed successfully; optional PDF export was omitted
after it stalled. No application/model/dataset/test/task-acceptance change.
Evidence: reports/project_brief_20261105_word_render.json and
reports/project_brief_20261105_verified.json. File linked from docs/README.md.

## JSON export follow-up — 05/11/2026 — CODE VERIFIED / ACTIVATION PENDING

Recovered exact user UUID download as UTF-8 JSON:15comments/48293bytes, copied
without changing bytes to demo_2e7ba701c0343580/downloads/
REDDIT_TROCHUYENLINHTINH_001_analysis.json. Original temp file retained.
Root cause confirmed in installed Playwright: allowAndName overrides the real
disk filename with UUID. Prior saveAs-based tests masked the user issue.

New headed contexts use scoped CDP allow with session-owned downloads directory;
keep CDP attached for context lifetime. Shared frontend export helper adds safe
prefix/UTC timestamp/nonce and preserves extension/payload, avoiding repeated
overwrite. Quick JSON and Studio exports reuse it. No backend/model/API change.
7native Chrome checks PASS,5actual V1.1 JSON export E2E PASS without saveAs,
startup13PASS,Moderator/Studio build PASS. Repeated exports and CSV/JSONL checked;
Chrome Downloads shows .json, UTF-8 preserved, files survive context close.

Readiness FAIL:9external original V1 files missing at
C:/Users/admin/Downloads/visobert_toxic_final;1302other entries have no mismatch,
lock SHA unchanged. Registry uses this same missing path. Full fresh Studio
startup needs those artifacts; do not stop current demo/rewrite lock or model
paths. Existing headed browser policy needs a fresh context to activate the fix.
User's current session/pointer/DB retained; recovered JSON is immediately usable.
No train, download of external models/datasets, deploy or production change.

Details: docs/realtime_moderation/DOWNLOAD_EXPORT_FIX.md.
Evidence: reports/download_fix_20261105_verified.json,
download_fix_20261105_recovered.json; actual test root demo_e2716aa0ec230f62.
