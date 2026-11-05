# T019 — Đánh giá AI/policy và bảo mật riêng tư
**Status:** DONE (local evaluation, giới hạn policy gold ghi rõ) | **Phụ thuộc:** T012, T013 | **Skill:** `$shieldvi-moderation-policy`, `$shieldvi-ai-integration`

## Việc cần làm
- Tập test comment thật riêng, synthetic tách biệt, không dùng nhãn AI làm gold.
- Đo ViSoBERT/lexicon/hybrid, policy auto-hold FP/FN, review load và latency.
- Test security: auth, role, IDOR, rate limit, XSS, CORS, CSRF (nếu dùng cookie), log PII.
- Chạy e2e trên worker lỗi + admin offline + appeal; viết report điều chưa kiểm chứng.

## DONE khi
Có metrics từ run thật, hạn chế rõ ràng, pytest/build/e2e evidence và recommendation bật/tắt auto-hold.

## Kết quả thực hiện

Người dùng xác nhận **chưa có bộ thread/comment người gán nhãn độc lập; dùng ViCTSD có sẵn và ghi rõ policy chưa đủ dữ liệu**. Đã inference CPU thật trên đủ 1.000 ViCTSD test gốc, checkpoint active V1.1, giữ 0.41/hash/split: precision 0.5524, recall 0.5273, Macro-F1 0.7420. Lexicon review-screening không thêm hit trên tập này; hybrid review load 10.5%. 30 câu synthetic tách biệt, không dùng nhãn AI làm gold; không claim V1 baseline hoặc holdout mù mới.

177 Social API tests, 139 V3 tests, 16 Chrome tests, hai frontend build pass; 19 privacy/security subset cuối pass. E2E worker lỗi/admin offline/appeal/recovery và AI process outage 600s pass. Khuyến nghị **HIGH auto-hold tiếp tục tắt**: thiếu gold HIGH/target/repeated, các metrics đó null/N/A. Chưa kiểm chứng PostgreSQL/Colab/GPU/load production, retention và license bản ViCTSD local chưa reverify; không tải dữ liệu mới hoặc migrate DB demo. Không có skill model-eval trong catalog local; dùng policy/AI integration và evaluator có test riêng.

[Báo cáo, giới hạn, files, command/log/metrics](../../docs/archive/implementation_reports/T014_T019_VALIDATION_REPORT.md), [runbook](../../docs/guides/RUN_LOCAL.md). Không làm T015.
