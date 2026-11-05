# T013 — Trang kiểm duyệt tích hợp

**Trạng thái:** DONE
**Phụ thuộc:** T012

## Mục tiêu
Tích hợp moderation dashboard với dữ liệu mạng xã hội thực.

## Phạm vi và việc cần làm
- Tạo admin queue theo post/comment, chi tiết bằng chứng AI và toàn văn.
- Chức năng approve/hide/review reason, audit log, basic appeal.
- Hiển thị provenance/model version và feedback false positives.
- Chỉ admin/moderator truy cập.

## Tiêu chí nghiệm thu
- Quyền truy cập test; review lưu và tải lại; không ghi đè verdict thủ công khi re-run.

## Kết quả kiểm thử / thay đổi
Đã triển khai cùng T018 theo yêu cầu người dùng: `apps/moderation-web`, queue/detail full text/context/provenance, decisions/false-positive feedback, claim lease, audit reader; Social API và UI role guard. [Danh sách file, lệnh và evidence](../../docs/archive/implementation_reports/T013_T018_ADMIN_REPORT.md).

158 Social API tests (23 review), 130 V3/adapter tests, 6 Chrome review + 9 Chrome Social Web regression và cả hai frontend build PASS. Review lưu/tải lại qua re-login; concurrent reviewer một 200/một 409; late AI không ghi đè human decision. Test dùng DB tạm và AI tổng hợp, chưa chạy real checkpoint/PostgreSQL server. DB demo chưa migrate; HIGH tắt, threshold 0.41 giữ nguyên.
