> Source directory: `apps/social-web/`. Run relative commands from the working directory named in each section; when omitted, use this source directory. [Documentation index](../README.md).

# ShieldVI Social Web — T010

T013/T018 thêm **Nội dung & kháng nghị** tại `/my-moderation`: danh sách bài/bình luận của chính mình, trạng thái/lý do quyết định, nộp appeal khi hidden/held và xem kết quả. Người xem có form report trên nội dung công khai của người khác. Không hiện reporter/reviewer identity cho author; không trả context cha riêng tư. [Dashboard và demo DB tạm](moderation_web.md).

T011/T012/T017 đã bổ sung AI adapter, worker và manual review API; xem [hướng dẫn backend/worker](social_api.md). Các mô tả chưa có worker bên dưới ghi lại phạm vi T010; khi chạy worker với AI hợp lệ, LOW sẽ xuất hiện trên feed, REVIEW công khai kèm cờ nội bộ. Social Web không thêm nút duyệt/admin, vẫn dùng Làm mới để cập nhật.

React/Vite app độc lập với dashboard V3. Có đăng nhập/đăng ký (có cờ), feed phân trang, tạo/xem/sửa/xóa bài của mình, comment/reply nhiều cấp và trạng thái kiểm tra. Chỉ gọi **Social API**; không gọi moderation-ai, không có service API key trong browser.

## Chạy local

Terminal backend, từ `services/social-api/`:

```powershell
& ./.venv/Scripts/python.exe -m alembic upgrade head
& ./.venv/Scripts/python.exe -m uvicorn shieldvi_social.main:create_app --factory --app-dir src --host 127.0.0.1 --port 8001 --no-proxy-headers
```

Terminal frontend, từ `apps/social-web/`:

```powershell
npm.cmd ci
npm.cmd run dev
```

Mở URL Local được Vite in ra (mặc định `http://127.0.0.1:5173`). Port strict: nếu dashboard dev cũ đang dùng 5173, chạy `npm.cmd run dev -- --port 5175`, hoặc dừng đúng server của bạn; không sửa dashboard legacy. `/api` được dev proxy tới Social API 8001, không phải AI 8000. Các server kiểm thử tự động đã được dừng sau QA; tài liệu này không khẳng định một server còn chạy.

### Cấu hình

- `SOCIAL_API_PROXY_TARGET`: biến server-side của Vite, mặc định `http://127.0.0.1:8001`; dùng riêng cho dev proxy.
- `VITE_SOCIAL_API_BASE`: mặc định rỗng → `/api/v1` cùng origin. Nếu dùng API host riêng, đặt exact HTTP(S) origin (không path/query/credentials), cấu hình CORS allowlist ở backend. Production static hosting cần SPA fallback `/posts/* → index.html` và reverse proxy `/api/*`, hoặc build với origin API riêng. Chưa deploy trong T010.
- `VITE_REGISTRATION_ENABLED=false` mặc định. Backend có cờ **độc lập** `SOCIAL_REGISTRATION_ENABLED=false`. Nếu chủ động thử với dữ liệu giả trong local/private demo, đặt cả hai thành `true` trước khi start hai server. Frontend không thể mở đăng ký khi backend không cho phép. Không mở public registration/Internet từ task này.
- Vite đọc `.env.local` hoặc environment; `.env.example` chỉ mẫu. Mọi `VITE_*` đều có thể xuất hiện trong bundle: **không đặt token/secret/service key** ở đó. Cờ frontend được chốt lúc build.

## Hành vi và giới hạn có chủ đích

