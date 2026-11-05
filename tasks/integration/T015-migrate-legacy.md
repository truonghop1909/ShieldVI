# T015 — Chuyển AI backend/dashboard legacy

**Trạng thái:** DONE  
**Phụ thuộc:** T014

## Mục tiêu
Chuyển vị trí code legacy khi 4 app/service đã hoạt động.

## Phạm vi và việc cần làm
- Move có kiểm soát `app/` vào `services/moderation-ai/` và `frontend/` vào `apps/moderation-web/`.
- Cập nhật imports, scripts, static paths, notebook Colab và tests.
- Có kế hoạch rollback, không xóa checkpoint/database hay lịch sử.

## Tiêu chí nghiệm thu
- Legacy `/api/analyze`, `/health`, `/dashboard/` vẫn đáp ứng test.
- Fullstack E2E, pytest và npm build đạt hoặc ghi blocker rõ.

## Kết quả kiểm thử / thay đổi
Đã chuyển `app/` sang `services/moderation-ai/app/`, `frontend/` sang **`apps/moderation-web/legacy-v3/`** để giữ dashboard Social tại thư mục cha. Có root import/npm compatibility, path model/DB ổn định theo repo root, requirements/static/scripts/tests/Colab/Windows launcher đã cập nhật; snapshot rollback-source giữ nguyên. [Files, lệnh, output, rollback và limits](../../docs/archive/implementation_reports/T015_MIGRATION_REPORT.md).

Gate trước move: 139 legacy + 177 Social API tests, cả 3 build pass. Sau move: **143 legacy/migration + 177 Social API tests, 16 Chrome tests, cả 3 builds và lệnh build cũ PASS**. HTTP trước/sau cùng checkpoint CPU thật cho legacy/internal response/OpenAPI/static bằng nhau; review/summary roundtrip chỉ DB tạm. **52 checkpoint/dataset/database files giữ hash**, Social DB demo vẫn 0002, không migrate; 0.41/HIGH-off giữ nguyên. Colab/GPU/Drive/ZIP thực tế chưa chạy; chỉ compile/layout. Không deploy/train/push, không xóa compatibility/DB/history.
