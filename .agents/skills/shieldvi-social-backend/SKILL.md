---
name: shieldvi-social-backend
description: Dùng khi xây FastAPI social-api cho tài khoản, post, comment, reply, feed và permission trong ShieldVI Social AI; không sửa model AI.
---
# Workflow social-api
1. Đọc task trong `tasks/social-api/`, `docs/architecture/ARCHITECTURE.md`, `docs/architecture/DATABASE.md` và contract.
2. Kiểm tra tách database/social-api khỏi moderation-ai; không import predictor/torch/transformers vào social-api.
3. Viết API với auth và authorization thực, migration, validation, pagination, rate limit và idempotency.
4. Không dùng mật khẩu plaintext, không đưa token/secrets vào source, không bỏ qua IDOR/permission tests.
5. Viết pytest độc lập bằng test database tạm; kiểm thử role thường/admin, hành vi sai, retry/job.
6. Không di chuyển legacy hoặc train model. Chỉ cập nhật task sau khi chạy test thực.
