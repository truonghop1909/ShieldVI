# T018 — Dashboard Admin, audit và kháng nghị
**Status:** DONE | **Phụ thuộc:** T013, T016 | **Skill:** `$shieldvi-moderation-admin`

## Việc cần làm
- Queue ưu tiên, tabs Reports/Appeals/Failed; full text + parent context; phân biệt ai_label/risk/visibility.
- Approve/hide/restore phải có reason, actor, timestamp, decision version.
- Author xem trạng thái và gửi appeal; moderator quyết định trên appeal, có audit.
- Kiểm thử quyền truy cập, không lộ dữ liệu held, reviewer concurrency.

## DONE khi
Demo từ đăng bình luận đến admin quyết định, kháng nghị và khôi phục; test auth/IDOR/audit passed.

## Kết quả thực hiện

Đã làm cùng T013 theo yêu cầu: priority queue Reports/Appeals/Failed, full text/parent context, tách AI/risk/visibility; approve/hide/restore/claim/appeal resolve có reason/actor/time/decision version. Author status/appeal qua Social Web; reports dedupe không auto-hide; audit/provenance/FP feedback staff-only. Schema `0004_review` chỉ trên DB tạm, rollback giữ lịch sử.

**PASS:** 158 Social API tests (23 review gồm auth/IDOR/held ancestor/reviewer concurrency/audit/stale AI), 130 V3 tests, 6 Chrome review và 9 Chrome Social regression, hai frontend builds. Browser demo đã đăng comment → hide → appeal → restore → re-login audit; không gọi inference thật. [File/lệnh/log/demo/giới hạn](../../docs/archive/implementation_reports/T013_T018_ADMIN_REPORT.md). DB demo hiện có chưa migrate, chưa cấp staff thật, chưa kiểm chứng PostgreSQL/GPU/HIGH; không thực hiện T014/T019/T015.
