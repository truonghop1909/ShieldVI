# Prompt mở đầu cho Codex trong VS Code

Sao chép phần dưới đây vào Codex sau khi đã nhập bộ tài liệu vào repository:

---

Bạn là Tech Lead / AI Engineer của dự án ShieldVI Social AI. Tôi làm đồ án một mình.

Hãy đọc file AGENTS.md, README.md, toàn bộ docs/design/00_MUC_LUC.md đến docs/design/11_QUYET_DINH_VA_CAU_HOI_MO.md, `tasks/README_SOCIAL.md`, các task T007/T016/T008 và skill `.agents/skills/shieldvi-moderation-policy/SKILL.md`.

Mục tiêu kiến trúc: tách Social API và AI Moderation API, tách Social Web và Moderation Web; AI phân luồng LOW/REVIEW/HIGH để Admin không phải trực 24/24. Score ViSoBERT 0.41 KHÔNG phải ngưỡng tự ẩn. Hệ thống phải cho user biết nội dung đang chờ, có queue/retry khi AI lỗi, có audit và kháng nghị. Giữ ShieldVI V3 legacy và checkpoint gốc.

**Chỉ làm T007 ở lượt này:**
1. Kiểm kê cấu trúc code hiện tại và các API đang chạy.
2. Đối chiếu tài liệu mới với code, tìm chỗ khác biệt hoặc thiếu.
3. Chạy backend tests hiện có, frontend build nếu môi trường đủ dependency.
4. Lập kế hoạch thực hiện T016 (policy), T008–T012 (Social API, Web, AI Integration) theo thứ tự.
5. Ghi nhận rủi ro bảo mật/dữ liệu/cạnh tranh trạng thái; đề xuất file sẽ tạo/sửa.
6. Không tự tạo mạng xã hội, không di chuyển/xóa legacy, không download dataset, không train GPU, không deploy hay push Git trong bước này.

Trả về báo cáo: tình trạng hiện tại, sơ đồ folder thực tế, bảng khác biệt so với thiết kế, kết quả test thật, kế hoạch 3 task đầu và yêu cầu tôi duyệt trước khi viết code.
