# Durable sequence and failure/recovery

```mermaid
sequenceDiagram
 participant C as Authenticated client
 participant S as Existing Social API + opt-in live routes
 participant D as SQLite/Postgres
 participant W as Existing worker + live wrapper
 participant A as Canonical AI + incremental adapter
 C->>S: Send comment, membership, Idempotency-Key
 S->>D: Transaction comment + moderation job + durable event
 D-->>S: COMMIT
 S-->>C: ACK ID/revision, QUEUED
 C->>S: Authenticated SSE since cursor
 S->>D: Read committed events, recheck auth/membership
 S-->>C: Minimal event (no text/evidence)
 W->>D: Claim job with token/lease, snapshot/hash
 W->>A: Bounded context + current revision
 A-->>W: Actual raw + v5 advisory/evidence/versions
 W->>D: CAS current content/decision/job lease
 D-->>W: Result + policy + audit + event COMMIT
 S-->>C: Updated event
 C->>S: Authorized snapshot/review detail
```

POST retry keeps same key; changed body conflicts409. Worker crash recovers expired lease, old claim cannot finish. Edit/delete/manual decision invalidate old job/result; late result never restores tombstone or overrides moderator. AI timeout queues RETRYING with existing5/30second bounded backoff; exhausted FAILED remains pending/manual recovery, no invented labels.

SSE ID is durable monotonic integer. Client remembers cursor, orders by ID, ignores duplicate or older content/decision revisions. Reconnect revalidates token/active user/role/membership; expired/revoked access stops stream. Stream duration bounded25s, reconnect uses backoff; heartbeat does not keep a DB transaction open. Snapshot and cursor from same transaction, preventing snapshot/subscribe gap. Future retention/gap or invalid-ahead cursor requires fresh snapshot, not silent event loss.
