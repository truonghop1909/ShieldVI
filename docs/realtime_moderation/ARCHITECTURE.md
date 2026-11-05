# T034 — Realtime extension architecture (local)

Existing stack verified: shieldvi_social FastAPI/SQLAlchemy, schema0004_review, bearer auth, posts/comments, revision-safe durable ModerationJob/Worker, immutable ModerationResult and manual review/appeal. AI canonical app remains separate; no Social DB access. Social/Admin React already exist; no chat/DM module or realtime transport exists.

Use authenticated **fetch SSE**, with JSON polling fallback on the SAME event log. Client sends through HTTP, so WebSocket adds no required bidirectional capability. Avoid EventSource query-token leakage. Authorization Bearer uses existing sessions; no service token in browser. Existing public post/comment thread is the conversation, not new DM or production private chat.

Additive opt-in factory reuses canonical Social app and routers; original entrypoint/locked files remain byte-identical. Add separate extension metadata for durable live event rows and membership, in the same DB/transaction as existing content/jobs. Base Alembic0004 remains unchanged; explicitly initialize extension only in a named disposable/local DB. Default startup never silently migrates a DB. Rollback is deactivating the extension entrypoint while retaining content/jobs/events; no automatic DROP.

Message create delegates existing authenticated/rate-limited/idempotent comment mutation; message+job remain atomic. Engine-scoped ORM hooks append durable event in that transaction. Worker wrapper reuses Worker claim/lease/retry/finish, enabling same hooks. Publish is reading committed event rows; no transient in-memory fanout. No event appears from rolled-back writes; no lost notification on restart.

Normal user needs explicit membership AND existing post visibility; no private content becomes readable through joining/SSE. Public post join is allowed, author can read own pending post, staff retain RBAC. Pending comments keep original visibility: author sees ACK/pending immediately; another member receives content only after existing policy publishes it. SSE reveals no body/raw score/target/evidence, only IDs/revisions/status. Snapshot reuses existing content visibility/parent filtering; staff fetch authorized review detail for evidence. Do not claim public-thread demo is private chat.

T036 incremental AI adapter is additive and uses default-v5 signal processor with existing approved model (.41), not research v6.1/v6.2. Keep original internal1.0 and research2.0 endpoints unchanged. Opt-in conversation worker uses new internal response extension carrying v5 context/target/repeated; canonical policy/DB ownership unchanged. Bounded context50, raw score cache by model fingerprint/text hash, no network or fake scores when unavailable. Context changes recompute deterministic signals, cached text scores avoid repeated neural inference. Window incompleteness is explicit; evidence outside the supplied snapshot is not invented.

Studio branch reuses existing dataset/solo annotation/training/registry tooling behind staff-only APIs when implemented. No trainer role silently added to frozen users role constraint: admin owns Studio start/cancel, moderator read-only if specified. Upload ≠ approval; real/private rights, PII and development/test leakage gates remain. User now authorizes a distinct bounded T041 synthetic CPU smoke after validation; no r07/fullGPU/default/promotion inferred.

## Compatibility/integration dependencies

The current Social Feed v2 audit, transport ADR, UI state mapping, RBAC matrix
and acceptance-to-test map are in [REPO_AUDIT.md](REPO_AUDIT.md). The main entry
is now a post feed/composer with multiple authenticated commenters; thread SSE
and advisory policy are reused, not replaced by private chat.

T034 contracts→T035 durable events→T036 incremental adapter→T037 two-client UI→T038 staff live review. T039 dataset validation independent afterT034; T040 unlabeled workflow precedes training from those labels; T041 prelabelled synthetic smoke thenT042 actual evaluation/registry; T043 full acceptance requires all. Formal T028/T029BLOCKED/T030–T033PARTIAL unchanged.
