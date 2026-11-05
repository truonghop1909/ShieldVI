# T014 — E2E, security và tài liệu vận hành

**Trạng thái:** DONE  
**Phụ thuộc:** T010, T012, T013

## Mục tiêu
Hoàn thiện demo fullstack không cần deploy public.

## Phạm vi và việc cần làm
- Kiểm thử register/login/post/comment/moderate/review/appeal.
- Kiểm tra JWT, CORS, XSS, IDOR, rate-limit, backup và env.
- Thêm hướng dẫn chạy 4 tiến trình và test smoke.
- Nếu dùng Colab: ghi giới hạn hạ tầng, không public proxy không bảo vệ.

## Tiêu chí nghiệm thu
- Chạy và lưu bằng chứng test/build; báo cáo limitations rõ ràng.

## Kết quả kiểm thử / thay đổi
Đã kiểm chứng E2E đủ 4 server + worker, register/login/post/comment/moderation/review/appeal/recovery; auth/opaque Bearer (không JWT), CORS/CSRF cookie rejection, XSS/IDOR/rate-limit/log PII, backup/restore trên DB tạm và env boundary. Sửa các lỗi SQLite concurrency/redaction/reason thực sự tìm thấy. [Files, lệnh và evidence](../../docs/archive/implementation_reports/T014_T019_VALIDATION_REPORT.md), [runbook 5 process/backup](../../docs/guides/RUN_LOCAL.md).

**PASS:** 177 Social API, 139 legacy, 16 Chrome tests; hai frontend build; outage process AI thật 600s giữ pending và phục hồi bằng manual retry. 19 privacy/security subset cuối pass. Không public deploy/Colab/migrate DB demo, HIGH tắt; PostgreSQL server/GPU/production security còn chưa kiểm chứng.
