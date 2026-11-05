# 08 — Bảo mật, quyền riêng tư và trách nhiệm

Mốc T014/T019: [evidence và giới hạn](../archive/implementation_reports/T014_T019_VALIDATION_REPORT.md), [vận hành/backup](../guides/RUN_LOCAL.md). Runtime hiện dùng opaque Bearer token, không JWT/cookie auth; CSRF test xác nhận cookie/query/forged JWT không cấp quyền. Kiểm chứng local/private không phải chứng nhận production. Legacy research routes chưa có auth Social API, không được public proxy toàn AI server.

## 1. Tài khoản
- Mật khẩu hash bằng Argon2id hoặc bcrypt cấu hình phù hợp; không lưu plaintext, không in password vào log.
- Cookie `HttpOnly + Secure + SameSite` hoặc JWT strategy tương đương với quản lý expiry/refresh/revocation; bảo vệ CSRF khi dùng cookie.
- Role `user/moderator/admin` phải được kiểm ở **Social API**, không dựa vào ẩn nút trên React.
- Rate limit đăng nhập, tạo bài, comment, báo cáo, kháng nghị; phòng brute-force/spam.

## 2. Content & API
- Validate input (min/max length, encoding, parent_id, ownership) và sanitize/escape khi render để chống XSS.
- Kiểm tra IDOR trên API bài viết/bình luận/queue/appeal; CORS allowlist chính xác, không wildcard với credential.
- Chỉ server/worker giữ AI API key. Browser không được gọi AI service trực tiếp.
- TLS/HTTPS production; secrets qua environment/secret store, không commit `.env`.
- Không log toàn văn bình luận công khai vào console mặc định vì có thể có dữ liệu cá nhân; thu gọn và đặt retention.

## 3. Quyền riêng tư
- Social API gửi sang AI text tối thiểu cần thiết + opaque user/content ID và context liên quan (ngắn có giới hạn).
- Không gửi email, tên thật, token, password, địa chỉ IP, dữ liệu tài khoản nhạy cảm cho model.
- Trường text có thể chứa thông tin riêng tư do user tự gõ; thiết kế thời hạn giữ và quyền truy cập đối với logs/audits.
- Chỉ dùng dữ liệu thật để đánh giá/huấn luyện nếu có căn cứ sử dụng phù hợp và quy định quyền riêng tư.
- Thiết kế đường xóa nội dung, ẩn dữ liệu người dùng và xử lý bản sao/audit/log phù hợp với yêu cầu pháp luật áp dụng (cần tư vấn pháp lý trước vận hành công khai).

## 4. Quyết định kiểm duyệt
- AI là hỗ trợ; không tự khóa vĩnh viễn chỉ dựa trên score/từ khóa.
- Có giải thích mức phù hợp và cơ chế kháng nghị; lưu actor, reason, policy/model version.
- Không công khai người báo cáo; tránh report brigading.
- Có khả năng tắt tự giữ HIGH hoặc rollback policy khi phát hiện false positive tăng.

## 5. Trước khi mở mạng xã hội thật
Checklist: privacy notice, điều khoản cộng đồng, quy tắc kiểm duyệt, chính sách tài khoản và dữ liệu, bảo mật, sao lưu/khôi phục, phản hồi sự cố, giới hạn tuổi/pháp lý nếu áp dụng, cơ chế xử lý báo cáo, hành vi nguy cấp. Đây là tiêu chí thiết kế, không phải khẳng định đã đáp ứng pháp luật.
