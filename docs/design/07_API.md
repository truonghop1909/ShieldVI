# 07 — Thiết kế API v1 (chưa triển khai)

## 1. Quy ước
- Các endpoint `/api/v1/*` mới là **đề xuất**, không khẳng định V3 đã có.
- HTTPS ở production; JSON UTF-8; xác thực client với secure session hoặc JWT/cookie được thiết kế đúng; API nội bộ dùng service credential riêng.
- Phản hồi lỗi chuẩn `{ "error": {"code":"...", "message":"...", "request_id":"..."} }`.
- API ghi nội dung hỗ trợ `Idempotency-Key`; kiểm tra size/input limit, type/schema, parent ownership, role.
- Dùng `created_at` ISO-8601 UTC; ID opaque, không nhúng email/name vào AI request.

## 2. Social API
| HTTP | Endpoint | Role | Chức năng |
|---|---|---|---|
| POST | `/api/v1/auth/register` | guest | Tạo user |
| POST | `/api/v1/auth/login` | guest | Đăng nhập |
| POST | `/api/v1/auth/logout` | user | Đăng xuất |
| GET | `/api/v1/me` | user | Hồ sơ hiện tại |
| GET | `/api/v1/feed?cursor=...` | guest | Chỉ bài được phép công khai |
| POST | `/api/v1/posts` | user | Lưu post + job; return trạng thái tạm |
| GET | `/api/v1/posts/{id}` | user/guest | Quyền hiển thị theo trạng thái |
| PATCH | `/api/v1/posts/{id}` | author | Sửa nội dung -> tạo revision & job mới |
| POST | `/api/v1/posts/{id}/comments` | user | Bình luận/reply, gửi `parent_id` nếu có |
| GET | `/api/v1/posts/{id}/comments` | user/guest | Chỉ nội dung có quyền xem |
| POST | `/api/v1/reports` | user | Báo cáo nội dung |
| POST | `/api/v1/appeals` | author | Kháng nghị quyết định về nội dung của mình |
| GET | `/api/v1/me/content` | user | Xem nội dung mình đang chờ/ẩn |
| GET | `/api/v1/moderation/queue` | moderator/admin | Queue phân trang, filter ưu tiên |
| GET | `/api/v1/moderation/items/{id}` | moderator/admin | Nội dung + evidence + audit |
| POST | `/api/v1/moderation/decisions` | moderator/admin | Approve/hide/restore, bắt buộc reason |
| GET | `/api/v1/moderation/appeals` | moderator/admin | Queue kháng nghị |
| GET | `/api/v1/admin/moderation/metrics` | admin | Stats backlog/FP/FN từ dữ liệu review |

## 3. Tạo bình luận — ví dụ
`POST /api/v1/posts/post-9/comments`
```json
{ "body": "Mình không đồng ý ở đoạn này", "parent_id": "cmt-1" }
```
`201 Created` (chỉ có nghĩa đã lưu, KHÔNG phải đã công khai)
```json
{
  "id": "cmt-123", "post_id": "post-9", "author_id": "user-7",
  "visibility_status": "PENDING_MODERATION", "review_status": "QUEUED",
  "moderation_request_id": "req-abc123", "message": "Đã nhận bình luận; đang kiểm tra."
}
```

## 4. AI internal API
`POST /api/v1/moderate/comment` **chỉ worker/backend gọi**.
- Request/response ví dụ ở `contracts/moderation_request.example.json` và `contracts/moderation_response.example.json` (các giá trị minh họa, không phải output thực).
- AI response gồm `request_id`, `model_version`, `model_threshold`, `toxicity_score`, lexical signals, target evidence, suspected repeated, limitations.
- Nếu có `suggested_action`, đó là **gợi ý**; Social API vẫn tính `risk_tier`, áp dụng policy, log kết quả và quyết định.
- `403` nếu thiếu service credential, `422` nếu schema sai, `429/503` khi quá tải, client áp timeout và retry có backoff.
- Legacy `/health`, `/api/analyze`, `/api/reviews/*`, `/dashboard/` không bị thay đổi trước khi regression test.

## 5. Decision API — ví dụ
`POST /api/v1/moderation/decisions`
```json
{
  "entity_type": "comment", "entity_id": "cmt-123",
  "action": "HIDE", "reason_code": "TARGETED_HARASSMENT",
  "note": "Đã xem ngữ cảnh đầy đủ", "expected_revision": 1,
  "expected_decision_version": 0
}
```
- Social API xác minh role, entity exists, constraints, concurrent version, actor, timestamp; ghi `moderation_decisions` bất biến.
- Không để một request của moderator có thể thay kết quả review của post khác (IDOR).

## 6. Hành vi HTTP cần test
- Create returns ID even if AI offline (job queued).
- User không được đọc item HELD/HIDDEN của người khác dù biết UUID.
- Admin action cần reason; trùng request không double-write.
- API giữa 2 service phải có contract tests, payload size limit, timeout, model unavailable behavior.