- Token Bearer chỉ ở memory, không localStorage/sessionStorage/cookie/URL. Reload hoặc đóng trang cần đăng nhập lại; server session vẫn theo TTL, chỉ logout thành công mới revoke phiên hiện tại. UI tôn trọng expires_in và 401; failed logout báo lỗi, giữ phiên để thử lại. Không có refresh-token flow.
- Request gắn với phiên/route bằng AbortController, bỏ kết quả cũ khi đổi bài hoặc đăng xuất. React StrictMode vẫn tải feed được. Token phiên cũ không thể xóa phiên mới bằng response 401 muộn.
- Feed chỉ public. Content mới **luôn pending**, chưa có AI worker/publish trong T010. Sau create, chuyển tới chi tiết và cho đọc riêng. “Bài vừa gửi” chỉ lưu tối đa 10 bài trong memory của phiên hiện tại; có thể sao chép URL `/posts/{id}` để mở lại sau đăng nhập. Chưa có backend endpoint list tất cả bài cá nhân, không giả lập dữ liệu này.
- Reply dùng parent_id thật. List comments phân trang 20, hiển thị toàn văn, indent tối đa 3 cấp trực quan, không cắt body; parent ở trang khác/không được phép đọc không bị fetch để lộ context. API là nơi quyết định quyền và giới hạn depth 32.
- Comment vừa gửi có thông báo pending. Các item mới của chính tác giả chưa nằm trên trang hiện tại có thể được giữ trong memory để đọc riêng; total vẫn là count đã lọc từ server. Sửa parent/post làm tải lại thread để không giữ stale descendants sau khi visibility thay đổi.
- Edit/delete chỉ hiện với tác giả. PATCH/DELETE gửi expected revision/decision version; conflict 409 giữ bản nháp và hướng dẫn tải lại. Không có admin moderation/appeal/publish button khi các API tương ứng chưa có.
- Create giữ cùng Idempotency-Key khi retry cùng bản nháp/parent sau lỗi mạng; server có thể đã lưu lần đầu, retry không tạo thêm bài/comment. Đổi bản nháp tạo key mới. Không tự retry POST vô hạn.
- Text được render qua React text nodes, không raw HTML/Markdown không tin cậy. Full text wrap trên mobile; textarea đếm Unicode code points tới 8000 như backend, không lấy UTF-16 length làm giới hạn thực.
- API chưa trả display name của người khác, nên UI dùng alias `Thành viên <opaque id prefix>`, không đoán tên thật. Không có upload ảnh, reactions giả, search giả, notification hoặc chức năng ngoài T010.
- Status pending/held/hidden/deleted/public tách biệt. `PUBLISHED_FLAGGED` của tác giả hiển thị đã công khai/chờ xem xét; không coi score là quyết định. Cập nhật qua “Làm mới”, chưa polling/stream tự động.

## Build và QA

```powershell
npm.cmd run build
& ../../services/social-api/.venv/Scripts/python.exe tests/run_browser.py
```

Build chỉ vào `apps/social-web/dist`, không đụng `app/static`. Dùng config loader runner để phù hợp môi trường Windows. `package-lock.json` cố định dependencies, dùng `npm ci` để tái lập.

Browser runner cần service venv đã có dependency và **Google Chrome cài sẵn** (Playwright channel chrome; có thể override `PLAYWRIGHT_CHANNEL`). Không tải/cài browser tự động. Runner tạo SQLite trong thư mục temp, chạy Alembic và seed fixture **chỉ khi marker test bật + DB nằm trong temp**, khởi động hai server loopback/port tạm, chạy tests rồi dừng đúng process tree và dọn DB tạm. Không tạo tài khoản thật, không seed/publish DB dev của người dùng. `npm test` riêng chỉ phù hợp khi môi trường fixture và các biến test đã được chuẩn bị.

QA có 9 ca Chrome: real registration/login/post/comment/reply/edit/delete/logout; feed pagination/private 404; HTML literal và wrap 390/320px; mất response sau POST nhưng idempotent retry; 401/storage/reload; 403/429 thông báo trung thực; 409/failed logout giữ draft; expires_in; late POST sau logout. 403/429/409/deadline/network được fault-inject có chủ đích, còn luồng chính dùng Social API thật. Dữ liệu public seed không phải kết quả AI, không chứng minh inference/moderation quality.

Screenshots/logs tại design docs `docs/baseline/T010/`. Desktop 1440px, mobile 390px/320px đã kiểm tra; có labels, focus trả lời, skip link, aria-live status/error, keyboard controls và prefers-reduced-motion. Đây là accessibility cơ bản, chưa phải chứng nhận WCAG hay kiểm thử screen reader/Safari/Firefox. Production hosting, tải lớn và real AI chưa kiểm chứng.
