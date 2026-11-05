# 11 — Nhật ký quyết định kiến trúc & câu hỏi còn mở

## Đã thống nhất trong hội thoại (design constraints)
- Tạo một mạng xã hội web để mọi người đăng bài/comment và tích hợp AI.
- Chia backend mạng xã hội và backend AI thành dịch vụ riêng.
- Có giao diện Social Web và trang quản trị AI.
- AI hỗ trợ và tự động phân luồng, giảm yêu cầu Admin trực liên tục.
- Admin có quyết định cuối cùng với trường hợp cần con người kiểm duyệt.
- Giữ ShieldVI V3 legacy, ViSoBERT V1 và threshold 0.41 làm baseline.

## Đề xuất kỹ thuật (chưa được xem là đã xác nhận hay triển khai)
- 3 luồng `LOW -> publish`, `REVIEW -> publish+flag`, `HIGH -> hold` khi được hiệu chuẩn.
- Error AI -> `PENDING_MODERATION` + retry + manual review.
- Worker poll database với SQLite cho MVP; PostgreSQL/Redis khi có nhu cầu tải lớn.
- Không làm mobile native trong MVP.

## Quyết định thiết kế T016 — 30/10/2026

[T016_POLICY_SPEC.md](../architecture/T016_POLICY_SPEC.md) là bản chốt thiết kế `social-policy-draft-0.2`, chưa phải phê duyệt active config/production. Các đề xuất và câu hỏi bên dưới được cập nhật như sau:

1. Demo local/private, tài khoản thử; public registration/Internet chưa bật.
2. LOW publish; REVIEW publish+flag; HIGH shadow publish+flag, không hold. V3 repeated heuristic chỉ REVIEW ưu tiên cao. Chưa có HIGH rule được hiệu chuẩn.
3. Mọi nội dung mới pending tới khi policy hoặc moderator quyết định; không bypass cho tài khoản mới/cũ.
4. Appeal manual, không hứa SLA, không hạn nộp trong demo; appeal không tự restore. Chỉ author gửi, moderator/admin quyết định, không lộ reporter.
5. Chưa vận hành Internet; cần duyệt riêng trước mở.
6. Demo dùng fixture/synthetic, không tự tải dữ liệu thật hay purge audit/DB. Retention theo loại dữ liệu, số ngày, nguồn/quyền dùng dữ liệu và deletion workflow **còn mở trước production**.
7. Parent bị chặn che descendants qua effective visibility; restore không đổi state con đã hidden/pending/deleted riêng.
8. Edit tăng revision, pending và job mới; bản cũ ngừng public. Guard revision/decision version chống kết quả cũ ghi đè.

Chưa thể chốt vì thiếu validation: HIGH rule/threshold, budget FP/FN, support/CI tối thiểu; cần mục tiêu được duyệt trước tuning validation, final test độc lập, shadow report và approval kích hoạt. Không xem mock/synthetic tests là bằng chứng chất lượng AI. Chi tiết flags/rollback/gate và actor transitions ở đặc tả T016.

## Câu hỏi gốc (lưu lịch sử; kết quả T016 ở trên)
1. Đăng ký công khai hay chỉ demo bằng tài khoản thử? (MVP đề xuất tài khoản thử + test)
2. Chính sách cộng đồng cụ thể: tiêu chí vi phạm và thang ưu tiên HIGH? (chưa hiệu chuẩn)
3. Có cho bài viết mới từ tài khoản mới công khai trước khi AI xong không? (MVP: không)
4. Kháng nghị có thời hạn xử lý dự kiến nào nếu chỉ có một Admin? (không hứa SLA nếu chưa đủ nhân lực)
5. Có triển khai ra Internet không hay chỉ demo local? (ảnh hưởng bảo mật, privacy)
6. Retention audit/log tối đa bao lâu, dữ liệu thật lấy từ đâu và có quyền dùng không?
7. Khi một post bị ẩn, comment cũ ẩn theo post như thế nào và khi khôi phục hiển thị ra sao?
8. Chỉnh sửa post/comment đã công khai có tạm giữ ngay không? (đề xuất đưa revision mới vào review)

## Thước đo cần bảo đảm
- Hệ thống ổn định trước; không tăng độ phức tạp chỉ để thêm tính năng.
- Tách rõ yêu cầu người dùng, quyết định kiến trúc, và thứ chưa đủ bằng chứng.
- **Không có ngưỡng HIGH mặc định** trong tài liệu; phải đo trên validation trước khi bật auto-hold.
