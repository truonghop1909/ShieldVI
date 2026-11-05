# 05 — User journeys / Admin không cần trực 24/24

## A. User tạo bài viết
1. User đăng nhập rồi tạo bài.
2. Social API xác thực, rate limit, kiểm tra dữ liệu, ghi `post + moderation_job` cùng transaction.
3. Gửi response ngay: bài `PENDING_MODERATION`, user thấy “đang kiểm tra”.
4. Worker gọi AI và áp dụng policy; UI cập nhật trạng thái qua polling ngắn (MVP) hoặc refresh.
5. Nếu LOW: đăng; REVIEW: đăng có cờ admin; HIGH: tạm giữ (khi policy đã bật và có căn cứ kiểm thử).

## B. User bình luận/trả lời
- Bình luận mang `post_id`, `parent_id`, `author_id`, `created_at`; phân tích từng bình luận và context tối thiểu có liên quan.
- Chỉ dùng user IDs/pseudonymous để phân tích quan hệ; **không gửi email/mật khẩu**.
- Thread có công kích lặp lại cần nhiều bằng chứng, target inference có độ không chắc chắn và quyền xem lại.

## C. Moderator kiểm duyệt vào buổi sáng
1. Mở dashboard, có các tab: `Ưu tiên cao`, `Báo cáo của người dùng`, `Nghi vấn`, `Kháng nghị`, `Lỗi hệ thống`.
2. Mỗi item hiển thị full comment, author pseudonymous, ngữ cảnh parent, điểm model, từ phát hiện, lịch sử, policy version.
3. Admin chọn `Cho đăng`, `Ẩn`, `Khôi phục`, `Yêu cầu bổ sung`, ghi lý do; thao tác ghi audit và hiển thị phản hồi phù hợp cho user.
4. Không bao giờ “duyệt hết” bằng một cú click khi chưa xem nội dung, không tự ban user chỉ vì điểm model.

## D. User báo cáo nội dung
- Có nút Báo cáo, lý do chọn, chặn gửi spam/rate limit; báo cáo liên kết tới content và ưu tiên queue.
- Không tiết lộ identity người báo cáo cho người bị báo cáo.
- Nhiều báo cáo không tự chứng minh vi phạm; tránh report brigading.

## E. User kháng nghị
- Nội dung bị giữ/ẩn hiển thị lý do ở mức phù hợp và nút kháng nghị.
- Kháng nghị được ghi nhận có mã, không mất khi restart; moderator/admin xem và ra quyết định, lưu audit.
- Để tránh reviewer tự xử lý kháng nghị cho quyết định của chính mình, có thể tạo cảnh báo xung đột; một người làm MVP phải ghi rõ giới hạn và cơ chế lưu lý do.

## F. AI server bị tắt khi Admin offline
- Không mất bài/comment: Social API nhận nội dung và ghi job; queue retry; chưa công khai khi chưa xét.
- Hiển thị thông báo trung thực cho user, không báo nhầm “đã đăng công khai”.
- Khi AI hoạt động trở lại, worker tiếp tục; admin có thể manual review khi không có AI.
