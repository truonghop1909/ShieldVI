# T014/T019 — E2E, AI/policy evaluation, privacy/security

Ngày 30/10/2026, Asia/Saigon. **DONE cho local/private**, theo phạm vi người dùng xác nhận: dùng ViCTSD có sẵn để đánh giá classifier, ghi rõ chưa đủ gold độc lập cho policy/thread. Không thực hiện T015, không migrate DB demo, train/tune, tải dữ liệu hoặc bật HIGH auto-hold.

## Kết quả kiểm chứng

| Lệnh / phạm vi | Kết quả và evidence |
|---|---|
| Từ `services/social-api`: `.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider --junitxml=../../../ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/T014_T019/social-results.xml` | **177 passed**, 1 warning, 51.00s; [log](../../baseline/T014_T019/social-pytest.txt), [JUnit](../../baseline/T014_T019/social-results.xml) |
| Subset cuối `.venv/Scripts/python.exe -m pytest tests/test_privacy_security.py -q -p no:cacheprovider` | **19 passed**, 1 warning, 6.16s; chạy lại sau khi đóng rõ SQLite backup handles; [log](../../baseline/T014_T019/privacy-security-pytest.txt). Các cases nằm trong 177, không cộng trùng |
| V3 root, `STORE_SUMMARIES=0`: legacy `.venv/Scripts/python.exe -m pytest tests -q -p no:cacheprovider` | **139 passed**, 1 warning, 1.89s; [log](../../baseline/T014_T019/legacy-pytest.txt) |
| Social venv `services/social-api/tests/run_fullstack.py` | **1 Chrome fullstack passed**, 10.1s; đủ API + AI fixture + worker + 2 Vite servers; [log](../../baseline/T014_T019/fullstack/browser-tests.txt), [metrics](../../baseline/T014_T019/fullstack/metrics.json), [process health](../../baseline/T014_T019/fullstack/process-health.json), [cleanup](../../baseline/T014_T019/fullstack/cleanup.json) |
| T013 browser runner, artifacts override `T014_T019/admin-regression` | **6 Chrome passed**, 10.7s; [log](../../baseline/T014_T019/admin-regression/browser-tests.txt) |
| T010 browser runner, artifacts override `T014_T019/social-regression` | **9 Chrome passed**, 12.3s; [log](../../baseline/T014_T019/social-regression/browser-tests.txt) |
| `npm.cmd run build` trong moderation-web và social-web | **PASS**, exit 0; [dashboard](../../baseline/T014_T019/moderation-build.txt), [social](../../baseline/T014_T019/social-build.txt) |
| Social venv `services/social-api/tests/run_outage.py --seconds 600` | **PASS**, AI process thực sự vắng 600 giây, 21 mẫu pending; [result](../../baseline/T014_T019/outage/result.json), [cleanup](../../baseline/T014_T019/outage/cleanup.json) |
| Legacy venv `scripts/evaluate_social_policy.py --output ../ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/T014_T019/ai-evaluation.json --threads 2` | **Real checkpoint CPU inference**, đủ 1.000 ViCTSD + 30 synthetic riêng; [JSON](../../baseline/T014_T019/ai-evaluation.json) |

Hai browser runners regression được import bằng `importlib.util.spec_from_file_location`, chỉ đổi biến `ARTIFACTS` sang thư mục chặng này trước `main()`, không sửa fixture/baseline lịch sử. Warning pytest là Starlette/httpx deprecation hiện có; browser có NO_COLOR/FORCE_COLOR. Hai frontend không cấu hình lint/typecheck riêng; không tuyên bố đã chạy các check không tồn tại.

## E2E và lỗi đã sửa

Luồng fullstack chạy thật trên năm process loopback và SQLite tạm: register/login → tạo post nhận pending ngay → worker/AI fixture publish LOW khi admin offline → comment có score synthetic 0.9 được flag → AI trả 503 → job retry, content pending → moderator hide → author appeal → moderator restore → AI recovery xử lý công việc mới, không ghi đè quyết định thủ công. Browser không gửi request nào trực tiếp tới AI. [Ảnh sau recovery](../../baseline/T014_T019/fullstack/browser/appeal-after-worker-recovery.png).

