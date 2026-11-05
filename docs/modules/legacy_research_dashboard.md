> Source directory: `apps/moderation-web/legacy-v3/`. Run relative commands from the working directory named in each section; when omitted, use this source directory. [Documentation index](../README.md).

# Dashboard nghiên cứu ShieldVI V3

React source chuyển từ `frontend/`, giữ giao diện và `/dashboard/`. Đây là nghiên cứu/analyze/annotation V3; quyết định moderation của mạng xã hội dùng dashboard cha `apps/moderation-web` và Social API.

```powershell
npm.cmd ci
npm.cmd run build
npm.cmd run dev
```

Build chỉ vào `services/moderation-ai/app/static`, không ghi đè `apps/moderation-web/dist`. AI phục vụ `/dashboard/` ở port 8000; dev riêng 5175 để không trùng Social Web 5173 và Social moderation 5174. Proxy `/api` và `/health` về AI 8000 như V3. Root `frontend/package.json` chuyển tiếp các lệnh build/dev/preview; cài qua `npm --prefix frontend run install:legacy`.

Lockfile giữ các dependency đã build, tạo từ cache local; không đổi React/Vite major hoặc logic UI trong T015. Chỉ dùng dữ liệu demo/ẩn danh trên loopback/private vì legacy research API chưa có auth Social. [AI service](moderation_ai.md).


## Compatibility entrypoint tại frontend/

### Ghi chú compatibility

React source ở `apps/moderation-web/legacy-v3`. `npm --prefix frontend run build` và `run dev` từ repo root chuyển tiếp tới app đó. Cài dependency bằng `npm --prefix frontend run install:legacy`, hoặc `npm ci` ngay trong legacy-v3. Build phục vụ `/dashboard/` ở AI port 8000, dev port 5175. Dashboard Social vẫn ở `apps/moderation-web`, port 5174, không bị ghi đè.

