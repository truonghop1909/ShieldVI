# Budgets and measurement plan (not measured claims)

No neural inference inside send request; existing transactional ACK only. Measure perf_counter ACK, observer delivery, queue wait from durable timestamps, inference wall time and result delivery separately. Record hardware, model/config/DB/thread load and fixture vs actual model; no invented percentile or latency guarantee. Initial local target budgets: ACKp95<500ms and event catch-up<1s excluding inference, to be verified rather than reported achieved.

Caps: HTTP1MiB, content8000chars, context50comments/64Kchars, snapshot50rows, event100rows/page, bounded25s SSE windows/poll250ms, one worker inference at a time. Reconnect jitter/backoff1–30s, fresh snapshot on unknown/gap cursor. Guard active sessions/membership every stream poll; server-side ownership/visibility always wins over stale browser state. No raw text in notification log; full moderation data is role-restricted.

Failure tests: transaction rollback (no orphan event), duplicate POST409/replay200, worker restart/lease expiry, stale edit/delete/manual result, two-user IDOR, hidden parent, suspended/expired session, cross-thread parent, event reorder/duplicate, disconnect/cursor replay, AI503→retry→recovery, supervisor restart with same DB. Retention and high-load multi-host fanout remain capacity work; this local durable polling-backed SSE design is not a production scale claim.

Migration plan: base Alembic upgrade on disposable DB first, explicit extension init adds new metadata tables only, marker verifies expected version; do not migrate live DB. Repeated init is idempotent; original factory still starts on base0004 with extension tables present. Backup/rollback uses existing tools and deactivation, never dropping real tables.