Các lần chạy đầu phát hiện lỗi thật và đã được sửa, chạy lại:

- Login đọc user bằng deferred SQLite transaction rồi nâng lên write trong lúc worker commit: `database is locked`. Login lấy BEGIN IMMEDIATE **sau khi** rate-limit transaction đã commit; logout dùng chung authenticated writer session. Test phối hợp login và writer bằng thread events tái hiện cạnh tranh.
- Staff metrics giữ auth read transaction nhưng mở thêm connection cho schema/stats: reader mới chờ writer, writer chờ reader cũ, worker chết khi commit. Route metrics tái sử dụng cùng session đọc; CLI stats vẫn tự kiểm tra schema. Test worker ghi chín job song song 25 lượt authenticated metrics; fullstack kiểm tra cả năm process còn sống.
- Validation 422 phản chiếu tên JSON field do client đặt, dù đã bỏ input values. Social và internal AI endpoint redact cả location field không tin cậy. Không thay legacy validation response.
- Admin DELETE reason chấp nhận NUL; chặn NUL/invalid Unicode tương tự các review actions.
- Lỗi dependency tải model có thể chứa đường dẫn riêng tư trước khi vào adapter try/except. Internal moderation 5xx trả thông báo generic; legacy API giữ response cũ. SQLAlchemy Social engine bật `hide_parameters=True` để traceback không in bound values.
- SQLite backup dùng exclusive creation, không resolve destination symlink trước bước tạo file mới, đóng rõ connections sau verify/copy. Không overwrite/restore/migrate tự động.

Một lần E2E khác thất bại vì test dùng “cần xem xét” thay vì nhãn Social Web “chờ xem xét”; sửa assertion rồi chạy lại. Các lần lỗi ban đầu không được tính pass.

## AI: inference thật, threshold giữ 0.41

Model thực tế: **ViSoBERT V1.1 — ViCTSD**, auto-selected approved checkpoint `models/visobert_head_refined`, PyTorch 2.15.0+cpu, Transformers 4.57.3, CPU hai threads. Không có V1 baseline riêng được đánh giá trong chặng này; không gọi refined V1.1 là baseline V1. Weights/config/lexicon SHA-256 nằm trong JSON. Không training, tải model hay đổi threshold.

ViCTSD **1.000 dòng test gốc**, 890 clean/110 toxic, hash `e341013ca7441a5f2621b9347bd933f4d920d080b9931136ee8827d0ac0b2672`. Nhãn Toxicity có sẵn từ bản local do người dùng cung cấp, không phải nhãn AI mới. Giữ toàn bộ thứ tự/nhãn/split, không loại dòng hoặc chọn threshold từ test. Tập đã xuất hiện trong báo cáo cũ, **không phải holdout mù mới**. Provenance/license bản local vẫn `not_reverified_for_local_user_copy`; không tái phân phối raw text trong evidence.

| Phép đo trên cùng 1.000 câu | Precision | Recall | Macro-F1 | Confusion TN/FP/FN/TP |
|---|---:|---:|---:|---|
| ViSoBERT V1.1, nhãn toxicity ở 0.41 | 0.5524 | 0.5273 | 0.7420 | 843 / 47 / 52 / 58 |
| Lexicon review-screening, so với Toxicity như proxy | N/A, không hit dương | 0.0000 | 0.4709 | 890 / 0 / 110 / 0 |
| Hybrid review-screening, so với Toxicity như proxy | 0.5524 | 0.5273 | 0.7420 | 843 / 47 / 52 / 58 |

Classifier accuracy 0.9010, toxic F1 0.5395; FPR 5.28% (Wilson 95% 3.99–6.95%), FNR 47.27% (38.19–56.54%). Accuracy cao chịu ảnh hưởng 89% clean; recall còn hạn chế. Lexicon không bổ sung hit review nào trên tập này, nên hybrid screening trùng classifier. Đây là kết quả chạy, không suy ra lexicon vô dụng ở mọi domain hay tự mở rộng/enable pending rules để cải thiện test. Lexicon/screening dương **không đồng nghĩa** nhãn toxicity/cyberbullying.

