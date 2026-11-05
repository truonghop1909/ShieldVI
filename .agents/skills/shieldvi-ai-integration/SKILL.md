---
name: shieldvi-ai-integration
description: Dùng khi kết nối social-api tới moderation-ai, tạo API contract, job queue, retry, policy và integration tests với ViSoBERT.
---
# Workflow tích hợp AI
1. Đọc `docs/architecture/API_CONTRACT.md`, `contracts/`, task T011/T012 và mã ShieldVI V3 hiện tại.
2. Bảo toàn ViSoBERT V1, ngưỡng 0.41, `/api/analyze` và logics target/repeated đã có.
3. AI service chỉ đưa tín hiệu/rủi ro/giải thích, Social API quyết định status theo policy và ghi audit.
4. Không gọi AI inference blocking từ request người dùng khi có nguy cơ timeout; tách worker, retry/idempotency.
5. Thử thiếu checkpoint, lỗi AI, timeout, ambiguity, false positive và AI recover; không ghi dữ liệu thật vào SQLite test.
6. Nếu phải thay contract, cập nhật cả schema/example/test trong cùng task.
