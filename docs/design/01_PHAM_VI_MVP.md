# 01 — Phạm vi sản phẩm (MVP)

## 1. Tuyên bố sản phẩm
**ShieldVI Social** là mạng xã hội tối giản cho phép tài khoản đăng bài, bình luận và trả lời. **ShieldVI AI** phát hiện tín hiệu độc hại, teencode, nhắm mục tiêu và dấu hiệu công kích lặp lại. **Admin Dashboard** là nơi xem các trường hợp cần xử lý, không phải nơi duyệt tất cả bình luận.

## 2. Vai trò
| Vai trò | Khả năng |
|---|---|
| Guest | Xem bài/bình luận công khai, đăng ký |
| User | Đăng nhập, đăng bài/bình luận/trả lời, sửa hoặc xóa nội dung của mình, báo cáo vi phạm, kháng nghị quyết định liên quan nội dung của mình |
| Moderator | Xem hàng đợi, xác minh bằng chứng, duyệt/ẩn/khôi phục nội dung, ghi lý do, xử lý kháng nghị được phân quyền |
| Admin | Như Moderator, thêm phân quyền và cấu hình policy (cấu hình có version, audit, không sửa trực tiếp trong database) |

## 3. Bắt buộc làm cho MVP
- Đăng ký/đăng nhập/đăng xuất; trang cá nhân cơ bản.
- Feed bài viết: tạo, đọc, sửa/xóa bài của mình, phân trang.
- Bình luận một cấp và trả lời nhiều cấp (giới hạn độ sâu hiển thị nếu cần); xem thread theo `parent_id`.
- AI phân tích bài mới/bình luận mới bất đồng bộ qua job worker, không bắt browser đợi GPU.
- Ba nhánh chính sách: tự đăng, tự đăng kèm cờ theo dõi, tạm giữ chờ duyệt.
- Dashboard: queue ưu tiên, toàn văn bình luận, điểm và bằng chứng AI, approve/hide/restore, lịch sử thay đổi.
- User báo cáo nội dung, xem trạng thái nội dung của chính mình, gửi kháng nghị.
- SQLite dev riêng Social/AI, pytest, giao kèo API và log cơ bản.

## 4. Ngoài phạm vi MVP
Chat realtime, livestream, video, gợi ý bài bằng AI, quảng cáo, mobile native, notification push, chat riêng, khoá vĩnh viễn tự động, training model mới, Kubernetes.

## 5. Tiêu chí nghiệm thu
1. Hai backend chạy độc lập và giao tiếp API nội bộ.
2. Hai frontend sử dụng đúng API, role check ở server.
3. Người dùng tạo post + reply được, và không xem được nội dung đang giữ của người khác.
4. Nếu AI không phản hồi, request tạo bình luận vẫn trả ID và trạng thái minh bạch; job retry được.
5. Moderator kiểm duyệt khi online, lịch sử không mất; quyết định của Moderator không bị job cũ ghi đè.
6. Toàn bộ testcase bắt buộc trong `09_TEST_DANH_GIA.md` qua.
7. ShieldVI V3 legacy vẫn chạy được qua đường API cũ và checkpoint không bị chỉnh sửa.
