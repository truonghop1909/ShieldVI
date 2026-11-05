# Demo ShieldVI A–D trên máy của bạn

Dùng **AI checkpoint thật đang có trên máy**, chạy CPU, threshold 0.41. Ba tài khoản và nội dung demo là giả, trong SQLite tạm. Script chạy Social API + AI + worker + hai web; không cần cấu hình năm terminal, không sửa DB demo cũ hoặc train model.

## 1. Khởi động

Mở PowerShell trong VS Code và chạy:

```powershell
cd E:\lamDoAn\ShieldVI_V3_Hybrid_Review
.\services\social-api\.venv\Scripts\python.exe -X utf8 scripts/demo_social.py
```

Chờ model và hai web khởi động. Terminal hiện dạng:

```text
Social: http://127.0.0.1:<cổng được chọn>
Admin:  http://127.0.0.1:<cổng được chọn>
Accounts: demo_alice / demo_bob / demo_admin
Temporary password: <mật khẩu ngẫu nhiên của phiên này>
demo>
```

**Mở đúng URL terminal vừa in**, không mặc định dùng 5173/5174 vì script chọn cổng trống để tránh đụng server khác. Giữ terminal chạy suốt buổi demo.

Mở ba tab:

| Tab | URL | Tài khoản |
|---|---|---|
| Người viết | Social | `demo_alice` |
| Người tham gia khác | Social, mở tab thứ hai | `demo_bob` |
| Người kiểm duyệt | Admin | `demo_admin` |

Cả ba dùng mật khẩu tạm terminal in. Token chỉ trong bộ nhớ từng tab, nên hai tab Social có thể dùng hai tài khoản khác nhau. Khi F5/đóng trang phải đăng nhập lại; để cập nhật dữ liệu trong demo, dùng nút **Làm mới** của ứng dụng.

Không cần mở `/dashboard/` nghiên cứu V3 để duyệt nội dung Social; dùng URL **Admin** ở trên. Chế độ `apps/moderation-web/tests/run_browser.py --demo` cũ chỉ duyệt thủ công, không có AI/worker; dùng script mới này cho A–D.

## 2. Mốc A — đăng bài và bình luận bình thường

Trong tab **demo_alice**:

1. Ở Bảng tin, nhập bài: **“Xin chào, cảm ơn bạn.”** → **Gửi bài viết**.
2. Ban đầu thấy **Đang chờ kiểm tra**. Chờ vài giây, bấm **Làm mới** trong trang bài viết.
3. Khi worker nhận kết quả LOW, trạng thái thành **Đã công khai**. Bấm **Bảng tin** và làm mới để thấy bài trên feed.
4. Mở bài → bình luận **“Xin chào, cảm ơn bạn.”** → **Gửi bình luận**; chờ rồi làm mới.
5. Tab **demo_bob** làm mới Bảng tin, mở bài và thấy bình luận đó.

**Kết quả cần trình bày:** bài xuất hiện trên feed, bình luận xuất hiện trong cuộc trò chuyện của bài. API lưu nội dung trước, AI xử lý qua worker, không báo đã public khi còn pending.

## 3. Mốc B — AI gắn cờ, admin xem evidence

Vẫn dưới bài vừa tạo, **demo_alice** gửi bình luận thử nghiệm:

> Mày đúng là đồ ngu.

Chờ xử lý và làm mới. Trong tab **Admin**:

1. Chọn **Cần xem xét** → lọc **Bình luận** → **Làm mới hàng chờ**.
2. Mở bình luận, xem toàn văn và mục **Bằng chứng & provenance AI**.
3. Mở **Tín hiệu đầy đủ** để xem lexical signals/target/limitations; đối chiếu phiên bản model và ngưỡng 0.41.

Các trường có nghĩa khác nhau:

| Trường | Kỳ vọng với câu demo này | Ý nghĩa |
|---|---|---|
| AI label / score | `TOXIC`, score ≥0.41 | Dự đoán classifier |
| Policy risk | `REVIEW` | Cần người xem xét |
| Visibility | `PUBLISHED_FLAGGED` — công khai, cần xem xét | Vẫn public trong shadow mode |

**Không cần ẩn ở mốc B.** Score vượt 0.41 không tự ẩn hoặc khóa tài khoản. Nếu không có reply/mention đủ căn cứ, target có thể chưa xác định; không bịa nạn nhân từ nội dung câu chữ.

## 4. Mốc C — tắt AI, giữ comment, bật lại

Trong terminal đang có dấu `demo>`, nhập:

```text
ai-off
```

Không nhấn Ctrl+C ở bước này vì Ctrl+C dừng cả phiên demo.

1. Tab **demo_alice** gửi bình luận mới: **“Xin chào, cảm ơn bạn.”**
2. Bình luận vẫn được lưu, author thấy **Đang chờ kiểm tra**; người khác chưa thấy.
3. Trong terminal nhập `status`; chờ worker nhận lỗi, sẽ có job `RETRY_WAIT` hoặc sau hết budget là `FAILED_PERMANENTLY`.
4. Bật AI lại bằng:

