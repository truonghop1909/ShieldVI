# Tổ chức tài liệu ShieldVI — 04/11/2026

Tài liệu được tập trung dưới `docs/`; bắt đầu tại [mục lục](README.md).

## Kết quả

- Di chuyển 38 tài liệu hướng dẫn, kiến trúc và module vào nhóm phù hợp.
- Gộp ghi chú compatibility frontend vào hướng dẫn legacy research dashboard.
- Bỏ trang demo chỉ trỏ sang guide hiện hành; cập nhật tham chiếu về guide đó.
- Sửa liên kết và đường dẫn trong 53 file thuộc đợt di chuyển chính.
- Không có tài liệu độc lập trùng byte trong phạm vi tài liệu chính. Hai file bỏ
  đi là trang chỉ dẫn dư và ghi chú đã gộp đầy đủ; không xóa các bản khác nội dung
  chỉ vì cùng tên. README V3 và prompt cũ được chuyển vào khu lưu trữ.

## Cấu trúc

| Nhóm | Nội dung |
|---|---|
| `docs/README.md` | Điểm bắt đầu chung |
| `architecture/` | Kiến trúc hiện thực, database, API, migration, policy |
| `design/` | Bộ thiết kế Social ban đầu |
| `guides/` | Runbook và giải thích demo |
| `modules/` | Hướng dẫn backend/frontend và legacy dashboard |
| `ai-update/` | Quy trình, thực nghiệm và báo cáo AI theo phiên bản |
| `realtime_moderation/`, `ml_studio/` | Chi tiết realtime và ML Studio |
| `archive/` | Báo cáo triển khai, hướng dẫn và prompt lịch sử |
| `governance/` | Phụ lục quy tắc tham khảo |

## Các vị trí cần giữ

`AGENTS.md` là chỉ dẫn công cụ; README ở root chỉ liên kết tới mục lục.
`tasks/`, `.agents/skills/` và `contracts/` giữ quy ước hoạt động. README/license
cạnh dataset, model, lexicon là metadata provenance, không phải bản hướng dẫn
sản phẩm bị duy trì trùng. Snapshot `docs/baseline/`,
`docs/repository-merge-evidence/`, các bằng chứng kiểm thử và gói nguồn bên ngoài
repository được giữ nguyên.

Không sửa code runtime, checkpoint V1/r06, threshold 0.41, dataset hoặc database.
Giữ nguyên cả 37 trạng thái task. Các manifest SHA cũ là snapshot lịch sử;
bản đồ di chuyển và hash mới được ghi riêng.

## Phục hồi và kiểm tra

Bản sao nguyên byte của 61 file bị di chuyển/sửa/gộp nằm trong
`reports/docs_cleanup_20261104/before.zip`; bản sao chỉ mục AI trước khi bổ sung
liên kết hướng dẫn mới nằm trong `before_index_update.zip` cùng thư mục.
Tổng cộng 62 bản gốc đã được kiểm tra SHA. Bản đồ và kết quả kiểm tra nằm ở
`PLAN.json`, `APPLIED.json`, `VALIDATION.json`, `readiness.log` và
`FILES_SHA256.json` cùng thư mục. Không giải nén đè toàn repository; dùng bản đồ
để phục hồi đúng file cần thiết.

Kiểm tra từ repository root:

```powershell
.\.venv\Scripts\python.exe reports/docs_cleanup_20261104/validate_docs.py
.\.venv\Scripts\python.exe scripts/verify_ai_readiness_lock.py --lock reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json
```

Kiểm tra bao gồm vị trí file, nội dung bản sao ZIP, các liên kết tương đối,
metadata skill, trạng thái task, trùng nội dung và readiness lock. Không cần
build frontend hoặc chạy training vì source runtime không thay đổi.

## Bản đồ file

