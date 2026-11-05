# T012 — Kết nối Social API và AI

**Trạng thái:** DONE — mocked/cross-service/live HTTP stub tests đạt; inference thật chưa kiểm chứng.  
**Phụ thuộc:** T009, T011

## Mục tiêu
Tích hợp job worker riêng, retry và chính sách kiểm duyệt.

## Phạm vi và việc cần làm
- Social API tạo job; worker gọi AI với timeout/service auth.
- Advisory response theo state T016: LOW→PUBLISHED/NOT_REQUIRED, REVIEW→PUBLISHED_FLAGGED/QUEUED; thất bại AI→UNKNOWN/PENDING_MODERATION + retry, không âm thầm approve.
- Idempotency, không xử lý trùng, audit model_version/score/policy.
- Test AI offline/timeout, 4xx/5xx, high false-positive cases.

## Tiêu chí nghiệm thu
- E2E qua mocked AI; xử lý lỗi/retry không mất job.
- Không auto hide/xóa nội dung vì một tín hiệu lexicon.

## Kết quả kiểm thử / thay đổi
Đã thực hiện 30/10/2026, sau T011 theo xác nhận người dùng. Áp dụng skills shieldvi-ai-integration, shieldvi-social-backend và shieldvi-moderation-policy.

- Worker process riêng, internal auth/timeouts/response validation, shadow policy version social-policy-shadow-0.2; không import model vào Social API, không HIGH auto-hold.
- Request snapshot/dedupe, transactional result+visibility+audit; failures pending/retry/manual, source/evidence đúng context. Native model/lexicon/threshold 0.41 không đổi.
- Full service suite **135 pass**, final worker subset **48 pass**, V3/adapter **130 pass**, Chrome **9 pass**; live HTTP với predictor stub đã chạy down/recover/manual fallback. Mỗi pytest suite có 1 warning TestClient.
- Báo cáo file/lệnh/output và giới hạn: [T012_T017_WORKER_REPORT.md](../../docs/archive/implementation_reports/T012_T017_WORKER_REPORT.md). Tất cả migration/test accounts trên DB tạm; DB demo hiện có chưa được upgrade. Real inference/GPU/PostgreSQL server chưa kiểm chứng.