```text
ai-on
```

5. Chờ model báo ready, rồi chờ worker tới lượt retry và bấm **Làm mới** ở trang bài. Nội dung sẽ được xử lý mà không đăng lại comment.

Retry mặc định tối đa ba attempts, backoff khoảng 5s rồi 30s, có jitter. Vì vậy có thể cần chờ vài chục giây, không phải bật AI là UI đổi ngay. Nếu đã **FAILED_PERMANENTLY**, vào Admin → **AI lỗi** → chọn comment → nhập lý do → **Thử lại AI**. Sau đó chờ/làm mới; không xóa DB hay đổi threshold để giải phóng queue.

**Kết quả cần trình bày:** comment không mất, không fail-open; job có retry/error rõ ràng và có đường xử lý sau khi AI hoạt động lại.

## 5. Mốc D — lặp lại đúng actor/target, queue, appeal

Trước bước này, đảm bảo AI đang bật và các job pending của mốc C đã xử lý.

**Tab demo_bob:** mở cùng bài, gửi một bình luận mới:

> Mời mọi người góp ý lịch sự.

Chờ bình luận công khai. **Tab demo_alice:** làm mới và tìm đúng bình luận này.

1. Bấm **Trả lời** trên bình luận **của Bob**; gửi **“Mày đúng là đồ ngu.”**
2. Chờ phản hồi đầu xử lý xong, làm mới để thấy trạng thái công khai/cần xem xét.
3. Chờ ít nhất **2 giây**.
4. Bấm **Trả lời lại chính bình luận của Bob**, gửi câu trên lần hai.

**Không trả lời vào phản hồi của chính Alice.** Hai reply phải cùng người gửi Alice, cùng người nhận Bob qua parent metadata, và khác thời điểm. Hai comment độc lập hoặc hai lượt reply vào chính mình không đủ điều kiện chứng minh cùng actor→target.

**Tab Admin:**

1. **Cần xem xét** → **Bình luận** → **Làm mới hàng chờ**.
2. Mở phản hồi thứ hai có mức ưu tiên cao hơn các REVIEW thường. Số priority nhỏ hơn nghĩa ưu tiên cao hơn; pending/failed vẫn có nhóm ưu tiên riêng.
3. Xem parent context và dòng candidate lặp lại; mở **Tín hiệu đầy đủ** → `evidence`. Cần thấy nhiều `evidence_comment_ids`, `n_distinct_timestamps >= 2`, actor/target và phương pháp suy luận từ reply.
4. Risk vẫn `REVIEW`, không tự nâng HIGH chỉ vì heuristic lặp lại.
5. Nhập **Lý do quyết định** → **Ẩn nội dung** để trình diễn quyết định thủ công.

**Tab demo_alice:**

1. Mở **Nội dung & kháng nghị**, tìm phản hồi đang tạm ẩn.
2. Nhập **Lý do kháng nghị**, ví dụ “Đề nghị xem xét lại ngữ cảnh.” → **Gửi kháng nghị**.
3. Nội dung vẫn ẩn trong lúc chờ, không tự khôi phục.

**Tab Admin:**

1. Chọn **Kháng nghị**, mở nội dung và xem lời giải thích.
2. Nhập lý do → **Chấp nhận · khôi phục** để trình diễn đường restore.
3. Xem **Lịch sử audit**: `MANUAL_HIDE`, `APPEAL_OPENED`, `APPEAL_RESOLVED`, actor/time/reason/decision version.
4. Alice bấm **Làm mới trạng thái**, thấy **Đã được khôi phục**.

Các câu/tài khoản trên là dữ liệu giả để trình diễn workflow, không phải gold labels hoặc kết luận một cá nhân bắt nạt. Nếu model thật không cho đủ hai prediction toxic hoặc thiếu context, ghi rõ không đủ evidence; không sửa threshold hoặc bịa kết quả cho buổi demo.

## 6. Kết thúc và kiểm tra tự động

Trong terminal nhập `quit` hoặc nhấn Ctrl+C. Script dừng đúng các process nó tạo và dọn SQLite tạm. Dữ liệu buổi demo không được giữ sau khi thoát; DB cũ vẫn nguyên.

Muốn kiểm tra nhanh toàn bộ pipeline A–D bằng HTTP với AI thật trước buổi trình bày:

```powershell
.\services\social-api\.venv\Scripts\python.exe -X utf8 scripts/demo_social.py --smoke --report ../ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/DEMO_ABCD/smoke.json
```

Đây là smoke API/worker với hai web server đang chạy, không phải thao tác trình duyệt tự động. Kết quả hiện hành: [smoke evidence](../baseline/DEMO_ABCD/smoke.json). Nếu thiếu dependency web thì chạy `npm.cmd ci` trong `apps/social-web` và `apps/moderation-web`; không cần build dashboard nghiên cứu legacy để demo Social.
