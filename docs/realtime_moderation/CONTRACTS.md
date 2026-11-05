# Live contracts

Envelope `live-1.0`: [JSON schema](../../contracts/realtime_event.schema.json), generated from shieldvi_social.live_contract.LiveEventEnvelope. Content/reply recipient, grounded attack target, raw toxicity, context, policy risk, visibility are separate. Event contains IDs/version/status only; detailed text/evidence via existing authorized snapshot/review reads. No bearer/query credential or raw body in event/log.

Planned additive opt-in routes:

- POST `/api/live/threads/{post_id}/join`, DELETE same membership; require existing readable Post. No joining someone else's hidden/pending post.
- POST `/api/live/threads/{post_id}/messages`: existing CommentCreate + Idempotency-Key UUID, same revision1/job semantics. Returns existing CommentOutput plus analysis state via snapshot; no blocking AI.
- GET `/api/live/threads/{post_id}/snapshot?page=1`: existing visibility-filtered posts/comments, max50/page, analysis statuses and committed cursor.
- GET `/api/live/threads/{post_id}/events?since=0`: fetch SSE Authorization, since/Last-Event-ID cursor; event_id reused as SSE id. `once=true` returns one bounded SSE page for verification.
- GET `/api/live/threads/{post_id}/events/poll?since=0`: same authorization/envelopes, max100/page, has_more/cursor. No second event transport/store.
- GET `/api/live/moderator/events`: staff-only global minimal notifications, detail stays behind existing review RBAC.
- POST AI `/api/live/moderate/comment`: existing1.0 request, additive response subclass carries `conversation_signals` with separate raw/advisory/target/evidence/rule metadata; service auth, default-v5 only unless explicitly isolated test/shadow.

Original API routes and schema0004 remain untouched. Error401credentials/403membership or role/404unreadable content/409idempotency or revision mismatch/413size/422schema/429bounded capacity/503AI unavailable. All writes preserve body on client retry; no frontend-supplied SQL/Python/shell/path execution.

Jobs map QUEUED→QUEUED, PROCESSING→PROCESSING, SUCCEEDED→COMPLETED, RETRY_WAIT→RETRYING, FAILED_PERMANENTLY→FAILED; STALE_IGNORED→SUPERSEDED. Message content_revision and decision_version prevent stale update; analysis_revision is analyzed content revision, correlation is request_id. Same-revision neural retry never creates a second content/job/result.

## Live display identity extension — live-identity-1.0

`GET /api/live/feed?page=1` reuses the canonical authenticated public feed,
10items per page, and adds server-derived display metadata. Live snapshot
post/comments and live message ACKs also carry `author_username`,
`reply_to_user_id`, `reply_to_username` alongside unchanged `author_id` and
`parent_id`. Snapshot retains `schema_version=live-1.0` and adds
`identity_version=live-identity-1.0`. Identity fragment schema:
[live_content_identity.schema.json](../../contracts/live_content_identity.schema.json).

Names are retrieved only for already-authorized content and readable parents;
no email, account secret, session or role is returned. A hidden/unreadable
parent's recipient metadata remains null. Client-supplied author/recipient
claims are rejected by the unchanged CommentCreate schema. Core `/api/v1`
responses and AI1.0/2.0 contracts remain untouched.

The UI reply tag is a structured `@username` chip tied to the existing parent
comment ID. It does not prepend text to the authored body or manufacture an
attack mention. AI receives canonical UUIDs, original text and the parent/context
graph through the existing worker. Reply recipient is distinct from directed
attack target: a clean reply has a recipient and no attack instance; attack
target/repeated require existing context and evidence. Manually typing a handle
without choosing Reply does not create a parent relationship. Historical plain
text or missing parent links are not rewritten or inferred from display names.

## Staff quick JSON analysis — quick-test-1.0

Admin/Moderator UI tab **Test AI bằng JSON** uses owner-private background jobs:

| Route | Behavior |
|---|---|
| POST `/api/live/moderator/test-conversations` | Staff bearer required. Accept thread_id, optional profile=conservative, comments; return202job immediately |
| GET same `/{id}` | Same owner/staff only; other staff404, normal user403. Returns id/status/completed/total/result/error |
| DELETE same `/{id}` | Owner requests cancellation; CANCELLING until current bounded AI call ends, then CANCELLED |

Request schema: [admin_quick_conversation.schema.json](../../contracts/admin_quick_conversation.schema.json).
Comments use existing ContextComment fields: comment_id/user_id/text/timestamp,
optional parent_id/mentioned_user_ids. Limits:1–50comments,128KiB HTTP body,
64000text characters total, timezone-aware chronological timestamps, unique
IDs and parents preceding replies. Unknown model/threshold/path overrides and
research profiles are rejected. No credentials or URLs may be supplied by client.

States: QUEUED/RUNNING/COMPLETED/FAILED/CANCELLING/CANCELLED. One job runs per
Social API instance; up to16recent jobs retained only in memory for30minutes.
Restart loses these transient jobs. Total run budget120seconds, individual AI
read timeout bounded by15seconds/config. Cancellation is cooperative between
comments. Result size cap4MiB; upstream error/timeout gives FAILED with no fake
CLEAN scores. No Social content, moderation-result, dataset or gold-label writes.

Backend uses existing authenticated LiveAIClient/default-v5 service endpoint
for each chronological prefix; service token never reaches the browser. Input
text/IDs/parent graph are preserved, processor/fingerprint consistency checked,
and model/0.41 remain unchanged. Result comments carry full LiveModerationResponse
as `analysis`; raw score/label, final assessment, context, lexicon, target,
policy and per-comment repeated evidence remain separate. `repeated_events`
summarizes the latest observed event per actor-target pair. Scope is manual test,
not human gold or independent evaluation. The UI can export result JSON locally.
