> Source directory: `apps/moderation-web/`. Run relative commands from the working directory named in each section; when omitted, use this source directory. [Documentation index](../README.md).

# ShieldVI Moderation Web — T013/T018

T015 chuyển dashboard nghiên cứu V3 vào [legacy-v3](legacy_research_dashboard.md) bên trong app này. Social moderation source, API và dist của dashboard này giữ nguyên; V3 build vào static của AI service, không dùng Social decisions/review DB chung.

T014/T019 có [runbook E2E 4 server + worker, backup và đánh giá](../guides/RUN_LOCAL.md). Test Playwright chọn `review.spec.js` mặc định; `SHIELDVI_FULLSTACK_E2E=1` chỉ dùng trong runner fullstack có AI fixture/worker riêng.

React dashboard riêng cho moderator/admin, cổng mặc định 5174. Chỉ gọi Social API bằng user Bearer, không gửi AI service token cho browser. Token trong memory, reload phải đăng nhập lại. Dùng chung auth/roles với Social Web; dashboard không tự cấp quyền staff.

## Chạy cùng backend đã cấu hình

Từ `apps/moderation-web`:

```powershell
npm ci
npm run dev
```

Backend ở `http://127.0.0.1:8001`, schema yêu cầu `0004_review`. Xem [backend README](social_api.md) về migration/auth/worker. Vite đọc `.env` nếu chủ động tạo theo `.env.example`. `SOCIAL_API_PROXY_TARGET` chỉ ở dev server. `VITE_SOCIAL_API_BASE` rỗng dùng cùng origin/proxy, hoặc HTTP(S) origin chính xác; khi cross-origin, cấu hình Social API cho phép đúng origin 5174.

## Demo với DB tạm và tài khoản giả

Không cần sửa role trong DB demo hiện có. Từ **V3 root**, dùng venv Social API đã cài dependency và cả hai app đã `npm ci`:

```powershell
.\services\social-api\.venv\Scripts\python.exe apps/moderation-web/tests/run_browser.py --demo
```

Script tạo SQLite tạm, migrate riêng, chạy Social API và hai giao diện trên cổng loopback trống. Terminal in URL Social/Admin và mật khẩu ngẫu nhiên dùng chung **chỉ cho bốn tài khoản giả**: `fixture_author`, `fixture_viewer`, `fixture_mod`, `fixture_admin`. Dùng hai browser profile/cửa sổ cho author và moderator. Ctrl+C dừng process do script tạo và dọn DB tạm. Không có inference thật/worker trong demo này; “Evidence fixture” là kết quả tổng hợp, version `browser-synthetic-not-real-inference`. Không nhập dữ liệu thật vào demo fixture.

1. Social: đăng nhập `fixture_author`, mở bài “Cau chuyen demo cong khai”, đăng bình luận; trạng thái pending.
2. Admin: đăng nhập `fixture_mod`, lọc Bình luận, mở toàn văn/ngữ cảnh, nhập lý do rồi Ẩn nội dung. Có thể duyệt khi AI offline.
3. Social: mở **Nội dung & kháng nghị**, tìm bình luận, gửi lý do. Nội dung vẫn ẩn trong lúc chờ.
4. Admin: tab **Kháng nghị**, nhập lý do, chọn **Chấp nhận · khôi phục** hoặc **Giữ quyết định ẩn**. Audit lưu actor/time/revision/decision version/reason/outcome.
5. Social: Làm mới trạng thái để xem kết quả. Reload/đăng nhập lại vẫn còn appeal. Viewer có thể báo cáo nội dung công khai; reports không tự ẩn.

## Các guard

- Queue phân trang post/comment, tabs Cần xem xét/Báo cáo/Kháng nghị/AI lỗi/Tất cả. Ưu tiên held, failed pending, pending, appeal, repeated candidate, thường; trong nhóm xếp tuổi chờ, report count, ID. Priority là thứ tự xử lý, không phải verdict/severity.
- AI label/score, policy risk, visibility, review status tách riêng. Hiện model/lexicon/threshold/evidence/limitations; không gọi model khi mở dashboard.
- Approve/hide/restore/resolve/claim/retry cần lý do và expected revision/decision version. Xung đột 409 giữ bản thảo; tải lại chi tiết trước quyết định tiếp.
- Nhận duyệt có lease 5 phút; reviewer khác bị chặn. Hết hạn hiện QUEUED/APPEALED, không đổi visibility. Nhận duyệt vô hiệu job AI đang chạy; sau lease vẫn ở manual queue, không tự re-run.
- Appeal đang mở phải resolve qua endpoint appeal, không bypass bằng restore/admin DELETE. Author edit đóng appeal SUPERSEDED; author delete đóng AUTHOR_DELETED và không thể restore.
- Feedback cảnh báo nhầm vào audit cùng provenance, chưa phải nhãn gold/training. HIGH auto-hold tắt, threshold 0.41 giữ nguyên.
- Full text render bằng React text nodes. Chưa có bulk export; audit đọc phân trang có auth.

## Kiểm chứng

```powershell
npm run build
# Từ V3 root: tự tạo DB tạm, mở Chrome headless rồi dọn.
.\services\social-api\.venv\Scripts\python.exe apps/moderation-web/tests/run_browser.py
```

Chrome đã cài là mặc định (`PLAYWRIGHT_CHANNEL=chrome`), không tải browser tự động. [Báo cáo và giới hạn](../archive/implementation_reports/T013_T018_ADMIN_REPORT.md).