| Vị trí cũ (tính từ root) | Vị trí hiện tại |
|---|---|
| `docs/00_MUC_LUC.md` | `docs/design/00_MUC_LUC.md` |
| `docs/01_PHAM_VI_MVP.md` | `docs/design/01_PHAM_VI_MVP.md` |
| `docs/02_KIEN_TRUC.md` | `docs/design/02_KIEN_TRUC.md` |
| `docs/03_CHINH_SACH_KIEM_DUYET.md` | `docs/design/03_CHINH_SACH_KIEM_DUYET.md` |
| `docs/04_VONG_DOI_NOI_DUNG.md` | `docs/design/04_VONG_DOI_NOI_DUNG.md` |
| `docs/05_LUONG_NGUOI_DUNG.md` | `docs/design/05_LUONG_NGUOI_DUNG.md` |
| `docs/06_DU_LIEU.md` | `docs/design/06_DU_LIEU.md` |
| `docs/07_API.md` | `docs/design/07_API.md` |
| `docs/08_BAO_MAT_QUYEN_RIENG_TU.md` | `docs/design/08_BAO_MAT_QUYEN_RIENG_TU.md` |
| `docs/09_TEST_DANH_GIA.md` | `docs/design/09_TEST_DANH_GIA.md` |
| `docs/10_KE_HOACH_CODEX.md` | `docs/design/10_KE_HOACH_CODEX.md` |
| `docs/11_QUYET_DINH_VA_CAU_HOI_MO.md` | `docs/design/11_QUYET_DINH_VA_CAU_HOI_MO.md` |
| `docs/API_CONTRACT.md` | `docs/architecture/API_CONTRACT.md` |
| `docs/ARCHITECTURE.md` | `docs/architecture/ARCHITECTURE.md` |
| `docs/DATABASE.md` | `docs/architecture/DATABASE.md` |
| `docs/DEMO_ABCD.md` | `docs/guides/DEMO_ABCD.md` |
| `docs/MIGRATION.md` | `docs/architecture/MIGRATION.md` |
| `docs/REPOSITORY_MERGE_REPORT.md` | `docs/archive/merges/REPOSITORY_MERGE_REPORT.md` |
| `docs/RUN_LOCAL.md` | `docs/guides/RUN_LOCAL.md` |
| `docs/SOCIAL_DESIGN_README.md` | `docs/design/README.md` |
| `docs/T007_REPO_BLUEPRINT.md` | `docs/archive/implementation_reports/T007_REPO_BLUEPRINT.md` |
| `docs/T012_T017_WORKER_REPORT.md` | `docs/archive/implementation_reports/T012_T017_WORKER_REPORT.md` |
| `docs/T013_T018_ADMIN_REPORT.md` | `docs/archive/implementation_reports/T013_T018_ADMIN_REPORT.md` |
| `docs/T014_T019_VALIDATION_REPORT.md` | `docs/archive/implementation_reports/T014_T019_VALIDATION_REPORT.md` |
| `docs/T015_MIGRATION_REPORT.md` | `docs/archive/implementation_reports/T015_MIGRATION_REPORT.md` |
| `docs/T016_POLICY_SPEC.md` | `docs/architecture/T016_POLICY_SPEC.md` |
| `README.md` | `docs/archive/legacy_guides/V3_OVERVIEW.md` |
| `CHANGELOG.md` | `docs/CHANGELOG.md` |
| `AGENTS_SOCIAL_ADDENDUM.md` | `docs/governance/AGENTS_SOCIAL_ADDENDUM.md` |
| `HUONG_DAN_SAO_CHEP.md` | `docs/archive/legacy_guides/HUONG_DAN_SAO_CHEP.md` |
| `PROMPT_CODEX_KHOI_DONG.md` | `docs/archive/legacy_guides/PROMPT_CODEX_KHOI_DONG.md` |
| `PROMPT_CODEX_TAI_LIEU.md` | `docs/archive/legacy_guides/PROMPT_CODEX_TAI_LIEU.md` |
| `services/social-api/README.md` | `docs/modules/social_api.md` |
| `services/moderation-ai/README.md` | `docs/modules/moderation_ai.md` |
| `apps/social-web/README.md` | `docs/modules/social_web.md` |
| `apps/moderation-web/README.md` | `docs/modules/moderation_web.md` |
| `apps/moderation-web/legacy-v3/README.md` | `docs/modules/legacy_research_dashboard.md` |
| `examples/DEMO_HYBRID_GIAI_THICH.md` | `docs/guides/DEMO_HYBRID_GIAI_THICH.md` |
| `frontend/README.md` (gộp) | `docs/modules/legacy_research_dashboard.md` |
| `docs/demo/REALTIME_TRAINING_DEMO.md` (bỏ trang trỏ dư) | `docs/ai-update/final-report/REALTIME_DEMO_GUIDE.md` |

SHA256 bản sao ZIP: `61bd4b17bfdc478c1c2b2e97baafd4f4a6bfa59fb031a06dc18ec1e06f37c32b`.