Active worker dùng chung hàm `policy_outcome` được tách nguyên logic từ worker để evaluator chạy đúng policy, không triển khai policy giả riêng: **895 LOW/PUBLISHED, 105 REVIEW/PUBLISHED_FLAGGED**, review load **10.5%**, không HIGH/hold/hide tự động. Adapter dùng score đã được inference thật tính một lần; bước postprocess không chạy model lại. Cả 1.000 câu được đánh giá standalone, context incomplete; target unknown 100% là coverage của ngữ cảnh đầu vào, không phải target recall.

Latency CPU: 65 batch, tối đa 16 items/batch, warm-up tách riêng; median **2.185s/batch**, p95 **2.874s/batch**; amortized median **136.54ms/item**, p95 **179.62ms/item**. Đây là batch inference đo trên máy local, gồm cả 30 câu synthetic, **không phải** HTTP/singleton production latency. Adapter cached postprocess median 0.223ms cho ViCTSD; không cộng nhầm thành thời gian model.

30 câu MXH challenge giữ `is_gold=false`, `training_eligible=false`, chạy riêng bằng checkpoint thật: 18 LOW, 12 REVIEW (40%). Không tính precision/recall/F1 từ bộ tổng hợp. Không có gold mới cho HIGH, target hoặc repeated event; không trộn ViHOS span/ViLexNorm normalization thành Toxicity.

**Khuyến nghị: tiếp tục tắt HIGH auto-hold.** FP/FN/precision/recall của HIGH và target/repeated F1 để null/N/A, không coi 0 lần hold trong chế độ tắt là chứng minh hold an toàn. Cần thread/event gold độc lập, guideline/annotators/adjudication, provenance/quyền sử dụng, split theo thread/actor, validation goals trước tuning, final test mới và approval kích hoạt. Người dùng xác nhận chưa có bộ này; T019 hoàn thành phép đo classifier và ghi rõ giới hạn theo phạm vi đã chốt.

## Fault recovery, performance và backup

AI process vắng thật **600s**, worker chạy và không có staff requests trong outage. 21 lần đọc author vẫn nhận đúng body/pending. Sau ba attempts, job FAILED_PERMANENTLY, hai retries, oldest wait 601s. Bật AI synthetic lại rồi moderator retry → PUBLISHED, audit CREATE/AI_RETRY/AI_FAILED/JOB_RETRY/AI_APPLIED; worker vẫn sống. Job đã hết budget cần manual retry, không tự thử vô hạn. `model_availability=unknown` sau khi không có kết quả trong cửa sổ năm phút là thống kê gần đây, không phải healthy/live probe.

Fullstack đo browser create flow **122ms**, tới public **2.685s** khi AI fixture cố tình chậm 1.5s; thấy retry sau fault **911ms**. Bao gồm thao tác browser/polling, không phải SLO HTTP hay model thật. Metrics tổng job có một failed fixture tạo sẵn; không dùng tổng đó làm failure rate thực tế. Appeal overturn 1/1 trong test là synthetic workflow, không phải tỷ lệ kháng nghị ngoài thực tế.

Feed fixture: 1.000 public + 200 pending/held/hidden/deleted trong DB tạm, đọc 20 trang size 50 đủ 1.000 ID duy nhất, không lộ private qua total/body; trang 21 rỗng. TestClient median **5.805ms**, p95 **6.395ms** cho 20 lượt đọc local, [JUnit properties](../../baseline/T014_T019/social-results.xml). Đây là benchmark fixture đơn máy, chưa có load/concurrent users/PostgreSQL hoặc SLA production.

