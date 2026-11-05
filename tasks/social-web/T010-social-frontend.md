# T010 — React Social Web

**Trạng thái:** DONE — build và 9 ca Chrome với Social API thật/DB tạm đạt.  
**Phụ thuộc:** T009

## Mục tiêu
Xây giao diện mạng xã hội độc lập với Dashboard V3.

## Phạm vi và việc cần làm
- Trang đăng nhập/đăng ký, feed, tạo bài viết, chi tiết post và bình luận/reply.
- Hiển thị pending moderation/needs_review hợp lý, thông báo lỗi backend.
- Mobile responsive, text wrap, tránh XSS, accessibility cơ bản.
- Không truy cập AI API trực tiếp.

## Tiêu chí nghiệm thu
- Build React đạt; luồng đăng bài, comment, đăng xuất chạy với social-api.

## Kết quả kiểm thử / thay đổi
Ngày thực hiện: 30/10/2026 (Asia/Saigon). Áp dụng [shieldvi-social-frontend](../../.agents/skills/shieldvi-social-frontend/SKILL.md) và hướng dẫn Sites cho **local-only**; không tạo/publish hosted Site. Đã đọc task, AGENTS, user journeys, phạm vi MVP và contract T009.

### Chức năng và ranh giới

- Thêm app React/Vite mới tại **V3 root/apps/social-web/**, tách dashboard legacy. Giao diện tiếng Việt, tông xanh ShieldVI, responsive và toàn văn wrap; không cần ảnh hoặc font bên ngoài.
- Login/register/logout với Social API; register mặc định tắt ở cả frontend/backend riêng biệt. Token chỉ giữ memory, xử lý 401/expires_in, reload cần đăng nhập lại, failed logout báo thật. Abort requests khi rời phiên/route để kết quả muộn không mở lại private post.
- Feed public phân trang; tạo bài dẫn tới chi tiết, ghi rõ pending/chưa công khai. “Bài vừa gửi” chỉ trong memory phiên và có copy link, không giả lập endpoint bài cá nhân.
- Post detail/comment/reply parent_id thật, phân trang/full text/indent có giới hạn trực quan. Edit/delete tác giả dùng revision/decision guards, conflict giữ draft; parent/post thay đổi làm refetch thread.
- Idempotency-Key giữ ổn định khi retry cùng draft sau lỗi mạng; body HTML được render như text. Không service key/localStorage/token URL/raw HTML. Không gọi AI API, không thêm nút publish/duyệt/appeal chưa có backend.
- Scope MVP cũ có guest feed, nhưng contract T009 hiện yêu cầu Bearer cho mọi content read; UI tuân thủ contract đang chạy, không mở guest bằng frontend. Mọi moderation state/role/ancestor permission vẫn do backend quyết định.

### File thêm/sửa

Tạo `V3 root/apps/social-web/`: `package.json`, `package-lock.json`, `.gitignore`, `.env.example`, `index.html`, `vite.config.js`, `README.md`; `src/{main.jsx,App.jsx,Thread.jsx,components.jsx,api.js,utils.js,styles.css}`; `playwright.config.js`, `tests/{run_browser.py,seed_demo.py,social.spec.js}`. `node_modules/`/`dist/` là artifact local, đã ignore. Không thêm dependency vào backend hoặc dashboard.

Design root: cập nhật task T010 này, `docs/CHANGELOG.md`; thêm `docs/baseline/T010/` (build/dependency/browser logs, screenshot, manifest, integrity). Không sửa Social API hoặc legacy runtime/DB/checkpoint, không tạo tài khoản thật, không bắt đầu T011.

Kiểm kê 18 file nguồn app mới: [social-web-source-manifest.json](../../docs/baseline/T010/social-web-source-manifest.json), kèm kích thước/SHA-256, loại trừ node_modules/dist/artifact QA.

### Lệnh và kết quả thật

Từ `V3 root/apps/social-web/`:

```powershell
npm.cmd install --no-audit --no-fund
npm.cmd run build
& ../../services/social-api/.venv/Scripts/python.exe tests/run_browser.py
```

| Kiểm chứng | Kết quả | Evidence |
|---|---|---|
| Production build | PASS, exit 0, Vite 6.4.5, 1581 modules, 2.01s | [frontend-build.txt](../../docs/baseline/T010/frontend-build.txt) |
| Chrome/Playwright | **9 passed**, 9.7s, exit 0 | [browser-tests.txt](../../docs/baseline/T010/browser-tests.txt) |
| Runtime dependency snapshot | React 18.3.1, Playwright 1.64.1, plugin-react 4.7.0 | [dependencies.txt](../../docs/baseline/T010/dependencies.txt) |
| Legacy/API integrity | **68 legacy + 30 Social API file giữ nguyên SHA-256** | [integrity-check.json](../../docs/baseline/T010/integrity-check.json) |
| Desktop/mobile visual QA | Đã xem screenshot; không tràn ngang 390px/320px, HTML payload hiện nguyên văn | [Desktop login](../../docs/baseline/T010/browser/desktop-login.png), [feed](../../docs/baseline/T010/browser/desktop-feed.png), [mobile login](../../docs/baseline/T010/browser/mobile-login.png), [thread](../../docs/baseline/T010/browser/mobile-thread.png) |

Browser runner dùng DB tạm + synthetic accounts, migrate schema thật, real HTTP/proxy; chỉ các lỗi/deadline/mất response được fault injection. 9 ca gồm register→login→post→comment→reply→edit→delete→logout; feed phân trang/private 404; XSS literal/wrap/focus; retry sau response bị mất giữ key (server 201 rồi 200); storage/401/reload; 403/429; 409/failed logout; expires_in; late POST sau logout. Không dùng public seed làm bằng chứng AI đã duyệt.

Trong QA đã sửa selector để phân biệt button/textarea cùng tên, cleanup process tree Windows và AbortController với React StrictMode; kết quả trên là lượt kiểm tra cuối. Có warning môi trường NO_COLOR/FORCE_COLOR không ảnh hưởng exit code. Lần build trong shell hạn chế không ghi được dist; build cuối với quyền ghi phù hợp đã đạt và chỉ ghi app mới.

### Giới hạn/bàn giao

- T009 chưa có AI worker/manual approve nên bài mới vẫn pending, không được báo đã public. Cập nhật trạng thái qua nút Làm mới.
- Frontend phiên memory và recent list memory là chủ đích bảo vệ token; không có refresh/session restore/all-my-posts endpoint. Backend vẫn có TTL/revoke riêng.
- Browser QA dùng Vite dev + Chrome local; production bundle đã build nhưng chưa deploy/E2E trên hosting, chưa Safari/Firefox/screen reader hoặc full WCAG audit. Registration trong browser test bật riêng cho fixture, không bật default ứng dụng.
- Backend/legacy pytest không chạy lại trong T010 vì byte-identical, đã có baseline T009; không tuyên bố kết quả mới cho backend hoặc inference thật.
- Server/DB tạm QA đã dừng/dọn; lệnh khởi động local và cấu hình trong [README](../../docs/modules/social_web.md). Git vẫn không có repository nên không có Git diff/commit; review file list và manifest. T011 chưa thực hiện.
