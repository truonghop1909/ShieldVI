# Báo cáo gộp toàn bộ thư mục tài liệu vào root dự án

Ngày 02/11/2026. Theo yêu cầu gộp tiếp của người dùng, **root hoạt động duy nhất là ShieldVI_V3_Hybrid_Review/**: AGENTS, docs, tasks, skills, contracts, templates và fixtures cùng gốc với services/apps. Không lồng nguyên thư mục thiết kế vào docs tạo thêm cấu trúc trùng.

## Kết quả tổ chức

- Đã đưa **341 file** từ thư mục tài liệu vào cấu trúc hiện có, gồm cả bằng chứng/snapshot lịch sử. Không mang cache/pycache vào dự án.
- Chỉ README.md trùng tên và khác nội dung: giữ README chạy dự án, đưa toàn bộ README thiết kế vào [SOCIAL_DESIGN_README](../../design/README.md), thêm chú thích lịch sử và chỉnh liên kết.
- [AGENTS](../../../AGENTS.md), [TASK_ORDER](../../../tasks/TASK_ORDER.md), [skill AI Update](../../../.agents/skills/shieldvi-ai-upgrade/SKILL.md) và [ghi chú tích hợp](../../ai-update/INTEGRATION_NOTES.md) dùng root thống nhất.
- Đã cập nhật các liên kết đang trỏ về thư mục tài liệu cũ trong README root, Moderation AI, Social API và Moderation Web. Chỉ sửa README của service/app, không thay implementation.
- Toàn bộ 27 file task T007–T033 giữ nguyên byte: 13 DONE và 14 TODO đúng nguồn, không bắt đầu task AI. TASK_ORDER_AI cũng giữ nguyên byte.
- Fixtures/templates giữ nguyên byte; datasets huấn luyện và checkpoint không sao chép lại hay thay đổi. Hai thư mục nguồn ngang hàng giữ nguyên làm backup.

## Điều chỉnh cần thiết

- Các liên kết tài liệu được tính lại theo root mới. Hai README đều giữ đầy đủ nội dung; file hướng dẫn sao chép/addendum cũ có banner để tránh áp dụng lại nhầm.
- Test tài liệu được sao chép vào tests/test_policy_design.py và chỉ thêm nhận diện root thống nhất, không đổi assertions hoặc test data. Mọi test vốn có giữ nguyên.
- Báo cáo AI Update và manifests cũ giữ làm lịch sử. Validator cũ trong docs/ai-update/merge-evidence chuyển tiếp sang validator root mới; phần logic cũ vẫn giữ trong file để đối chiếu.
- Hash nguồn/đích và action từng file: [CONSOLIDATION_MANIFEST](../../repository-merge-evidence/CONSOLIDATION_MANIFEST.json). Không đọc toàn bộ source/dataset; chỉ kiểm kê metadata runtime và đọc các fixture mới phục vụ kiểm tra.

## Kiểm tra thực tế

**PASS 51 kiểm tra, exit code 0; 268 liên kết hợp lệ; 341 file nguồn bảo toàn; 7 skill hợp lệ; không có thay đổi metadata runtime ngoài README tài liệu được phép sửa.**

- Trước gộp: test_policy_design tại root tài liệu cũ **17 passed**, exit 0.
- Sau gộp: test_policy_design tại root dự án **17 passed**, exit 0; một warning deprecation Starlette/httpx từ môi trường hiện có, không cài/nâng thư viện.
- Kiểm tra toàn vẹn: `python -X utf8 docs/repository-merge-evidence/validate_consolidation.py`. Kết quả chi tiết tại [VALIDATION_RESULTS](../../repository-merge-evidence/VALIDATION_RESULTS.json).
- Đối chiếu 341 file nguồn, hash bản cài, 27 task và trạng thái, 7 skill, mọi liên kết Markdown đang áp dụng, 150 comment/tag, JSON contracts/templates và metadata các file runtime có trước. Snapshot/baseline lịch sử không sửa.
- Không chạy build frontend hoặc toàn bộ backend vì không thay logic; không inference/train/download/deploy/push hoặc migrate database.

## Các điểm chưa quyết định từ lần gộp trước

Gói AI Update gốc vẫn có SKILL.md thiếu nội dung; skill tái lập không được coi là bản phục hồi hash gốc. Lựa chọn baseline thí nghiệm V1/V1.1 và scope liên service của T026/T032 vẫn để người dùng quyết định khi giao triển khai. Việc gộp thư mục không tự giải quyết/chọn các chính sách này.

## Mapping file đã đưa vào dự án

| Nguồn trong thư mục tài liệu cũ | Đích tại root dự án | Xử lý |
|---|---|---|
| .agents/skills/shieldvi-ai-integration/SKILL.md | .agents/skills/shieldvi-ai-integration/SKILL.md | copied |
| .agents/skills/shieldvi-ai-upgrade/SKILL.md | .agents/skills/shieldvi-ai-upgrade/SKILL.md | copied_and_adapted_paths_or_routing |
| .agents/skills/shieldvi-architecture-migration/SKILL.md | .agents/skills/shieldvi-architecture-migration/SKILL.md | copied |
| .agents/skills/shieldvi-moderation-admin/SKILL.md | .agents/skills/shieldvi-moderation-admin/SKILL.md | copied |
| .agents/skills/shieldvi-moderation-policy/SKILL.md | .agents/skills/shieldvi-moderation-policy/SKILL.md | copied |
| .agents/skills/shieldvi-social-backend/SKILL.md | .agents/skills/shieldvi-social-backend/SKILL.md | copied |
| .agents/skills/shieldvi-social-frontend/SKILL.md | .agents/skills/shieldvi-social-frontend/SKILL.md | copied |
| AGENTS.md | AGENTS.md | copied_and_adapted_paths_or_routing |
| docs/governance/AGENTS_SOCIAL_ADDENDUM.md | docs/governance/AGENTS_SOCIAL_ADDENDUM.md | copied_and_adapted_paths_or_routing |
| docs/CHANGELOG.md | docs/CHANGELOG.md | copied |
| contracts/ai_signals_v2_draft.example.json | contracts/ai_signals_v2_draft.example.json | copied |
| contracts/moderation_policy.example.json | contracts/moderation_policy.example.json | copied |
| contracts/moderation_request.example.json | contracts/moderation_request.example.json | copied |
| contracts/moderation_request.schema.json | contracts/moderation_request.schema.json | copied |
| contracts/moderation_response.example.json | contracts/moderation_response.example.json | copied |
| contracts/moderation_response.schema.json | contracts/moderation_response.schema.json | copied |
| contracts/policy_acceptance_cases.json | contracts/policy_acceptance_cases.json | copied |
| contracts/social-auth.openapi.json | contracts/social-auth.openapi.json | copied |
| contracts/social-content.openapi.json | contracts/social-content.openapi.json | copied |
| contracts/social-review.openapi.json | contracts/social-review.openapi.json | copied |
| contracts/social-worker.openapi.json | contracts/social-worker.openapi.json | copied |
| datasets/fixtures/genz_regression/README.md | datasets/fixtures/genz_regression/README.md | copied |
| datasets/fixtures/genz_regression/SHIELDVI_01_GAME_RANK_LAG_30.json | datasets/fixtures/genz_regression/SHIELDVI_01_GAME_RANK_LAG_30.json | copied |
| datasets/fixtures/genz_regression/SHIELDVI_02_SHOP_GIAY_SECONDHAND_30.json | datasets/fixtures/genz_regression/SHIELDVI_02_SHOP_GIAY_SECONDHAND_30.json | copied |
| datasets/fixtures/genz_regression/SHIELDVI_03_DANCE_COVER_TIKTOK_30.json | datasets/fixtures/genz_regression/SHIELDVI_03_DANCE_COVER_TIKTOK_30.json | copied |
| datasets/fixtures/genz_regression/SHIELDVI_04_DI_CAMPING_CHIA_TIEN_30.json | datasets/fixtures/genz_regression/SHIELDVI_04_DI_CAMPING_CHIA_TIEN_30.json | copied |
| datasets/fixtures/genz_regression/SHIELDVI_05_FANART_AI_DISPUTE_30.json | datasets/fixtures/genz_regression/SHIELDVI_05_FANART_AI_DISPUTE_30.json | copied |
| datasets/fixtures/genz_regression/synthetic_reference_tags.csv | datasets/fixtures/genz_regression/synthetic_reference_tags.csv | copied |
| docs/design/00_MUC_LUC.md | docs/design/00_MUC_LUC.md | copied |
| docs/design/01_PHAM_VI_MVP.md | docs/design/01_PHAM_VI_MVP.md | copied |
| docs/design/02_KIEN_TRUC.md | docs/design/02_KIEN_TRUC.md | copied |
| docs/design/03_CHINH_SACH_KIEM_DUYET.md | docs/design/03_CHINH_SACH_KIEM_DUYET.md | copied |
| docs/design/04_VONG_DOI_NOI_DUNG.md | docs/design/04_VONG_DOI_NOI_DUNG.md | copied |
| docs/design/05_LUONG_NGUOI_DUNG.md | docs/design/05_LUONG_NGUOI_DUNG.md | copied |
| docs/design/06_DU_LIEU.md | docs/design/06_DU_LIEU.md | copied |
| docs/design/07_API.md | docs/design/07_API.md | copied |
| docs/design/08_BAO_MAT_QUYEN_RIENG_TU.md | docs/design/08_BAO_MAT_QUYEN_RIENG_TU.md | copied |
| docs/design/09_TEST_DANH_GIA.md | docs/design/09_TEST_DANH_GIA.md | copied |
| docs/design/10_KE_HOACH_CODEX.md | docs/design/10_KE_HOACH_CODEX.md | copied |
| docs/design/11_QUYET_DINH_VA_CAU_HOI_MO.md | docs/design/11_QUYET_DINH_VA_CAU_HOI_MO.md | copied |
| docs/ai-update/00_READ_ME_FIRST.md | docs/ai-update/00_READ_ME_FIRST.md | copied |
| docs/ai-update/01_FAILURE_CASES.md | docs/ai-update/01_FAILURE_CASES.md | copied |
| docs/ai-update/02_ANNOTATION_GUIDE.md | docs/ai-update/02_ANNOTATION_GUIDE.md | copied |
| docs/ai-update/03_EXPERIMENT_PLAN.md | docs/ai-update/03_EXPERIMENT_PLAN.md | copied |
| docs/ai-update/04_API_VERSIONING.md | docs/ai-update/04_API_VERSIONING.md | copied |
| docs/ai-update/05_RELEASE_GATES.md | docs/ai-update/05_RELEASE_GATES.md | copied |
| docs/ai-update/06_COLAB_RUNBOOK.md | docs/ai-update/06_COLAB_RUNBOOK.md | copied |
| docs/ai-update/07_DATA_AND_SECURITY.md | docs/ai-update/07_DATA_AND_SECURITY.md | copied |
| docs/ai-update/INTEGRATION_NOTES.md | docs/ai-update/INTEGRATION_NOTES.md | copied_and_adapted_paths_or_routing |
| docs/ai-update/merge-evidence/MERGE_MANIFEST.json | docs/ai-update/merge-evidence/MERGE_MANIFEST.json | copied |
| docs/ai-update/merge-evidence/validate_merge.py | docs/ai-update/merge-evidence/validate_merge.py | copied_and_adapted_paths_or_routing |
| docs/ai-update/merge-evidence/VALIDATION_RESULTS.json | docs/ai-update/merge-evidence/VALIDATION_RESULTS.json | copied |
| docs/ai-update/MERGE_REPORT.md | docs/ai-update/MERGE_REPORT.md | copied_and_adapted_paths_or_routing |
| docs/ai-update/PACK_README.md | docs/ai-update/PACK_README.md | copied |
| docs/ai-update/PROMPT_CODEX_BAT_DAU.md | docs/ai-update/PROMPT_CODEX_BAT_DAU.md | copied |
| docs/ai-update/SOURCE_FILE_MANIFEST.json | docs/ai-update/SOURCE_FILE_MANIFEST.json | copied |
| docs/architecture/API_CONTRACT.md | docs/architecture/API_CONTRACT.md | copied_and_adapted_paths_or_routing |
| docs/architecture/ARCHITECTURE.md | docs/architecture/ARCHITECTURE.md | copied |
| docs/baseline/DEMO_ABCD/integrity-check.json | docs/baseline/DEMO_ABCD/integrity-check.json | copied |
| docs/baseline/DEMO_ABCD/smoke.json | docs/baseline/DEMO_ABCD/smoke.json | copied |
| docs/baseline/T007/frontend-build/assets/index-B6t7Eu4q.js | docs/baseline/T007/frontend-build/assets/index-B6t7Eu4q.js | copied |
| docs/baseline/T007/frontend-build/assets/index-BaiwjHcP.css | docs/baseline/T007/frontend-build/assets/index-BaiwjHcP.css | copied |
| docs/baseline/T007/frontend-build/index.html | docs/baseline/T007/frontend-build/index.html | copied |
| docs/baseline/T007/frontend-build-retry.txt | docs/baseline/T007/frontend-build-retry.txt | copied |
| docs/baseline/T007/frontend-build.txt | docs/baseline/T007/frontend-build.txt | copied |
| docs/baseline/T007/integrity-check.json | docs/baseline/T007/integrity-check.json | copied |
| docs/baseline/T007/pytest.txt | docs/baseline/T007/pytest.txt | copied |
| docs/baseline/T007/smoke.txt | docs/baseline/T007/smoke.txt | copied |
| docs/baseline/T007/source-manifest.json | docs/baseline/T007/source-manifest.json | copied |
| docs/baseline/T008/dependency-check.txt | docs/baseline/T008/dependency-check.txt | copied |
| docs/baseline/T008/legacy-integrity.json | docs/baseline/T008/legacy-integrity.json | copied |
| docs/baseline/T008/legacy-pytest.txt | docs/baseline/T008/legacy-pytest.txt | copied |
| docs/baseline/T008/live-smoke.txt | docs/baseline/T008/live-smoke.txt | copied |
| docs/baseline/T008/social-pytest.txt | docs/baseline/T008/social-pytest.txt | copied |
| docs/baseline/T008/social-source-manifest.json | docs/baseline/T008/social-source-manifest.json | copied |
| docs/baseline/T009/legacy-integrity.json | docs/baseline/T009/legacy-integrity.json | copied |
| docs/baseline/T009/legacy-pytest.txt | docs/baseline/T009/legacy-pytest.txt | copied |
| docs/baseline/T009/live-smoke.txt | docs/baseline/T009/live-smoke.txt | copied |
| docs/baseline/T009/social-pytest.txt | docs/baseline/T009/social-pytest.txt | copied |
| docs/baseline/T009/social-source-manifest.json | docs/baseline/T009/social-source-manifest.json | copied |
| docs/baseline/T010/api-server.txt | docs/baseline/T010/api-server.txt | copied |
| docs/baseline/T010/browser/.last-run.json | docs/baseline/T010/browser/.last-run.json | copied |
| docs/baseline/T010/browser/desktop-feed.png | docs/baseline/T010/browser/desktop-feed.png | copied |
| docs/baseline/T010/browser/desktop-login.png | docs/baseline/T010/browser/desktop-login.png | copied |
| docs/baseline/T010/browser/mobile-login.png | docs/baseline/T010/browser/mobile-login.png | copied |
| docs/baseline/T010/browser/mobile-thread.png | docs/baseline/T010/browser/mobile-thread.png | copied |
| docs/baseline/T010/browser-tests.txt | docs/baseline/T010/browser-tests.txt | copied |
| docs/baseline/T010/dependencies.txt | docs/baseline/T010/dependencies.txt | copied |
| docs/baseline/T010/frontend-build.txt | docs/baseline/T010/frontend-build.txt | copied |
| docs/baseline/T010/integrity-check.json | docs/baseline/T010/integrity-check.json | copied |
| docs/baseline/T010/social-web-source-manifest.json | docs/baseline/T010/social-web-source-manifest.json | copied |
| docs/baseline/T010/web-server.txt | docs/baseline/T010/web-server.txt | copied |
| docs/baseline/T011/legacy-pytest.txt | docs/baseline/T011/legacy-pytest.txt | copied |
| docs/baseline/T012_T017/ai-fixture-server.txt | docs/baseline/T012_T017/ai-fixture-server.txt | copied |
| docs/baseline/T012_T017/browser-regression/api-server.txt | docs/baseline/T012_T017/browser-regression/api-server.txt | copied |
| docs/baseline/T012_T017/browser-regression/browser/.last-run.json | docs/baseline/T012_T017/browser-regression/browser/.last-run.json | copied |
| docs/baseline/T012_T017/browser-regression/browser/desktop-feed.png | docs/baseline/T012_T017/browser-regression/browser/desktop-feed.png | copied |
| docs/baseline/T012_T017/browser-regression/browser/desktop-login.png | docs/baseline/T012_T017/browser-regression/browser/desktop-login.png | copied |
| docs/baseline/T012_T017/browser-regression/browser/mobile-login.png | docs/baseline/T012_T017/browser-regression/browser/mobile-login.png | copied |
| docs/baseline/T012_T017/browser-regression/browser/mobile-thread.png | docs/baseline/T012_T017/browser-regression/browser/mobile-thread.png | copied |
| docs/baseline/T012_T017/browser-regression/browser-tests.txt | docs/baseline/T012_T017/browser-regression/browser-tests.txt | copied |
| docs/baseline/T012_T017/browser-regression/web-server.txt | docs/baseline/T012_T017/browser-regression/web-server.txt | copied |
| docs/baseline/T012_T017/dependency-check.txt | docs/baseline/T012_T017/dependency-check.txt | copied |
| docs/baseline/T012_T017/integrity-check.json | docs/baseline/T012_T017/integrity-check.json | copied |
| docs/baseline/T012_T017/legacy-pytest.txt | docs/baseline/T012_T017/legacy-pytest.txt | copied |
| docs/baseline/T012_T017/live-http-smoke.txt | docs/baseline/T012_T017/live-http-smoke.txt | copied |
| docs/baseline/T012_T017/social-pytest.txt | docs/baseline/T012_T017/social-pytest.txt | copied |
| docs/baseline/T012_T017/social-server.txt | docs/baseline/T012_T017/social-server.txt | copied |
| docs/baseline/T012_T017/source-manifest.json | docs/baseline/T012_T017/source-manifest.json | copied |
| docs/baseline/T012_T017/worker-pytest.txt | docs/baseline/T012_T017/worker-pytest.txt | copied |
| docs/baseline/T013_T018/admin-server.txt | docs/baseline/T013_T018/admin-server.txt | copied |
| docs/baseline/T013_T018/api-server.txt | docs/baseline/T013_T018/api-server.txt | copied |
| docs/baseline/T013_T018/browser/.last-run.json | docs/baseline/T013_T018/browser/.last-run.json | copied |
| docs/baseline/T013_T018/browser/desktop-dashboard.png | docs/baseline/T013_T018/browser/desktop-dashboard.png | copied |
| docs/baseline/T013_T018/browser/mobile-detail.png | docs/baseline/T013_T018/browser/mobile-detail.png | copied |
| docs/baseline/T013_T018/browser-tests.txt | docs/baseline/T013_T018/browser-tests.txt | copied |
| docs/baseline/T013_T018/frontend-builds.txt | docs/baseline/T013_T018/frontend-builds.txt | copied |
| docs/baseline/T013_T018/integrity-check.json | docs/baseline/T013_T018/integrity-check.json | copied |
| docs/baseline/T013_T018/legacy-pytest.txt | docs/baseline/T013_T018/legacy-pytest.txt | copied |
| docs/baseline/T013_T018/social-pytest.txt | docs/baseline/T013_T018/social-pytest.txt | copied |
| docs/baseline/T013_T018/social-regression/api-server.txt | docs/baseline/T013_T018/social-regression/api-server.txt | copied |
| docs/baseline/T013_T018/social-regression/browser/.last-run.json | docs/baseline/T013_T018/social-regression/browser/.last-run.json | copied |
| docs/baseline/T013_T018/social-regression/browser/desktop-feed.png | docs/baseline/T013_T018/social-regression/browser/desktop-feed.png | copied |
| docs/baseline/T013_T018/social-regression/browser/desktop-login.png | docs/baseline/T013_T018/social-regression/browser/desktop-login.png | copied |
| docs/baseline/T013_T018/social-regression/browser/mobile-login.png | docs/baseline/T013_T018/social-regression/browser/mobile-login.png | copied |
| docs/baseline/T013_T018/social-regression/browser/mobile-thread.png | docs/baseline/T013_T018/social-regression/browser/mobile-thread.png | copied |
| docs/baseline/T013_T018/social-regression/browser-tests.txt | docs/baseline/T013_T018/social-regression/browser-tests.txt | copied |
| docs/baseline/T013_T018/social-regression/web-server.txt | docs/baseline/T013_T018/social-regression/web-server.txt | copied |
| docs/baseline/T013_T018/social-review.openapi.json | docs/baseline/T013_T018/social-review.openapi.json | copied |
| docs/baseline/T013_T018/social-server.txt | docs/baseline/T013_T018/social-server.txt | copied |
| docs/baseline/T013_T018/source-manifest.json | docs/baseline/T013_T018/source-manifest.json | copied |
| docs/baseline/T013_T018/verify_integrity.py | docs/baseline/T013_T018/verify_integrity.py | copied |
| docs/baseline/T014_T019/admin-regression/admin-server.txt | docs/baseline/T014_T019/admin-regression/admin-server.txt | copied |
| docs/baseline/T014_T019/admin-regression/api-server.txt | docs/baseline/T014_T019/admin-regression/api-server.txt | copied |
| docs/baseline/T014_T019/admin-regression/browser/.last-run.json | docs/baseline/T014_T019/admin-regression/browser/.last-run.json | copied |
| docs/baseline/T014_T019/admin-regression/browser/desktop-dashboard.png | docs/baseline/T014_T019/admin-regression/browser/desktop-dashboard.png | copied |
| docs/baseline/T014_T019/admin-regression/browser/mobile-detail.png | docs/baseline/T014_T019/admin-regression/browser/mobile-detail.png | copied |
| docs/baseline/T014_T019/admin-regression/browser-tests.txt | docs/baseline/T014_T019/admin-regression/browser-tests.txt | copied |
| docs/baseline/T014_T019/admin-regression/social-review.openapi.json | docs/baseline/T014_T019/admin-regression/social-review.openapi.json | copied |
| docs/baseline/T014_T019/admin-regression/social-server.txt | docs/baseline/T014_T019/admin-regression/social-server.txt | copied |
| docs/baseline/T014_T019/ai-evaluation.json | docs/baseline/T014_T019/ai-evaluation.json | copied |
| docs/baseline/T014_T019/fullstack/ai-fixture.txt | docs/baseline/T014_T019/fullstack/ai-fixture.txt | copied |
| docs/baseline/T014_T019/fullstack/browser/.last-run.json | docs/baseline/T014_T019/fullstack/browser/.last-run.json | copied |
| docs/baseline/T014_T019/fullstack/browser/appeal-after-worker-recovery.png | docs/baseline/T014_T019/fullstack/browser/appeal-after-worker-recovery.png | copied |
| docs/baseline/T014_T019/fullstack/browser-tests.txt | docs/baseline/T014_T019/fullstack/browser-tests.txt | copied |
| docs/baseline/T014_T019/fullstack/cleanup.json | docs/baseline/T014_T019/fullstack/cleanup.json | copied |
| docs/baseline/T014_T019/fullstack/log-privacy.json | docs/baseline/T014_T019/fullstack/log-privacy.json | copied |
| docs/baseline/T014_T019/fullstack/metrics.json | docs/baseline/T014_T019/fullstack/metrics.json | copied |
| docs/baseline/T014_T019/fullstack/moderation-web.txt | docs/baseline/T014_T019/fullstack/moderation-web.txt | copied |
| docs/baseline/T014_T019/fullstack/process-health.json | docs/baseline/T014_T019/fullstack/process-health.json | copied |
| docs/baseline/T014_T019/fullstack/social-api.txt | docs/baseline/T014_T019/fullstack/social-api.txt | copied |
| docs/baseline/T014_T019/fullstack/social-web.txt | docs/baseline/T014_T019/fullstack/social-web.txt | copied |
| docs/baseline/T014_T019/fullstack/worker.txt | docs/baseline/T014_T019/fullstack/worker.txt | copied |
| docs/baseline/T014_T019/integrity-check.json | docs/baseline/T014_T019/integrity-check.json | copied |
| docs/baseline/T014_T019/legacy-pytest.txt | docs/baseline/T014_T019/legacy-pytest.txt | copied |
| docs/baseline/T014_T019/moderation-build.txt | docs/baseline/T014_T019/moderation-build.txt | copied |
| docs/baseline/T014_T019/outage/ai-fixture.txt | docs/baseline/T014_T019/outage/ai-fixture.txt | copied |
| docs/baseline/T014_T019/outage/cleanup.json | docs/baseline/T014_T019/outage/cleanup.json | copied |
| docs/baseline/T014_T019/outage/progress.json | docs/baseline/T014_T019/outage/progress.json | copied |
| docs/baseline/T014_T019/outage/result.json | docs/baseline/T014_T019/outage/result.json | copied |
| docs/baseline/T014_T019/outage/social-api.txt | docs/baseline/T014_T019/outage/social-api.txt | copied |
| docs/baseline/T014_T019/outage/worker.txt | docs/baseline/T014_T019/outage/worker.txt | copied |
| docs/baseline/T014_T019/privacy-security-pytest.txt | docs/baseline/T014_T019/privacy-security-pytest.txt | copied |
| docs/baseline/T014_T019/social-build.txt | docs/baseline/T014_T019/social-build.txt | copied |
| docs/baseline/T014_T019/social-pytest.txt | docs/baseline/T014_T019/social-pytest.txt | copied |
| docs/baseline/T014_T019/social-regression/api-server.txt | docs/baseline/T014_T019/social-regression/api-server.txt | copied |
| docs/baseline/T014_T019/social-regression/browser/.last-run.json | docs/baseline/T014_T019/social-regression/browser/.last-run.json | copied |
| docs/baseline/T014_T019/social-regression/browser/desktop-feed.png | docs/baseline/T014_T019/social-regression/browser/desktop-feed.png | copied |
| docs/baseline/T014_T019/social-regression/browser/desktop-login.png | docs/baseline/T014_T019/social-regression/browser/desktop-login.png | copied |
| docs/baseline/T014_T019/social-regression/browser/mobile-login.png | docs/baseline/T014_T019/social-regression/browser/mobile-login.png | copied |
| docs/baseline/T014_T019/social-regression/browser/mobile-thread.png | docs/baseline/T014_T019/social-regression/browser/mobile-thread.png | copied |
| docs/baseline/T014_T019/social-regression/browser-tests.txt | docs/baseline/T014_T019/social-regression/browser-tests.txt | copied |
| docs/baseline/T014_T019/social-regression/web-server.txt | docs/baseline/T014_T019/social-regression/web-server.txt | copied |
| docs/baseline/T014_T019/social-results.xml | docs/baseline/T014_T019/social-results.xml | copied |
| docs/baseline/T014_T019/source-manifest.json | docs/baseline/T014_T019/source-manifest.json | copied |
| docs/baseline/T014_T019/verify_integrity.py | docs/baseline/T014_T019/verify_integrity.py | copied |
| docs/baseline/T015/admin-regression/admin-server.txt | docs/baseline/T015/admin-regression/admin-server.txt | copied |
| docs/baseline/T015/admin-regression/api-server.txt | docs/baseline/T015/admin-regression/api-server.txt | copied |
| docs/baseline/T015/admin-regression/browser/.last-run.json | docs/baseline/T015/admin-regression/browser/.last-run.json | copied |
| docs/baseline/T015/admin-regression/browser/desktop-dashboard.png | docs/baseline/T015/admin-regression/browser/desktop-dashboard.png | copied |
| docs/baseline/T015/admin-regression/browser/mobile-detail.png | docs/baseline/T015/admin-regression/browser/mobile-detail.png | copied |
| docs/baseline/T015/admin-regression/browser-tests.txt | docs/baseline/T015/admin-regression/browser-tests.txt | copied |
| docs/baseline/T015/admin-regression/social-review.openapi.json | docs/baseline/T015/admin-regression/social-review.openapi.json | copied |
| docs/baseline/T015/admin-regression/social-server.txt | docs/baseline/T015/admin-regression/social-server.txt | copied |
| docs/baseline/T015/after-legacy-build.txt | docs/baseline/T015/after-legacy-build.txt | copied |
| docs/baseline/T015/after-manifest.json | docs/baseline/T015/after-manifest.json | copied |
| docs/baseline/T015/after-move-legacy-pytest.txt | docs/baseline/T015/after-move-legacy-pytest.txt | copied |
| docs/baseline/T015/before-legacy-build/assets/index-B6t7Eu4q.js | docs/baseline/T015/before-legacy-build/assets/index-B6t7Eu4q.js | copied |
| docs/baseline/T015/before-legacy-build/assets/index-BaiwjHcP.css | docs/baseline/T015/before-legacy-build/assets/index-BaiwjHcP.css | copied |
| docs/baseline/T015/before-legacy-build/index.html | docs/baseline/T015/before-legacy-build/index.html | copied |
| docs/baseline/T015/before-legacy-build.txt | docs/baseline/T015/before-legacy-build.txt | copied |
| docs/baseline/T015/before-legacy-pytest.txt | docs/baseline/T015/before-legacy-pytest.txt | copied |
| docs/baseline/T015/before-manifest.json | docs/baseline/T015/before-manifest.json | copied |
| docs/baseline/T015/before-moderation-build.txt | docs/baseline/T015/before-moderation-build.txt | copied |
| docs/baseline/T015/before-social-build.txt | docs/baseline/T015/before-social-build.txt | copied |
| docs/baseline/T015/before-social-pytest.txt | docs/baseline/T015/before-social-pytest.txt | copied |
| docs/baseline/T015/canonical-real-server.txt | docs/baseline/T015/canonical-real-server.txt | copied |
| docs/baseline/T015/compat-build.txt | docs/baseline/T015/compat-build.txt | copied |
| docs/baseline/T015/fullstack/ai-fixture.txt | docs/baseline/T015/fullstack/ai-fixture.txt | copied |
| docs/baseline/T015/fullstack/browser/.last-run.json | docs/baseline/T015/fullstack/browser/.last-run.json | copied |
| docs/baseline/T015/fullstack/browser/appeal-after-worker-recovery.png | docs/baseline/T015/fullstack/browser/appeal-after-worker-recovery.png | copied |
| docs/baseline/T015/fullstack/browser-tests.txt | docs/baseline/T015/fullstack/browser-tests.txt | copied |
| docs/baseline/T015/fullstack/cleanup.json | docs/baseline/T015/fullstack/cleanup.json | copied |
| docs/baseline/T015/fullstack/log-privacy.json | docs/baseline/T015/fullstack/log-privacy.json | copied |
| docs/baseline/T015/fullstack/metrics.json | docs/baseline/T015/fullstack/metrics.json | copied |
| docs/baseline/T015/fullstack/moderation-web.txt | docs/baseline/T015/fullstack/moderation-web.txt | copied |
| docs/baseline/T015/fullstack/process-health.json | docs/baseline/T015/fullstack/process-health.json | copied |
| docs/baseline/T015/fullstack/social-api.txt | docs/baseline/T015/fullstack/social-api.txt | copied |
| docs/baseline/T015/fullstack/social-web.txt | docs/baseline/T015/fullstack/social-web.txt | copied |
| docs/baseline/T015/fullstack/worker.txt | docs/baseline/T015/fullstack/worker.txt | copied |
| docs/baseline/T015/integrity-check.json | docs/baseline/T015/integrity-check.json | copied |
| docs/baseline/T015/legacy-pytest.txt | docs/baseline/T015/legacy-pytest.txt | copied |
| docs/baseline/T015/moderation-build.txt | docs/baseline/T015/moderation-build.txt | copied |
| docs/baseline/T015/protected-manifest.json | docs/baseline/T015/protected-manifest.json | copied |
| docs/baseline/T015/real-http-smoke.json | docs/baseline/T015/real-http-smoke.json | copied |
| docs/baseline/T015/real_http_smoke.py | docs/baseline/T015/real_http_smoke.py | copied |
| docs/baseline/T015/rollback-source/.gitignore | docs/baseline/T015/rollback-source/.gitignore | copied |
| docs/baseline/T015/rollback-source/app/.env.moderation.example | docs/baseline/T015/rollback-source/app/.env.moderation.example | copied |
| docs/baseline/T015/rollback-source/app/__init__.py | docs/baseline/T015/rollback-source/app/__init__.py | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/active.json | docs/baseline/T015/rollback-source/app/data/lexicon/active.json | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/candidates.json | docs/baseline/T015/rollback-source/app/data/lexicon/candidates.json | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/manifest.json | docs/baseline/T015/rollback-source/app/data/lexicon/manifest.json | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/README.md | docs/baseline/T015/rollback-source/app/data/lexicon/README.md | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/reviewed_rules.json | docs/baseline/T015/rollback-source/app/data/lexicon/reviewed_rules.json | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/sources/blue_eyes_vi_LICENSE.md | docs/baseline/T015/rollback-source/app/data/lexicon/sources/blue_eyes_vi_LICENSE.md | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/sources/blue_eyes_vi_README.md | docs/baseline/T015/rollback-source/app/data/lexicon/sources/blue_eyes_vi_README.md | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/sources/blue_eyes_vi_vn_offensive_words.txt | docs/baseline/T015/rollback-source/app/data/lexicon/sources/blue_eyes_vi_vn_offensive_words.txt | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/sources/ldnoobw_v2_data_en.txt | docs/baseline/T015/rollback-source/app/data/lexicon/sources/ldnoobw_v2_data_en.txt | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/sources/ldnoobw_v2_data_vi.txt | docs/baseline/T015/rollback-source/app/data/lexicon/sources/ldnoobw_v2_data_vi.txt | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/sources/ldnoobw_v2_LICENSE | docs/baseline/T015/rollback-source/app/data/lexicon/sources/ldnoobw_v2_LICENSE | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/sources/ldnoobw_v2_README.md | docs/baseline/T015/rollback-source/app/data/lexicon/sources/ldnoobw_v2_README.md | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/sources/ldnoobw_v2_SOURCES.md | docs/baseline/T015/rollback-source/app/data/lexicon/sources/ldnoobw_v2_SOURCES.md | copied |
| docs/baseline/T015/rollback-source/app/data/lexicon/sources/snapshots.json | docs/baseline/T015/rollback-source/app/data/lexicon/sources/snapshots.json | copied |
| docs/baseline/T015/rollback-source/app/database.py | docs/baseline/T015/rollback-source/app/database.py | copied |
| docs/baseline/T015/rollback-source/app/engine.py | docs/baseline/T015/rollback-source/app/engine.py | copied |
| docs/baseline/T015/rollback-source/app/lexical.py | docs/baseline/T015/rollback-source/app/lexical.py | copied |
| docs/baseline/T015/rollback-source/app/main.py | docs/baseline/T015/rollback-source/app/main.py | copied |
| docs/baseline/T015/rollback-source/app/moderation_adapter.py | docs/baseline/T015/rollback-source/app/moderation_adapter.py | copied |
| docs/baseline/T015/rollback-source/app/moderation_contract.py | docs/baseline/T015/rollback-source/app/moderation_contract.py | copied |
| docs/baseline/T015/rollback-source/app/predictor.py | docs/baseline/T015/rollback-source/app/predictor.py | copied |
| docs/baseline/T015/rollback-source/app/review_store.py | docs/baseline/T015/rollback-source/app/review_store.py | copied |
| docs/baseline/T015/rollback-source/app/schemas.py | docs/baseline/T015/rollback-source/app/schemas.py | copied |
| docs/baseline/T015/rollback-source/app/static/assets/index-B6t7Eu4q.js | docs/baseline/T015/rollback-source/app/static/assets/index-B6t7Eu4q.js | copied |
| docs/baseline/T015/rollback-source/app/static/assets/index-BaiwjHcP.css | docs/baseline/T015/rollback-source/app/static/assets/index-BaiwjHcP.css | copied |
| docs/baseline/T015/rollback-source/app/static/index.html | docs/baseline/T015/rollback-source/app/static/index.html | copied |
| docs/baseline/T015/rollback-source/frontend/index.html | docs/baseline/T015/rollback-source/frontend/index.html | copied |
| docs/baseline/T015/rollback-source/frontend/package.json | docs/baseline/T015/rollback-source/frontend/package.json | copied |
| docs/baseline/T015/rollback-source/frontend/src/App.jsx | docs/baseline/T015/rollback-source/frontend/src/App.jsx | copied |
| docs/baseline/T015/rollback-source/frontend/src/main.jsx | docs/baseline/T015/rollback-source/frontend/src/main.jsx | copied |
| docs/baseline/T015/rollback-source/frontend/src/styles.css | docs/baseline/T015/rollback-source/frontend/src/styles.css | copied |
| docs/baseline/T015/rollback-source/frontend/src/utils.js | docs/baseline/T015/rollback-source/frontend/src/utils.js | copied |
| docs/baseline/T015/rollback-source/frontend/vite.config.js | docs/baseline/T015/rollback-source/frontend/vite.config.js | copied |
| docs/baseline/T015/rollback-source/notebooks/08_ShieldVI_Dashboard_Colab.ipynb | docs/baseline/T015/rollback-source/notebooks/08_ShieldVI_Dashboard_Colab.ipynb | copied |
| docs/baseline/T015/rollback-source/notebooks/09_ShieldVI_V3_Hybrid_Review_Colab.ipynb | docs/baseline/T015/rollback-source/notebooks/09_ShieldVI_V3_Hybrid_Review_Colab.ipynb | copied |
| docs/baseline/T015/rollback-source/pytest.ini | docs/baseline/T015/rollback-source/pytest.ini | copied |
| docs/baseline/T015/rollback-source/README.md | docs/baseline/T015/rollback-source/README.md | copied |
| docs/baseline/T015/rollback-source/requirements-dev.txt | docs/baseline/T015/rollback-source/requirements-dev.txt | copied |
| docs/baseline/T015/rollback-source/requirements.txt | docs/baseline/T015/rollback-source/requirements.txt | copied |
| docs/baseline/T015/rollback-source/run_windows_dashboard.bat | docs/baseline/T015/rollback-source/run_windows_dashboard.bat | copied |
| docs/baseline/T015/rollback-source/scripts/check_dashboard.py | docs/baseline/T015/rollback-source/scripts/check_dashboard.py | copied |
| docs/baseline/T015/rollback-source/scripts/evaluate_social_policy.py | docs/baseline/T015/rollback-source/scripts/evaluate_social_policy.py | copied |
| docs/baseline/T015/rollback-source/scripts/import_lexicon.py | docs/baseline/T015/rollback-source/scripts/import_lexicon.py | copied |
| docs/baseline/T015/rollback-source/scripts/prepare_social_datasets.py | docs/baseline/T015/rollback-source/scripts/prepare_social_datasets.py | copied |
| docs/baseline/T015/rollback-source/scripts/refine_last_block.py | docs/baseline/T015/rollback-source/scripts/refine_last_block.py | copied |
| docs/baseline/T015/rollback-source/scripts/refine_model.py | docs/baseline/T015/rollback-source/scripts/refine_model.py | copied |
| docs/baseline/T015/rollback-source/tests/conftest.py | docs/baseline/T015/rollback-source/tests/conftest.py | copied |
| docs/baseline/T015/rollback-source/tests/test_api.py | docs/baseline/T015/rollback-source/tests/test_api.py | copied |
| docs/baseline/T015/rollback-source/tests/test_engine.py | docs/baseline/T015/rollback-source/tests/test_engine.py | copied |
| docs/baseline/T015/rollback-source/tests/test_evaluation.py | docs/baseline/T015/rollback-source/tests/test_evaluation.py | copied |
| docs/baseline/T015/rollback-source/tests/test_internal_privacy.py | docs/baseline/T015/rollback-source/tests/test_internal_privacy.py | copied |
| docs/baseline/T015/rollback-source/tests/test_lexical.py | docs/baseline/T015/rollback-source/tests/test_lexical.py | copied |
| docs/baseline/T015/rollback-source/tests/test_lexicon_data.py | docs/baseline/T015/rollback-source/tests/test_lexicon_data.py | copied |
| docs/baseline/T015/rollback-source/tests/test_model_refinement.py | docs/baseline/T015/rollback-source/tests/test_model_refinement.py | copied |
| docs/baseline/T015/rollback-source/tests/test_moderation_adapter.py | docs/baseline/T015/rollback-source/tests/test_moderation_adapter.py | copied |
| docs/baseline/T015/rollback-source/tests/test_social_datasets.py | docs/baseline/T015/rollback-source/tests/test_social_datasets.py | copied |
| docs/baseline/T015/rollback-source-real-server.txt | docs/baseline/T015/rollback-source-real-server.txt | copied |
| docs/baseline/T015/run_rollback.ps1 | docs/baseline/T015/run_rollback.ps1 | copied |
| docs/baseline/T015/snapshot_before.py | docs/baseline/T015/snapshot_before.py | copied |
| docs/baseline/T015/social-build.txt | docs/baseline/T015/social-build.txt | copied |
| docs/baseline/T015/social-pytest.txt | docs/baseline/T015/social-pytest.txt | copied |
| docs/baseline/T015/social-regression/api-server.txt | docs/baseline/T015/social-regression/api-server.txt | copied |
| docs/baseline/T015/social-regression/browser/.last-run.json | docs/baseline/T015/social-regression/browser/.last-run.json | copied |
| docs/baseline/T015/social-regression/browser/desktop-feed.png | docs/baseline/T015/social-regression/browser/desktop-feed.png | copied |
| docs/baseline/T015/social-regression/browser/desktop-login.png | docs/baseline/T015/social-regression/browser/desktop-login.png | copied |
| docs/baseline/T015/social-regression/browser/mobile-login.png | docs/baseline/T015/social-regression/browser/mobile-login.png | copied |
| docs/baseline/T015/social-regression/browser/mobile-thread.png | docs/baseline/T015/social-regression/browser/mobile-thread.png | copied |
| docs/baseline/T015/social-regression/browser-tests.txt | docs/baseline/T015/social-regression/browser-tests.txt | copied |
| docs/baseline/T015/social-regression/web-server.txt | docs/baseline/T015/social-regression/web-server.txt | copied |
| docs/baseline/T015/update_notebooks.py | docs/baseline/T015/update_notebooks.py | copied |
| docs/baseline/T015/verify_integrity.py | docs/baseline/T015/verify_integrity.py | copied |
| docs/baseline/T016/legacy-integrity.json | docs/baseline/T016/legacy-integrity.json | copied |
| docs/baseline/T016/legacy-pytest.txt | docs/baseline/T016/legacy-pytest.txt | copied |
| docs/baseline/T016/policy-tests.txt | docs/baseline/T016/policy-tests.txt | copied |
| docs/architecture/DATABASE.md | docs/architecture/DATABASE.md | copied_and_adapted_paths_or_routing |
| docs/guides/DEMO_ABCD.md | docs/guides/DEMO_ABCD.md | copied |
| docs/architecture/MIGRATION.md | docs/architecture/MIGRATION.md | copied |
| docs/guides/RUN_LOCAL.md | docs/guides/RUN_LOCAL.md | copied_and_adapted_paths_or_routing |
| docs/archive/implementation_reports/T007_REPO_BLUEPRINT.md | docs/archive/implementation_reports/T007_REPO_BLUEPRINT.md | copied |
| docs/archive/implementation_reports/T012_T017_WORKER_REPORT.md | docs/archive/implementation_reports/T012_T017_WORKER_REPORT.md | copied_and_adapted_paths_or_routing |
| docs/archive/implementation_reports/T013_T018_ADMIN_REPORT.md | docs/archive/implementation_reports/T013_T018_ADMIN_REPORT.md | copied_and_adapted_paths_or_routing |
| docs/archive/implementation_reports/T014_T019_VALIDATION_REPORT.md | docs/archive/implementation_reports/T014_T019_VALIDATION_REPORT.md | copied |
| docs/archive/implementation_reports/T015_MIGRATION_REPORT.md | docs/archive/implementation_reports/T015_MIGRATION_REPORT.md | copied_and_adapted_paths_or_routing |
| docs/architecture/T016_POLICY_SPEC.md | docs/architecture/T016_POLICY_SPEC.md | copied |
| docs/archive/legacy_guides/HUONG_DAN_SAO_CHEP.md | docs/archive/legacy_guides/HUONG_DAN_SAO_CHEP.md | copied_and_adapted_paths_or_routing |
| docs/archive/legacy_guides/PROMPT_CODEX_KHOI_DONG.md | docs/archive/legacy_guides/PROMPT_CODEX_KHOI_DONG.md | copied |
| docs/archive/legacy_guides/PROMPT_CODEX_TAI_LIEU.md | docs/archive/legacy_guides/PROMPT_CODEX_TAI_LIEU.md | copied |
| README.md | docs/design/README.md | copied_and_adapted_paths_or_routing |
| tasks/integration/T007-repo-blueprint.md | tasks/integration/T007-repo-blueprint.md | copied |
| tasks/integration/T012-moderation-jobs.md | tasks/integration/T012-moderation-jobs.md | copied |
| tasks/integration/T014-e2e-security.md | tasks/integration/T014-e2e-security.md | copied |
| tasks/integration/T015-migrate-legacy.md | tasks/integration/T015-migrate-legacy.md | copied |
| tasks/integration/T016-policy-design.md | tasks/integration/T016-policy-design.md | copied |
| tasks/integration/T017-durable-worker-and-offline.md | tasks/integration/T017-durable-worker-and-offline.md | copied |
| tasks/integration/T019-evaluation-and-privacy.md | tasks/integration/T019-evaluation-and-privacy.md | copied |
| tasks/moderation-ai/README_AI_UPDATE.md | tasks/moderation-ai/README_AI_UPDATE.md | copied |
| tasks/moderation-ai/T011-moderation-adapter.md | tasks/moderation-ai/T011-moderation-adapter.md | copied |
| tasks/moderation-ai/T020-audit-ai-snapshot-baseline.md | tasks/moderation-ai/T020-audit-ai-snapshot-baseline.md | copied |
| tasks/moderation-ai/T021-regression-fixtures-provisional-annotation.md | tasks/moderation-ai/T021-regression-fixtures-provisional-annotation.md | copied |
| tasks/moderation-ai/T022-context-signals-apology-quote-defense-inte.md | tasks/moderation-ai/T022-context-signals-apology-quote-defense-inte.md | copied |
| tasks/moderation-ai/T023-lexicon-vi-en-teencode-expansion.md | tasks/moderation-ai/T023-lexicon-vi-en-teencode-expansion.md | copied |
| tasks/moderation-ai/T024-target-detection-v3-explicit-and-abstain.md | tasks/moderation-ai/T024-target-detection-v3-explicit-and-abstain.md | copied |
| tasks/moderation-ai/T025-repeated-harassment-v3-evidence-aware.md | tasks/moderation-ai/T025-repeated-harassment-v3-evidence-aware.md | copied |
| tasks/moderation-ai/T026-api-schema-dashboard-signals-policy-bounda.md | tasks/moderation-ai/T026-api-schema-dashboard-signals-policy-bounda.md | copied |
| tasks/moderation-ai/T027-data-ingestion-provenance-for-hard-cases.md | tasks/moderation-ai/T027-data-ingestion-provenance-for-hard-cases.md | copied |
| tasks/moderation-ai/T028-independent-evaluation-solo-review-protoco.md | tasks/moderation-ai/T028-independent-evaluation-solo-review-protoco.md | copied |
| tasks/moderation-ai/T029-optional-train-candidate-visobert-on-colab.md | tasks/moderation-ai/T029-optional-train-candidate-visobert-on-colab.md | copied |
| tasks/moderation-ai/T030-paired-offline-evaluation-ablation.md | tasks/moderation-ai/T030-paired-offline-evaluation-ablation.md | copied |
| tasks/moderation-ai/T031-optional-model-registry-shadow-and-rollbac.md | tasks/moderation-ai/T031-optional-model-registry-shadow-and-rollbac.md | copied |
| tasks/moderation-ai/T032-social-ai-integration-offline-safety-e2e.md | tasks/moderation-ai/T032-social-ai-integration-offline-safety-e2e.md | copied |
| tasks/moderation-ai/T033-technical-report-thesis-handoff.md | tasks/moderation-ai/T033-technical-report-thesis-handoff.md | copied |
| tasks/moderation-ai/TASK_ORDER_AI.md | tasks/moderation-ai/TASK_ORDER_AI.md | copied |
| tasks/moderation-web/T013-admin-review.md | tasks/moderation-web/T013-admin-review.md | copied |
| tasks/moderation-web/T018-admin-appeals-audit.md | tasks/moderation-web/T018-admin-appeals-audit.md | copied |
| tasks/README_SOCIAL.md | tasks/README_SOCIAL.md | copied |
| tasks/social-api/T008-auth-database.md | tasks/social-api/T008-auth-database.md | copied |
| tasks/social-api/T009-social-content.md | tasks/social-api/T009-social-content.md | copied |
| tasks/social-web/T010-social-frontend.md | tasks/social-web/T010-social-frontend.md | copied |
| tasks/TASK_ORDER.md | tasks/TASK_ORDER.md | copied_and_adapted_paths_or_routing |
| templates/experiment_manifest.example.json | templates/experiment_manifest.example.json | copied |
| templates/solo_review_template.csv | templates/solo_review_template.csv | copied |
| tests/test_policy_design.py | tests/test_policy_design.py | copied_and_adapted_paths_or_routing |

## Điểm dừng

Dừng sau tổ chức tài liệu và kiểm tra. Mở ShieldVI_V3_Hybrid_Review trong VS Code để làm việc tiếp. Các thư mục ShieldVI_SocialAI_Design_Docs_v1 và ShieldVI_AI_Update_Codex_Tasks_v1 bên ngoài root là bản dự phòng, không phải nơi chỉnh sửa tiếp.

