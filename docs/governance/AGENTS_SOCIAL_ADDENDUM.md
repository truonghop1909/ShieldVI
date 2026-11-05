> Đã gộp tài liệu vào root dự án. File này giữ hướng dẫn nguồn để tra cứu; dùng [AGENTS hiện hành](../../AGENTS.md) và [báo cáo gộp](../archive/merges/REPOSITORY_MERGE_REPORT.md).

# Phần bổ sung AGENTS.md — ShieldVI Social AI

> Gộp phần này vào `AGENTS.md` đang có; đừng ghi đè các quy tắc cũ.

## Phạm vi mới
- `services/social-api/`: backend mạng xã hội, người dùng/bài viết/bình luận, nghiệp vụ công khai.
- `services/moderation-ai/`: AI server ViSoBERT V1 + lexicon + target/repeated. Không có quyền ghi nội dung bài viết của người dùng.
- `apps/social-web/`: ứng dụng mạng xã hội cho người dùng thường.
- `apps/moderation-web/`: giao diện người kiểm duyệt/admin.
- `contracts/`: ví dụ và schema trao đổi giữa hai API.
- `tasks/<group>/`: đầu mục nhiệm vụ riêng từng hệ thống.

## Workflow bắt buộc
1. Đọc task được chỉ định, skill liên quan, rồi kiểm tra repo trước khi sửa.
2. Chỉ thực hiện một task / một giai đoạn khi chưa có yêu cầu khác.
3. Không di chuyển/xóa thư mục legacy `app/` và `frontend/` trước khi T015 hoàn thành test hồi quy.
4. Không đưa ViSoBERT vào social-api; gọi nội bộ AI qua interface có version, timeout và retry.
5. Social API sở hữu database bài viết/bình luận; AI API không đọc trực tiếp database này.
6. Tất cả thao tác thay trạng thái nội dung phải có actor, thời gian, lý do, audit trail và quyền phù hợp.
7. Không hardcode token, JWT secret, CORS `*` khi gửi credential, đường dẫn Drive, email hoặc API key.
8. Không tự động tự gán TOXIC cho mọi từ tục; ưu tiên review đối với nội dung mơ hồ.
9. Không train, deploy, tạo tài khoản thật, gọi API trả phí, push Git hoặc xoá dữ liệu khi chưa được phép.
10. Nếu chưa chạy test/build thật, báo BLOCKED hoặc TODO, không nói DONE.

## Thứ tự phát triển
T007 → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015.
