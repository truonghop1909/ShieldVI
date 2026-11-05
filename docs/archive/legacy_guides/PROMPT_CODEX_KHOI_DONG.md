# Prompt gửi Codex trong VS Code

Hãy đọc `AGENTS.md`, `docs/governance/AGENTS_SOCIAL_ADDENDUM.md`, `docs/architecture/ARCHITECTURE.md`, `docs/architecture/MIGRATION.md`, `docs/architecture/API_CONTRACT.md` và `tasks/integration/T007-repo-blueprint.md` trong repository ShieldVI đang mở.

Mục tiêu là phát triển **mạng xã hội ShieldVI** tách hai backend độc lập:
1. `services/social-api`: FastAPI cho tài khoản, đăng nhập, bài viết, bình luận, trả lời, feed, moderation workflow và quyền admin.
2. `services/moderation-ai`: dịch vụ AI dùng ViSoBERT V1, lexicon Việt–Anh/teencode, target detection, repeated harassment từ ShieldVI V3 đang có.

Hai giao diện:
- `apps/social-web`: React, giao diện mạng xã hội dành cho người dùng.
- `apps/moderation-web`: React, dashboard người kiểm duyệt.

Yêu cầu làm **duy nhất T007 (khảo sát & thiết kế kế hoạch chuyển đổi)** trước:
- Kiểm tra mã nguồn thật và mọi route/test hiện hành.
- Lập file kiểm kê nguồn: app/, frontend/, tests/, notebook Colab, static build, các path checkpoint.
- Xác nhận boundary giữa social-api và moderation-ai, quyền sở hữu DB và contract trao đổi.
- Lập kế hoạch chuyển đổi từng bước không phá ShieldVI V3 đang chạy, theo thứ tự trong docs/architecture/MIGRATION.md.
- Không di chuyển file, không tạo service mới, không train model, không đổi threshold 0.41 trong T007.
- Nếu chạy được, ghi baseline pytest và frontend build. Nếu thiếu dependency/GPU, ghi rõ chưa kiểm chứng; không tuyên bố test pass.
- Cập nhật task T007 và báo cáo file nào định sửa cho T008.

Chỉ thực hiện T008 hoặc các task khác khi tôi yêu cầu tiếp.
