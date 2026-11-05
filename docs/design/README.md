> Tài liệu thiết kế gốc được giữ để tra cứu. Hiện tài liệu đã gộp vào root dự án; dùng [README chạy dự án](../README.md) và [TASK_ORDER](../../tasks/TASK_ORDER.md). Không chép gói hoặc bắt đầu task chỉ vì đọc hướng dẫn lịch sử bên dưới.

# SHIELDVI SOCIAL AI — BỘ TÀI LIỆU THIẾT KẾ V1

**Trạng thái:** DESIGN / TÀI LIỆU TRƯỚC KHI VIẾT CODE. Đây không phải source code mạng xã hội chạy ngay.

**Mục tiêu:** tạo mạng xã hội web có đăng ký/đăng nhập, bài viết, bình luận, trả lời, báo cáo vi phạm, kết nối hệ thống AI ViSoBERT hiện có để kiểm duyệt bán tự động. Người kiểm duyệt **không cần trực 24/24**.

**Điều đã chốt:**
1. Giữ nguyên ShieldVI V3 đang chạy (`app/`, `frontend/`, model ViSoBERT V1, threshold 0.41); không ghi đè checkpoint.
2. Tách `services/social-api` khỏi `services/moderation-ai`, và `apps/social-web` khỏi `apps/moderation-web`.
3. Social API là **nguồn sự thật** về trạng thái hiển thị; AI chỉ tạo tín hiệu/đề xuất. Lexicon không tự kết luận TOXIC.
4. 3 luồng vận hành: rủi ro thấp -> đăng; mơ hồ -> đăng và theo dõi; nghiêm trọng -> tạm giữ/ẩn chờ xét duyệt theo **chính sách đã kiểm thử**.
5. Thiết kế có hàng đợi, retry, audit log, kháng nghị và cơ chế khi AI lỗi. Không bắt Admin online liên tục.

## Đọc theo thứ tự

1. `docs/design/00_MUC_LUC.md` — danh mục tài liệu.
2. `docs/design/01_PHAM_VI_MVP.md` — phạm vi sản phẩm và vai trò người dùng.
3. `docs/design/02_KIEN_TRUC.md` — hai backend/hai frontend, worker, DB.
4. `docs/design/03_CHINH_SACH_KIEM_DUYET.md` — 3 mức rủi ro, tránh cảnh báo nhầm.
5. `docs/design/04_VONG_DOI_NOI_DUNG.md` — state machine và quyết định Admin.
6. `docs/design/05_LUONG_NGUOI_DUNG.md` — luồng sử dụng mạng xã hội + Admin offline.
7. `docs/design/06_DU_LIEU.md` và `docs/design/07_API.md` — database và hợp đồng API.
8. `docs/design/08_BAO_MAT_QUYEN_RIENG_TU.md`, `docs/design/09_TEST_DANH_GIA.md`.
9. `docs/design/10_KE_HOACH_CODEX.md` — chia task, nghiệm thu, không phá code cũ.
10. `docs/design/11_QUYET_DINH_VA_CAU_HOI_MO.md` — quyết định và điểm chờ xác nhận.

**Nhập vào repository:** copy thư mục `docs/`, `contracts/`, `tasks/` (gộp các file mới), `.agents/skills/` (gộp), file `docs/archive/legacy_guides/PROMPT_CODEX_TAI_LIEU.md`. **Không ghi đè** `AGENTS.md`, `app/`, `frontend/`; bổ sung nội dung `docs/governance/AGENTS_SOCIAL_ADDENDUM.md` vào file AGENTS.md hiện có sau khi soát trùng.

**Ghi chú vận hành:** Colab dùng để demo/nghiên cứu, không làm dịch vụ moderation công khai chạy liên tục. Các chính sách tự động ẩn chỉ được bật sau khi test và chốt mức rủi ro; không lấy 0.41 làm ngưỡng ẩn mặc định.

## Tài liệu AI Update đã tích hợp

Tài liệu/task tiếp tục được quản lý tại root này; code ở `../ShieldVI_V3_Hybrid_Review/`. Xem [AI Update](../ai-update/00_READ_ME_FIRST.md), [thứ tự dự án](../../tasks/TASK_ORDER.md) và [báo cáo gộp](../ai-update/MERGE_REPORT.md). Việc nhập tài liệu không bắt đầu T020, không train/deploy hay đổi cấu hình.
