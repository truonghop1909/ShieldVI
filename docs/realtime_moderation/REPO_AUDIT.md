# Social Feed v2 repository audit — 04/11/2026

This is a local synthetic implementation audit, separate from independent AI
acceptance. T028/T029 remain BLOCKED and T030–T033 PARTIAL. No Git metadata is
present; a clean working tree cannot be claimed. Source import map and original
task backups: `reports/social_feed_v2_20261104/MERGE_MANIFEST.json`.

| Layer | Verified reusable implementation | Additional v2 work |
|---|---|---|
| Auth/content | `shieldvi_social.content_routes`: bearer-derived actor, feed/post/comment CRUD, parent checks, optimistic revisions and idempotent transaction | Verify five independent accounts against a disposable DB |
| Durability | Comment/job/audit and `live_store` event rows share transaction; worker claim/lease/retry/CAS already tested | Reuse, rerun recovery and concurrency tests; no production migration |
| AI context | Existing builder includes synthetic `post:` ancestor, parent and bounded recent history; incremental default-v5 adapter | Verify source inclusion and actor-target provenance; no new rules/model |
| User UI | `apps/social-web/src/live.jsx` has comment SSE, replies, revision reconciliation and pagination | Replace ID-first Conversation entry with paginated post cards, visible post composer, automatic feed refresh and five-account demo |
| Moderator | Live queue, context, separate raw/advisory/target/evidence, manual decisions and appeals | Verify post/comment deep links and updated five-account flow |
| Dataset/ML | Existing DatasetStore, immutable snapshots, solo R1/R2, CPU-head job lifecycle, evaluation and registry | Revalidate controls and retained actual training receipt; no automatic retraining |

## ADR: transports and compatibility

Keep `live-1.0` authenticated fetch-SSE for an opened post and moderator queue,
with the same durable log's authenticated JSON polling fallback. HTTP POST
remains the write transport. Existing post/comment APIs are unchanged. Names
such as `post.created` in the new source pack are semantic aliases, not new
unversioned wire events: `conversation.message.created` includes post or
comment identity, and `moderation.analysis.updated` invalidates the authorized
snapshot. A reply recipient never proves an attack target.

The feed uses serialized bounded-interval GET `/api/v1/feed` refresh (1.5seconds
after completion, backing off on error), not global unfiltered moderator SSE.
This reuses the existing public-post visibility filter, including removals,
without revealing pending/hidden posts or private evidence to feed watchers.
Refresh pauses with component teardown/logout; stale requests are aborted.
Per-post comments and AI updates still use SSE. Feed polling latency and AI
CPU inference are not an instantaneous-delivery SLA.

## UI state mapping

| Requested UI state | Existing source of truth |
|---|---|
| PENDING_ANALYSIS | job QUEUED, content PENDING_MODERATION |
| ANALYZING | job PROCESSING |
| ANALYZED | job COMPLETED; does not mean CLEAN |
| NEEDS_REVIEW | authorized content visibility HELD_FOR_REVIEW or PUBLISHED_FLAGGED; separate from analysis completion |
| RETRYING | job RETRYING; preserve existing comment |
| AI_UNAVAILABLE | job FAILED/UNKNOWN; never manufacture CLEAN |
| SUPERSEDED | stale revision or deleted content; refetch snapshot |

## Security and acceptance trace

| Boundary | Authorization and test evidence to run |
|---|---|
| Feed | Authenticated public visibility only; pending creator gets own ACK via detail, peers wait for policy publication; T035 live/content tests |
| Post subscription | Existing readable post AND membership; session rechecked, expired/unauthorized => deny; test_live_api.py |
| Actor/reply graph | Actor derived from bearer, wrong-post parent denied, depth bounded; test_content.py, test_live_api.py |
| Moderator | Staff-only global event stream and evidence detail; regular accounts cannot subscribe; test_live_review.py |
| Dataset/train | Admin-only mutation, source/PII/split gates, immutable snapshots, no automatic promotion; Studio tests |
| Durability | Transaction rollback, restart, same-key races, stale completion, context revisions, AI offline/retry; live API/analysis worker tests |
| Browser | Five authenticated users create post/comment/reply, reactive feed, no reload/duplicates, UI XSS/long text, moderator review/appeal; new Social Feed E2E |

T034 is the contract/audit prerequisite; runtime acceptance remains separate
for T035–T038 and cannot be inherited from the historical completed rollout.
Original sequence, versioned schema and failure policy remain authoritative:
[sequence](SEQUENCE.md), [contract](CONTRACTS.md), [failure policy](SLO_AND_FAILURES.md).
