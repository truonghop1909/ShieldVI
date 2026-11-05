# Demo local r06 + v6.1 — 04/11/2026

Mở http://127.0.0.1:8023/dashboard/ . Banner vàng xác định đây là phiên nghiên cứu, không đổi model/rule mặc định. Process chỉ bind loopback, dùng CPU offline và ngưỡng .41, không training. Review DB riêng trong thư mục này; không ghi DB đang dùng. Không có Internal Social moderation API tại cổng demo.

1. Bấm **Tải input Test09** trên banner; file JSON tải xuống là input, không phải analysis.
2. Trong Dashboard, bấm **Nhập JSON**, chọn file vừa tải.
3. Bấm **Phân tích hội thoại** và đọc cột kết quả ngữ cảnh/final assessment, target và repeated evidence. Điểm ViSoBERT raw là trường riêng.
4. Test09 c17 phải TOXIC và target U03. Test10 c14 CLEAN/không có attack instance. Test07 có hai cặp U02→U03 `[c06,c11]` và U03→U02 `[c07,c12]`.
5. Bấm **JSON AI** để xuất kết quả. Không dùng file `*_analysis.json` làm input.

Khởi động lại khi cổng8023 trống, từ root repository, giữ terminal mở:

```powershell
.\.venv\Scripts\python.exe -X utf8 reports/ai_update/fresh10_demo_20261104/launch.py
```

Launcher kiểm SHA model/rule trước chạy, chỉ thay binding v2 của canonical app **trong process demo**, không sửa app/main.py, signal_engine.py, static build, .env hoặc default config. Endpoint `/api/demo/config` hiển thị thông tin phiên. API/Dashboard mặc định khi chạy entrypoint thông thường vẫn dùng v5.

`smoke_result.json`: actual HTTP/model inference trên 3thread/60comment PASS; HTML/assets PASS, internal endpoint404, readiness1311hashes PASS. `Test07/09/10_actual_demo_analysis.json` giữ kết quả thực tế. Không gọi đây là browser E2E: chỉ mở trình duyệt người dùng; kiểm chứng tự động ở mức HTTP/assets/API. Lần này không chạy lại toàn bộ648test vì không đổi processor/core/UI build. Process còn chạy để người dùng thao tác.

Nhãn vẫn synthetic_reference; không human gold hoặc independent real evaluation. Các miss/FP trong báo cáo Fresh10 vẫn còn, không hứa đúng mọi câu. Xem `docs/ai-update/final-report/FRESH10_RECOVERY.md` từ root.
