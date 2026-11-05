---
name: shieldvi-moderation-policy
description: Use for ShieldVI Social content moderation policy, AI risk tiering, visibility states, admin-offline workflows, queue durability, appeals and policy evaluation.
---
# Skill: Thiết kế và thực thi moderation policy an toàn

1. Đọc `docs/design/03_CHINH_SACH_KIEM_DUYET.md`, `docs/design/04_VONG_DOI_NOI_DUNG.md`, `docs/design/09_TEST_DANH_GIA.md` và task đang thực hiện.
2. Tách rõ `ai_label`, `ai_score`, `risk_tier`, `visibility_status`, `review_status`.
3. Cấm tự auto-hide/auto-ban từ một từ tục hoặc threshold ViSoBERT 0.41.
4. Policy HIGH ban đầu ở `shadow` cho tới khi có đánh giá và người dùng chấp thuận kích hoạt.
5. Chỉ Social API quyết định visibility. AI API không ghi Social DB.
6. Worker: idempotency, transaction, retry/backoff, late result guard; AI offline không làm mất content.
7. Tạo test cặp ít rủi ro/mơ hồ/nguy cơ cao, trích dẫn, teencode, false positive.
8. Audit decision và quyền appeal; không tiết lộ reporter cho user.
9. Không đổi model checkpoint/threshold, training data/test split; không tự push/deploy.
10. Kết thúc bằng bảng kết quả test và các giới hạn chưa kiểm chứng.
