# T017 — Worker bền vững và Admin offline
**Status:** DONE (durable worker + offline/manual fallback, stub inference) | **Phụ thuộc:** T009, T011, T012 | **Skill:** `$shieldvi-social-backend`, `$shieldvi-moderation-policy`

## Việc cần làm
1. Transaction content+job; idempotency; retry/backoff, timeout, worker crash recovery.
2. Áp fail-safe: AI lỗi -> pending + retry; trạng thái user chính xác; manual review có thể xử lý.
3. Chống stale result ghi đè quyết định Moderator hoặc content revision mới.
4. Metrics queue size, oldest job, retry, failed, model availability.

## DONE khi
Test AI-down, worker restart, duplicate job, late result, admin approve offline đạt; có output test và công cụ xem queue lỗi.

## Kết quả — 30/10/2026

- SQLite atomic claim/PostgreSQL SQL SKIP LOCKED, token/lease expiry/reclaim, bounded retry/backoff, result revision/decision/request/policy guards, stale owner không finalize; audit system actor riêng.
- CLI --stats và staff GET /api/v1/moderation/jobs có queue size/age/retry/failed/expired leases/model availability; không raw snapshot/token. Staff manual approve/hide và requeue failed có reason/version/RBAC, không cần AI/GPU. Chưa làm dashboard/appeal/provisioning tài khoản thật.
- 48 worker tests pass sau metric update; nằm trong full service suite 135 pass. Live HTTP test AI down/recover và offline manual approval pass; Chrome hồi quy 9 pass. Test clock mô phỏng outage, không claim đã đo downtime thực 10 phút.
- Đã kiểm tra result transaction rollback, restart/snapshot, concurrent claim, old lease, duplicate finalize, late success/error sau manual/edit/delete và hệ thống từ chối downgrade làm mất system audit.
- Toàn bộ file list, migration/rollback, command/log và giới hạn: [T012_T017_WORKER_REPORT.md](../../docs/archive/implementation_reports/T012_T017_WORKER_REPORT.md). Không migrate DB thật, không auto-hold HIGH; real model/PostgreSQL server chưa kiểm chứng.
