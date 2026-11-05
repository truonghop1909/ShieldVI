---
name: shieldvi-social-frontend
description: Dùng khi xây hoặc sửa React social-web cho người dùng mạng xã hội đăng nhập, đăng bài, comment, reply và feed.
---
# Workflow social-web
1. Đọc task `tasks/social-web/`, contract social-api; không gọi moderation-ai từ trình duyệt.
2. Viết UI responsive, accessible, hiển thị bình luận đầy đủ, xử lý loading/error/pending moderation.
3. Không render HTML không tin cậy dưới dạng raw, không lưu long-lived secret trong frontend.
4. Không sửa moderation-web cũ khi chỉ có social-web task.
5. Chạy npm install/build và test UI phù hợp; báo cáo kết quả thực, screenshot chỉ khi có browser.
