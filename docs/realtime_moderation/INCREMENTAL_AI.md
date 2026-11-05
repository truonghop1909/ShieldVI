# T036 — opt-in continuous bounded conversation analysis

Canonical AI is composed by `app.live_entrypoint:create_app`; original singleton/default endpoints remain unchanged, including internal1.0 and research2.0. New `/api/live/moderate/comment` uses the same service authentication/body1MiB/one-inference-at-a-time guard. No browser service token. Default weights remain approved V1.1 with threshold.41; default processor is frozen-v5. Experimental-v6.2 is available only in an explicitly authorized isolated analyzer/shadow constructor; live worker client rejects it.

New additive response contract extends1.0, vendored identically in both services and generated JSON schema in contracts/live_moderation_response.schema.json. `conversation_signals` separates current v5 context candidate, base instance candidate, derived live instance, assessment, policy risk, reply recipient, grounded target, typed attack instances, cache counters, model fingerprint and versions. Raw/classifier label and original v5 assessment remain unchanged. Social worker persists this subclass in existing ModerationResult.signals_json; original policy remains advisory/shadow, never auto-hide.

Neural cache is per immutable loaded predictor/model fingerprint plus SHA256(text), bounded2048LRU entries, memory only/no raw text persisted. Text edit misses only that score key; model replacement starts a new cache. Recompute deterministic v5 signals over supplied bounded50context+current, not an unbounded thread. Old supplied context is incomplete, evidence outside it is unavailable. Default instance horizon1800seconds; bounded constructor config only, no post-score threshold tuning. Parent-chain/context assembly remains canonical worker_context, so inherited1000char context truncation and same-second timestamp limitations remain explicit.

Three-message actual CPU smoke on approved default: full6neural texts vs incremental3; raw current scores identical, repeated evidence[b,c] grounded. Measured full274.6676ms/incremental222.9778ms, two CPU threads, warmup excluded. Single synthetic smoke, not an SLO, benchmark distribution or real-world quality claim. Full measurements/model SHA/hardware in T036_actual_benchmark.json.

## Provenance guard and inherited v5 limitation

An initial negative control reproduced v5 treating a pure apology/report as a directed attack. Do not activate research v6.2 to hide this. The opt-in live adapter adds **subtractive `live-provenance-v1` instance gate**: known v5 predicates occurring solely inside reported/quoted clauses cannot support new live instances. Assignment outside quote and endorsement/new attack clauses survive. The base v5 candidate/assessment/raw remain visible separately, so a classifier/v5 false-positive may still request REVIEW; this gate does not invent CLEAN or human labels. Rule versions disclose base-v5 and gate version. Same actor/target evidence must pass the gate and horizon and contain current content before creating a new event.

Client independently validates supplied snapshot IDs/participants/timestamps, nonself targets, parent/textual or bounded reciprocal grounding, distinct actor-target evidence and correlation. Arbitrary/research/unknown IDs rejected; no raw-score-only instance. Attack source must come from the authorized snapshot, not unrelated stored content. Normal client only sees status; staff obtains signals through existing review detail RBAC.

## Snapshot freshness and crash/retry

`ConversationWorker` reuses original Worker transaction/CAS/lease/idempotency. Its owned() hook runs inside finish's existing post/content lock and verifies supplied context text/author/tombstone against current DB. Changed parent/dependency discards result, clears snapshot/hash/lease, generates fresh request correlation and RETRY_WAIT; total attempts remain bounded. It never saves stale response or resurrects deleted content. Existing stale own-revision/manual-decision checks still run.

Run AI opt-in factory on loopback and worker with `python -m shieldvi_social.live_worker --incremental`. Original worker without flag stays legacy1.0. New functionality is opt-in local release, not production activation or a rewrite of readiness baseline. All original locked source files remain unchanged.

Tests:15AI cache/provenance/auth/privacy/factory tests,4new worker/snapshot/security tests,30combined live Social tests; full regression evidence recorded separately. Actual inference benchmark distinct from fixture-AI tests. No training/model/default/DB reset/deploy.
