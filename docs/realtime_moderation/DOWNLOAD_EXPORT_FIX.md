# Sửa tải kết quả JSON — 05/11/2026

## Nguyên nhân và bản khôi phục

File UUID trong ảnh là JSON UTF-8 hợp lệ:15 bình luận,48.293 byte. Nút frontend
đã đặt `download="..._analysis.json"`, nhưng Chrome do Playwright điều khiển dùng
`Browser.setDownloadBehavior: allowAndName`: tên file trên đĩa và trong Chrome
Downloads là UUID. Test cũ gọi `Download.saveAs()` sang tên được chọn bởi test,
nên kiểm tra nội dung đúng nhưng không phát hiện trải nghiệm tải thực tế.

Đã sao chép nguyên byte file người dùng vào session hiện tại, không đổi nhãn,
text hoặc score, không xóa file gốc:

`reports/task_rollout_20261104/demo_2e7ba701c0343580/downloads/REDDIT_TROCHUYENLINHTINH_001_analysis.json`.

SHA256: `b655e6acca7f71c29f3953cf1b9058d3602cf35b4550250d85d836732661109e`.
Chỉ kiểm tra định dạng/nội dung xuất, không coi dữ liệu đó là human gold.

## Thay đổi

- `scripts/demo_downloads.mjs`: cửa sổ operator dùng CDP `allow`, giới hạn đúng
  browserContextId, lưu vào `<demo_root>/downloads`. CDP session được giữ đến
  lúc context đóng; detach ngay sẽ làm Chrome reset cấu hình.
- `scripts/demo_open_browsers.mjs`: áp dụng cấu hình cho các cửa sổ headed.
  Headless automation vẫn dùng artifact/saveAs riêng như trước.
- `apps/shared/download-file.mjs`: helper tải chung, tên có prefix dễ nhận biết,
  dấu thời gian UTC và nonce; giữ extension `.json`/`.csv`/`.jsonl`/`.md`.
  Tên được lọc ký tự Windows và giới hạn độ dài. Gắn link vào DOM, thu hồi blob
  sau30giây. Tên duy nhất tránh Chrome CDP ghi đè export trùng tên.
- `QuickAiTest.jsx`, `studio-api.js`: tái sử dụng helper; nội dung Blob/API không
  thay đổi. Không thêm hook làm reset trạng thái editor hoặc kết quả.
- Launcher/runner thêm `-DownloadCheck` để chạy native-download E2E riêng.

Không sửa backend, contract, checkpoint, threshold0.41, reference hoặc lock.

## Kiểm thử thực tế

-7 Chrome checks PASS: tái hiện UUID ở context cũ; file native đúng `.json`;
  UTF-8/emoji; tên đúng trong `chrome://downloads`; hai lần tải giữ cả hai file;
  CSV/JSONL; cấu hình không lan sang context khác và file tồn tại sau đóng.
-5 actual-model E2E checks PASS qua launcher chuẩn: phân tích5comment, MIME JSON,
  file thật trên đĩa parse được, text/processor/threshold giữ nguyên, Chrome UI
  hiển thị tên, tải lặp không ghi đè, đóng browser vẫn giữ export.
  Không dùng `Download.saveAs()` để kiểm tra file native.
- Moderator/Studio build PASS, startup13/13 PASS.
- Các lần thử chưa đạt được giữ log: detach CDP quá sớm, selector Chrome cũ,
  và phát hiện ghi đè khi chưa có suffix tên duy nhất. Không tính chúng là PASS.

Logs: `reports/download_fix_20261105_native_complete.log`,
`download_fix_20261105_actual_verified.log`, `download_fix_20261105_build.log`,
`download_fix_20261105_startup.log`. Actual E2E root:
`reports/task_rollout_20261104/demo_e2716aa0ec230f62/`.
Manifest/SHA: `reports/download_fix_20261105_verified.json`.

Chạy lại kiểm thử riêng:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_realtime_studio.ps1 -DownloadCheck
```

## Trạng thái áp dụng và giới hạn môi trường

Code đã kiểm chứng trên browser context mới. Cấu hình download của các cửa sổ
đang mở được giữ trong Chrome; refresh frontend không gỡ `allowAndName` cũ.
Không dừng session người dùng hiện tại hoặc reset DB. Dùng bản JSON khôi phục
để mở ngay kết quả15comment; bản sửa sẽ có hiệu lực khi mở cửa sổ demo mới.

Readiness verification hiện FAIL vì9file original V1 dưới
`C:/Users/admin/Downloads/visobert_toxic_final/` đã không còn tồn tại.1.302file
còn lại không báo sai hash; SHA của lock vẫn
`ac21e3c29b358e9f9a1d8c1850d661e9c858f1c7270d4ae27b78d66dfe823ba3`.
Đã kiểm tra đường dẫn registry thật cũng trỏ V1 vào thư mục đó. Full launcher
khởi tạo Studio cần verify V1, nên không tự restart toàn bộ demo khi còn thiếu
artifact này. V1.1/r06 vẫn có sẵn; bài test download chỉ dùng default V1.1 thật.
Không sửa lock/path/checkpoint, không tải lại model hoặc tạo fake fallback.
Việc khôi phục original V1 là vấn đề môi trường riêng, chưa thực hiện trong
phạm vi sửa export này.
