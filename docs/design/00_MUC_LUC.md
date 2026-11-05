# 00 — Mục lục & cách dùng tài liệu

| Tài liệu | Trả lời câu hỏi |
|---|---|
| `01_PHAM_VI_MVP.md` | Phiên bản đầu tiên cần có những chức năng gì? |
| `02_KIEN_TRUC.md` | Frontend/backend/DB/worker tương tác ra sao? |
| `03_CHINH_SACH_KIEM_DUYET.md` | AI làm gì khi Admin không online? |
| `04_VONG_DOI_NOI_DUNG.md` | Bài viết/bình luận qua các trạng thái nào? |
| `05_LUONG_NGUOI_DUNG.md` | Từng vai trò nhìn thấy gì, thao tác thế nào? |
| `06_DU_LIEU.md` | Schema DB, phiên bản, audit, không mất dữ liệu? |
| `07_API.md` | REST API và hợp đồng giữa hai backend? |
| `08_BAO_MAT_QUYEN_RIENG_TU.md` | Bảo vệ tài khoản, dữ liệu nhạy cảm, tránh lạm dụng? |
| `09_TEST_DANH_GIA.md` | Đo chất lượng AI và test hệ thống thế nào? |
| `10_KE_HOACH_CODEX.md` | Codex thực hiện task/skill theo trình tự nào? |
| `11_QUYET_DINH_VA_CAU_HOI_MO.md` | Phạm vi đã chốt và vấn đề chưa chốt? |

## Từ vựng chuẩn
- **`ai_label`**: dự đoán `CLEAN | TOXIC` của mô hình, *không phải* quyết định Admin.
- **`ai_score`**: xác suất/điểm mô hình hiện hành; không đồng nghĩa mức độ nghiêm trọng.
- **`lexical_signals`**: từ/cụm từ đáng chú ý. Dấu hiệu không đủ chứng minh xúc phạm.
- **`risk_tier`**: `LOW | REVIEW | HIGH | UNKNOWN` do policy engine quyết định từ nhiều bằng chứng; cần hiệu chuẩn.
- **`visibility_status`**: quyền hiển thị bài viết/bình luận, do Social API quản lý.
- **`review_status`**: có/không cần người duyệt, kết quả duyệt.
- **`policy_version`**: phiên bản luật tự động để có thể tra cứu và rollback.
- **`model_version`**: checkpoint và cấu hình mô hình đã dùng.

Không dùng lẫn `ai_label=TOXIC`, `risk_tier=HIGH` và `visibility_status=HIDDEN`.

## AI Update

[Phạm vi](../ai-update/00_READ_ME_FIRST.md) · [Ghi chú hai root và điểm chờ quyết định](../ai-update/INTEGRATION_NOTES.md) · [Thứ tự toàn dự án](../../tasks/TASK_ORDER.md) · [Báo cáo gộp](../ai-update/MERGE_REPORT.md). Chỉ đọc tài liệu AI liên quan task đang được giao.
