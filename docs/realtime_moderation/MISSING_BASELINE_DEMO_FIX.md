# Demo khi thiếu baseline V1 — 05/11/2026

## Nguyên nhân và cách sửa

Demo realtime dùng V1.1 hiện có (`models/visobert_head_refined`), không dùng
V1 làm mô hình mặc định. Tuy nhiên, trước khi khởi động API, launcher khởi tạo
Studio và xác minh cả V1/V1.1/r06. Baseline V1 trỏ tới
`C:/Users/admin/Downloads/visobert_toxic_final`, hiện không tồn tại, nên toàn
bộ demo dừng trước khi AI realtime được mở.

Đã kiểm tra tên file/thư mục trong models và Downloads; chưa tìm thấy bản sao
V1 gốc. Không khôi phục bằng mô hình khác, không tải hay train checkpoint mới.

Launcher hiện gọi `initialize(allow_missing_baseline=True)` riêng cho demo.
Thiếu file của V1 được báo rõ; các file V1 còn lại vẫn phải đúng hash. Thiếu
V1.1/r06 hoặc artifact bị sửa sai vẫn gây lỗi khởi tạo. Các lệnh khởi tạo
registry khác giữ chế độ strict mặc định.

Studio hiển thị V1 `UNAVAILABLE`, thông báo thiếu baseline và khóa đánh giá.
Server từ chối tạo evaluation job nếu fallback V1 thiếu/không hợp lệ, kể cả
khi chỉ chọn V1.1 và r06. Fallback vẫn là V1; không thay bằng V1.1 hay r06.
Dataset upload, annotation và realtime moderation tiếp tục hoạt động.

## Chạy demo

```powershell
cd E:\lamDoAn\ShieldVI_V3_Hybrid_Review
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_realtime_studio.ps1 -AskPassword
```

Nhập mật khẩu 12–128 ký tự, giữ terminal mở và đợi `DEMO_READY`.
Các cửa sổ Social, Moderator và Studio tự đăng nhập; dùng URL của session mới.
Phiên kiểm thử đã dừng và chỉ dọn process do chính phiên đó tạo.

## Bằng chứng thực thi

| Kiểm tra | Kết quả |
|---|---|
| Test mới trước sửa | 7 FAIL / 1 PASS; API tùy chọn chưa tồn tại |
| Test mới và evaluation regression sau sửa | 12 PASS |
| Toàn bộ Social API/Studio và startup | 286 PASS; 1 cảnh báo dependency |
| `-StudioCheck` | 7 context đăng nhập, 3 tab; V1 thiếu hiển thị và đánh giá bị khóa |
| Upload / annotation browser workflows | 6 + 6 PASS; nhãn tự động chỉ là synthetic browser fixtures |
| `-HeadlessCheck` | 8 E2E PASS, inference V1.1 thật; review/appeal/repeated |
| Moderator/Studio Vite build | PASS, exit 0 |
| Readiness | FAIL: đúng 9 file V1 thiếu; 1.302 mục khác không lệch hash |

Studio evidence: `reports/task_rollout_20261104/demo_b9f7bbad22d8bdba/`;
realtime evidence: `reports/task_rollout_20261104/demo_b5222751c38c2ee3/`.
Ảnh: [Studio thiếu V1](../../reports/task_rollout_20261104/demo_b9f7bbad22d8bdba/studio_missing_v1.png).
Log và SHA: [receipt](../../reports/v1_demo_fix_20261105_verified.json).

Build đầu đã hoàn thành nhưng PowerShell trả lỗi do npm update notice;
build xác nhận với update notifier tắt có exit 0, log gốc vẫn giữ nguyên.

## Giới hạn còn lại

Đây là sửa dependency khởi động demo, **không phải khôi phục V1**. Training
dựa trên V1 và so sánh/rollback cần V1 vẫn chưa sử dụng được. Cần bản sao gốc
đúng SHA để khôi phục đầy đủ; sau đó khởi động session mới để xác minh lại.
Không sửa readiness lock, registry nguồn, checkpoint, threshold, rules,
dataset hoặc DB hiện có. T028/T029 formal BLOCKED, T030–T033 PARTIAL giữ nguyên.
