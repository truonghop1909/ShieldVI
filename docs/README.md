# Tài liệu ShieldVI

Đây là đầu mối tài liệu của dự án. Tài liệu hướng dẫn, kiến trúc, module và báo
cáo đều nằm dưới `docs/`; chọn mục phù hợp thay vì đọc toàn bộ thư mục.

## Chạy và sử dụng

| Bạn muốn làm gì? | Đọc ở đây |
|---|---|
| Chạy bảng tin với năm nick, moderator và Studio | [Demo Windows](ai-update/final-report/REALTIME_DEMO_GUIDE.md) |
| Xem nghiệm thu bổ sung Social Feed v2 | [Social Feed v2](realtime_moderation/SOCIAL_FEED_V2_ACCEPTANCE.md) |
| Xem responsive UI, ảnh before/after và kiểm thử nhiều màn hình | [Responsive UI report](realtime_moderation/RESPONSIVE_UI_REPORT.md) |
| Xem sửa lỗi resize cửa sổ Chrome thực, desktop1650 và tablet850 | [Responsive visual fix](realtime_moderation/RESPONSIVE_VISUAL_FIX_REPORT.md) |
| Kiểm tra môi trường, lệnh chạy và dừng | [Windows setup](ai-update/final-report/WINDOWS_SETUP_GUIDE.md) |
| Nhập dataset và gán nhãn hai vòng | [Dataset & annotation](ai-update/final-report/DATASET_ANNOTATION_GUIDE.md) |
| Huấn luyện candidate CPU và xem kết quả | [Training Studio](ai-update/final-report/TRAINING_STUDIO_GUIDE.md) |
| Chạy các dịch vụ Social theo cách thủ công | [Runbook](guides/RUN_LOCAL.md) |
| Xem tình trạng triển khai và giới hạn | [Báo cáo T034–T043](ai-update/final-report/T034_T043_FINAL_REPORT.md) |

Lệnh demo chạy từ **thư mục gốc dự án**; runbook module ghi thư mục làm việc
riêng khi cần. Khi mở demo, giữ cửa sổ
PowerShell và chờ `DEMO_READY`; Ctrl+C dùng để dừng. Dataset synthetic không phải
human gold; kết quả thử nghiệm không tự cho phép đổi model mặc định hoặc deploy.

## Kiến trúc và module

| Nhóm | Tài liệu |
|---|---|
| Kiến trúc hiện thực | [Architecture](architecture/ARCHITECTURE.md), [Database](architecture/DATABASE.md), [API](architecture/API_CONTRACT.md) |
| Chính sách và migration | [Policy](architecture/T016_POLICY_SPEC.md), [Migration](architecture/MIGRATION.md) |
| Backend | [Social API](modules/social_api.md), [Moderation AI](modules/moderation_ai.md) |
| Frontend | [Social Web](modules/social_web.md), [Moderator Web](modules/moderation_web.md) |
| Dashboard nghiên cứu V3 và compatibility | [Legacy research dashboard](modules/legacy_research_dashboard.md) |
| Realtime | [Architecture](realtime_moderation/ARCHITECTURE.md), [Internal AI](realtime_moderation/INCREMENTAL_AI.md), [Moderator](realtime_moderation/MODERATOR_LIVE.md) |
| ML Studio | [Datasets](ml_studio/DATASETS.md), [Annotation](ml_studio/ANNOTATION.md), [Training](ml_studio/TRAINING.md), [Evaluation](ml_studio/EVALUATION.md) |
| Thiết kế Social ban đầu | [Mục lục thiết kế](design/00_MUC_LUC.md) |

## Nghiên cứu, lịch sử và quản lý

- [Tóm tắt đề tài, yêu cầu và hướng phát triển — Word 2 trang](ai-update/final-report/ShieldVI_Tom_tat_de_tai_2_trang.docx).
- [AI Update và báo cáo nghiên cứu](ai-update/final-report/README.md).
- [Thiếu bằng chứng real-world và formal acceptance](ai-update/final-report/FINAL_READINESS_REPORT.md).
- [Lịch sử thay đổi](CHANGELOG.md), [tài liệu lưu trữ](archive/README.md).
- [Thứ tự task](../tasks/TASK_ORDER.md), [tiến độ thực tế](../tasks/AUTO_PROGRESS.md).
- [Contracts](../contracts/), [metadata dataset](../datasets/README.md).
- [Báo cáo tổ chức tài liệu](ORGANIZATION.md).

`AGENTS.md`, `tasks/` và `.agents/skills/` giữ vị trí theo quy ước của công cụ.
README/license đi kèm dataset, model hoặc nguồn từ điển là metadata provenance;
chúng ở cạnh artifact tương ứng. Snapshot `baseline/`, bằng chứng cũ và các gói
nguồn ngoài repository được giữ nguyên để có thể xác minh lịch sử.
