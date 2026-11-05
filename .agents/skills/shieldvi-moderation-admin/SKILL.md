---
name: shieldvi-moderation-admin
description: Dùng khi phát triển moderation-web, queue kiểm duyệt, xác nhận nhãn, lịch sử và kháng nghị cho ShieldVI Social AI.
---
# Workflow kiểm duyệt
1. Đọc task `tasks/moderation-web/`, quy tắc auth/permissions, audit và policy.
2. Hiển thị toàn văn, điểm ViSoBERT, lexical signals và model version nhưng không đồng nhất tín hiệu với verdict.
3. Review action phải có moderator ID, thời gian, lý do, lịch sử; phải có kiểm soát role.
4. Khi retry AI không tự ghi đè quyết định của người kiểm duyệt.
5. Test dữ liệu thiếu, lỗi API, content XSS, truy cập chưa đăng nhập và export; chạy build thật.
