> Báo cáo dưới đây ghi lần gộp AI Update trước khi thống nhất root. Hiện tài liệu/code cùng root; xem [báo cáo gộp thư mục tài liệu](../archive/merges/REPOSITORY_MERGE_REPORT.md). Nguồn và số liệu lần trước được giữ làm lịch sử. Validator đi kèm chuyển tiếp sang kiểm tra root hiện tại.

# Báo cáo gộp tài liệu AI Update

Ngày 02/11/2026 (Asia/Saigon). Đích theo lựa chọn người dùng: **ShieldVI_SocialAI_Design_Docs_v1/**. Runtime tiếp tục nằm ở thư mục ngang hàng ShieldVI_V3_Hybrid_Review. Chỉ gộp tài liệu, không triển khai T020 hoặc task AI khác.

## File đã thêm

Giữ nguyên tên task (kể cả tên nguồn rút ngắn), không tạo alias cùng ID. Các file mới từ gói và index/ghi chú:

- `.agents/skills/shieldvi-ai-upgrade/SKILL.md`
- `contracts/ai_signals_v2_draft.example.json`
- `datasets/fixtures/genz_regression/README.md`
- `datasets/fixtures/genz_regression/SHIELDVI_01_GAME_RANK_LAG_30.json`
- `datasets/fixtures/genz_regression/SHIELDVI_02_SHOP_GIAY_SECONDHAND_30.json`
- `datasets/fixtures/genz_regression/SHIELDVI_03_DANCE_COVER_TIKTOK_30.json`
- `datasets/fixtures/genz_regression/SHIELDVI_04_DI_CAMPING_CHIA_TIEN_30.json`
- `datasets/fixtures/genz_regression/SHIELDVI_05_FANART_AI_DISPUTE_30.json`
- `datasets/fixtures/genz_regression/synthetic_reference_tags.csv`
- `docs/ai-update/00_READ_ME_FIRST.md`
- `docs/ai-update/01_FAILURE_CASES.md`
- `docs/ai-update/02_ANNOTATION_GUIDE.md`
- `docs/ai-update/03_EXPERIMENT_PLAN.md`
- `docs/ai-update/04_API_VERSIONING.md`
- `docs/ai-update/05_RELEASE_GATES.md`
- `docs/ai-update/06_COLAB_RUNBOOK.md`
- `docs/ai-update/07_DATA_AND_SECURITY.md`
- `docs/ai-update/INTEGRATION_NOTES.md`
- `docs/ai-update/PACK_README.md`
- `docs/ai-update/PROMPT_CODEX_BAT_DAU.md`
- `docs/ai-update/SOURCE_FILE_MANIFEST.json`
- `tasks/TASK_ORDER.md`
- `tasks/moderation-ai/README_AI_UPDATE.md`
- `tasks/moderation-ai/T020-audit-ai-snapshot-baseline.md`
- `tasks/moderation-ai/T021-regression-fixtures-provisional-annotation.md`
- `tasks/moderation-ai/T022-context-signals-apology-quote-defense-inte.md`
- `tasks/moderation-ai/T023-lexicon-vi-en-teencode-expansion.md`
- `tasks/moderation-ai/T024-target-detection-v3-explicit-and-abstain.md`
- `tasks/moderation-ai/T025-repeated-harassment-v3-evidence-aware.md`
- `tasks/moderation-ai/T026-api-schema-dashboard-signals-policy-bounda.md`
- `tasks/moderation-ai/T027-data-ingestion-provenance-for-hard-cases.md`
- `tasks/moderation-ai/T028-independent-evaluation-solo-review-protoco.md`
- `tasks/moderation-ai/T029-optional-train-candidate-visobert-on-colab.md`
- `tasks/moderation-ai/T030-paired-offline-evaluation-ablation.md`
- `tasks/moderation-ai/T031-optional-model-registry-shadow-and-rollbac.md`
- `tasks/moderation-ai/T032-social-ai-integration-offline-safety-e2e.md`
- `tasks/moderation-ai/T033-technical-report-thesis-handoff.md`
- `tasks/moderation-ai/TASK_ORDER_AI.md`
- `templates/experiment_manifest.example.json`
- `templates/solo_review_template.csv`
- `docs/ai-update/MERGE_REPORT.md` — báo cáo này.
- `docs/ai-update/merge-evidence/MERGE_MANIFEST.json` — mapping/hash trước và sau, kiểm kê từng file nguồn.
- `docs/ai-update/merge-evidence/validate_merge.py` — kiểm tra tính toàn vẹn tài liệu, không chạy task AI.
- `docs/ai-update/merge-evidence/VALIDATION_RESULTS.json` — kết quả kiểm tra có thể tái lập.

## File đã gộp

- `AGENTS.md`
- `.agents/skills/shieldvi-ai-integration/SKILL.md`
- `tasks/README_SOCIAL.md`
- `docs/design/00_MUC_LUC.md`
- `README.md`

- AGENTS: chỉ bổ sung quy tắc AI còn thiếu, liên kết chi tiết sang skill/docs; giới hạn báo cáo đổi từ 100 sang 120 từ theo yêu cầu. Giữ quy tắc token, checkpoint V1/threshold 0.41, không tự train/test mutation, test trước nghiệm thu, đúng scope.
- Metadata AI Update đặt nhầm cuối skill integration được chuyển sang skill mới, workflow integration được giữ nguyên. Body skill mới là bản tái lập từ nội dung còn nguyên, không tuyên bố khôi phục byte nguồn thiếu.
- README gói nguồn được đặt thành PACK_README.md trong docs/ai-update, không ghi đè README dự án. Prompt mẫu đặt cùng docs/ai-update, bỏ yêu cầu đọc addendum riêng đã gộp vào AGENTS/skill; không thực thi prompt.
- AGENTS_AI_ADDENDUM.md không cài thêm bản trùng; toàn bộ quy tắc được đối chiếu vào AGENTS/skill/docs. Bản gốc vẫn nằm ở thư mục nguồn.
- tasks/TASK_ORDER.md tổng hợp T007–T033, giữ TASK_ORDER_AI nguyên byte, thêm liên hệ T026/T032 với Social adapter/policy/worker/UI/E2E. T029/T031 vẫn cần duyệt riêng. T001–T006 được tài liệu cũ nhắc nhưng không có file để xác nhận, không tự tạo trạng thái.

## File giữ nguyên

13 task cũ T007–T019 giữ nguyên byte và trạng thái DONE có sẵn; không đánh giá lại hoặc tự xác nhận DONE. 14 task AI T020–T033 và TASK_ORDER_AI giữ nguyên byte/TODO từ gói. Toàn bộ contracts đang áp dụng không bị thay. Các file có trước giữ nguyên hash:

- `.agents/skills/shieldvi-architecture-migration/SKILL.md`
- `.agents/skills/shieldvi-moderation-admin/SKILL.md`
- `.agents/skills/shieldvi-moderation-policy/SKILL.md`
- `.agents/skills/shieldvi-social-backend/SKILL.md`
- `.agents/skills/shieldvi-social-frontend/SKILL.md`
- `docs/governance/AGENTS_SOCIAL_ADDENDUM.md`
- `docs/CHANGELOG.md`
- `contracts/moderation_policy.example.json`
- `contracts/moderation_request.example.json`
- `contracts/moderation_request.schema.json`
- `contracts/moderation_response.example.json`
- `contracts/moderation_response.schema.json`
- `contracts/policy_acceptance_cases.json`
- `contracts/social-auth.openapi.json`
- `contracts/social-content.openapi.json`
- `contracts/social-review.openapi.json`
- `contracts/social-worker.openapi.json`
- `docs/design/01_PHAM_VI_MVP.md`
- `docs/design/02_KIEN_TRUC.md`
- `docs/design/03_CHINH_SACH_KIEM_DUYET.md`
- `docs/design/04_VONG_DOI_NOI_DUNG.md`
- `docs/design/05_LUONG_NGUOI_DUNG.md`
- `docs/design/06_DU_LIEU.md`
- `docs/design/07_API.md`
- `docs/design/08_BAO_MAT_QUYEN_RIENG_TU.md`
- `docs/design/09_TEST_DANH_GIA.md`
- `docs/design/10_KE_HOACH_CODEX.md`
- `docs/design/11_QUYET_DINH_VA_CAU_HOI_MO.md`
- `docs/architecture/API_CONTRACT.md`
- `docs/architecture/ARCHITECTURE.md`
- `docs/architecture/DATABASE.md`
- `docs/guides/DEMO_ABCD.md`
- `docs/architecture/MIGRATION.md`
- `docs/guides/RUN_LOCAL.md`
- `docs/archive/implementation_reports/T007_REPO_BLUEPRINT.md`
- `docs/archive/implementation_reports/T012_T017_WORKER_REPORT.md`
- `docs/archive/implementation_reports/T013_T018_ADMIN_REPORT.md`
- `docs/archive/implementation_reports/T014_T019_VALIDATION_REPORT.md`
- `docs/archive/implementation_reports/T015_MIGRATION_REPORT.md`
- `docs/architecture/T016_POLICY_SPEC.md`
- `docs/archive/legacy_guides/HUONG_DAN_SAO_CHEP.md`
- `docs/archive/legacy_guides/PROMPT_CODEX_KHOI_DONG.md`
- `docs/archive/legacy_guides/PROMPT_CODEX_TAI_LIEU.md`
- `tasks/integration/T007-repo-blueprint.md`
- `tasks/integration/T012-moderation-jobs.md`
- `tasks/integration/T014-e2e-security.md`
- `tasks/integration/T015-migrate-legacy.md`
- `tasks/integration/T016-policy-design.md`
- `tasks/integration/T017-durable-worker-and-offline.md`
- `tasks/integration/T019-evaluation-and-privacy.md`
- `tasks/moderation-ai/T011-moderation-adapter.md`
- `tasks/moderation-web/T013-admin-review.md`
- `tasks/moderation-web/T018-admin-appeals-audit.md`
- `tasks/social-api/T008-auth-database.md`
- `tasks/social-api/T009-social-content.md`
- `tasks/social-web/T010-social-frontend.md`

Toàn bộ **39 file nguồn** còn nguyên tên/nội dung/hash, gồm cả SKILL.md bị thiếu. Không xóa thư mục ShieldVI_AI_Update_Codex_Tasks_v1. Không sao chép fixture vào runtime tạo bản thứ hai. Không đọc toàn bộ source code/dataset; chỉ đọc fixture mới để kiểm tra 150 comment và CSV tham chiếu.

## Xung đột / quyết định còn mở

1. **Nguồn SKILL.md thiếu nội dung:** FILE_MANIFEST đòi 2.015 byte; thực tế 5 byte. 37/38 entry manifest khớp, một entry sai. Skill được cài là bản hợp lệ tái lập, không trùng hash nguồn dự kiến. Người dùng cần chấp nhận bản tái lập hoặc cung cấp skill gốc để so sánh. Không tự sửa manifest nguồn hoặc giả kết quả toàn vẹn PASS cho gói nguồn.
2. **Baseline V1 so với default V1.1:** gói mới lấy V1/B0; tài liệu T015 hiện tại ghi runtime mặc định V1.1 refined. Giữ cả hai mô tả, chưa chọn baseline cho task thực nghiệm, chưa đổi model/threshold. Cần người dùng xác nhận B0 trước thực nghiệm.
3. **Scope T026/T032:** yêu cầu UI/worker/E2E nhưng scope mẫu chủ yếu moderation-ai. Giữ nguyên task; cần chốt module được phép sửa khi giao triển khai, không tự cấp quyền sửa Social API/Web/Moderation Web.

## Kiểm tra

**Kết quả cuối: PASS, exit code 0 — 26 kiểm tra; 7 skill hợp lệ; 232 liên kết Markdown và 220 tham chiếu đường dẫn đã phân loại; 5 fixture/150 bình luận.** Gói nguồn vẫn có 1 cảnh báo manifest (skill thiếu), không được coi là đã phục hồi nguyên bản. Chạy lần đầu phát hiện liên kết đến file kết quả chưa được tạo; chạy lại sau khi evidence tồn tại đã PASS.

- Lệnh kiểm tra từ root tài liệu: `..\ShieldVI_V3_Hybrid_Review\.venv\Scripts\python.exe -X utf8 docs/ai-update/merge-evidence/validate_merge.py`.
- Kết quả và exit code thực tế được ghi trong [VALIDATION_RESULTS](merge-evidence/VALIDATION_RESULTS.json); [manifest](merge-evidence/MERGE_MANIFEST.json) ghi từng file nguồn/đích và SHA-256. Các nhãn warning nguồn thiếu được tách khỏi kiểm tra cấu trúc sau gộp.
- Kiểm tra đủ 14 task duy nhất, trạng thái không đổi, skill frontmatter hợp lệ và tên không trùng, 5 fixture × 30 comment và 150 dòng tag khớp IDs, JSON/CSV template/contract parse, hash payload copy khớp.
- Kiểm tra mọi liên kết Markdown của tài liệu đang áp dụng và đường dẫn inline trong tài liệu AI. Đường output T020/T021 chưa tồn tại được đánh dấu planned, không tạo giả. Đường legacy app/*.py được đối chiếu canonical service; Colab/API endpoints/placeholder được giải thích trong [INTEGRATION_NOTES](INTEGRATION_NOTES.md). Snapshot baseline lịch sử không sửa/không tái diễn giải.
- Backend/frontend/runtime test và build **CHƯA CHẠY — chỉ gộp tài liệu, không sửa runtime**. Không fine-tune, không download, không đụng checkpoint/database hoặc default selection, không push/deploy. Workspace không có Git metadata; dùng hash thay Git diff, không tạo repository mới.

## Điểm dừng

Kết thúc ở gộp và kiểm tra tài liệu. Không bắt đầu T020, không chuyển bất kỳ task nào sang IN_PROGRESS/DONE. Các quyết định ở trên được giữ mở cho người dùng.