Backup test: SQLite online backup → integrity/foreign key/schema verify → khởi động API trên **bản copy DB tạm** → session/content/job/audit đọc lại thành công. Refuse existing destination/source alias, hỗ trợ schema trước upgrade, không ghi đè DB thật. Runbook có commands và khôi phục bằng đổi DB path riêng; chưa vận hành offsite/encryption/retention trên dữ liệu thật.

## Security/privacy đã kiểm tra và phạm vi còn lại

| Mục | Bằng chứng |
|---|---|
| Auth/JWT/cookie/CSRF | Runtime opaque Bearer, Argon2id, token hash/expiry/revoke; cookie/query token và forged JWT không authenticate/mutate; không dùng cookie auth nên không có CSRF cookie flow |
| Role/IDOR | Role/suspend đọc từ DB mỗi request, author/staff boundary, held ancestor direct/list/count, appeal author-only và audit staff-only; hạ role/suspend có hiệu lực |
| CORS/rate limit | Exact allowlist và mutation preflight, reject null/suffix origin, no credentials; durable shared quotas cho report/appeal, không bypass bằng forwarded peer |
| XSS/browser secrets | Full text React text nodes, 320/390 responsive regression, memory-only auth, late response/logout/expiry; browser không gọi AI, service token không vào bundle |
| PII/log/error | Synthetic text/email/password/service token không xuất hiện trong [5 server logs](../../baseline/T014_T019/fullstack/log-privacy.json); 422 không echo values/unknown field names; internal 5xx generic; SQL parameters hidden; failure diagnostics redact test credentials |
| AI payload minimization | Chỉ opaque IDs, text/context giới hạn, complete=false; không gửi account email/password/hash/IP/token/username; text tự thân vẫn có thể chứa PII, không tuyên bố đã anonymize toàn bộ |
| Backup/env | Dedicated Social DB, private defaults, unsafe config rejected, online backup verified/refuse overwrite; không migrate hoặc cấp staff thật trong test |

Không public-hosting/pentest/certification. Legacy research `/api/reviews*`, `/api/recent`, `/health` chưa dùng Social auth và có thể lộ metadata/path; giữ loopback hoặc proxy auth/route allowlist, không mở public nguyên AI server. Không thay legacy contract vì security check này. Chưa kiểm chứng Colab/GPU, protected public proxy, PostgreSQL server, distributed rate limits, production TLS/CSP/edge limits, retention/delete toàn bộ bản sao, backup encryption/offsite hoặc gold thread/HIGH/subgroup quality. Không có legal-compliance claim. Chưa thực hiện migration legacy T015.

## File và bàn giao

Tính từ V3 root:

- Sửa `app/main.py` (redaction chỉ internal); thêm `tests/test_internal_privacy.py`, `tests/test_evaluation.py`, `scripts/evaluate_social_policy.py`.
- Social API sửa `src/shieldvi_social/{main,content_schemas,routes,db,moderation_routes,worker}.py`; thêm `policy.py`, `backup.py`, `tests/{test_privacy_security,fullstack_ai,run_fullstack,run_outage}.py`; cập nhật README. Không schema migration mới, startup vẫn 0004.
- Moderation Web sửa `playwright.config.js`, thêm `tests/fullstack.spec.js`, cập nhật README; product React source/dependencies không đổi. Social Web source/dependencies không đổi.
- Design: task T014/T019, report/runbook, docs 04/08/09/API contract, CHANGELOG và `docs/baseline/T014_T019/`.

[Source manifest](../../baseline/T014_T019/source-manifest.json), [integrity và schema read-only](../../baseline/T014_T019/integrity-check.json). Không Git metadata trong hai root, commit=null; không tạo Git/push. Checkpoint/config, lexicon, datasets và legacy static được giữ nguyên; chỉ `app/main.py` thay đổi trong nguồn legacy gốc, với các legacy routes được regression. DB demo được kiểm tra chỉ `alembic_version`, không đọc body/account, không migrate.

[Hướng dẫn chạy/backup/eval](../../guides/RUN_LOCAL.md). Dừng ở T014/T019, T015 chỉ thực hiện khi người dùng yêu cầu.
