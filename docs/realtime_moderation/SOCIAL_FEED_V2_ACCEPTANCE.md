# Social Feed v2 — verified local acceptance, 04/11/2026

T034–T043 additional local scope is verified. Earlier task evidence/statuses
are preserved; new acceptance is separately tracked in TASK_ORDER_AI.md and
AUTO_EXECUTION_STATE.json/social_feed_v2. This is synthetic/local evidence,
not independent human-gold AI acceptance or a production release.

## Import and implementation

13source entries verified;10task ID collisions merged into the canonical
10files without creating duplicate task filenames. Original task bodies and
17control/task files are backed up byte-for-byte. New common safeguards stored
once; external source pack untouched. Source map and checksums:
`reports/social_feed_v2_20261104/MERGE_MANIFEST.json`.

| Task | Verified work |
|---|---|
| T034 | Actual repository audit, transport ADR, state/RBAC/test mapping;13contract tests |
| T035 | Existing durable API reused; five-account post/comment/reply test, idempotency/privacy/recovery;14tests |
| T036 | Explicit original-post/parent/current-reply context test;5worker+15incremental tests; approved processor/rules unchanged |
| T037 | Social Feed/post cards/composer, automatic public-feed refresh, reply context/time metadata and idempotent post retry;build+actual Chrome |
| T038 | Reauthenticated post/comment deep links; live evidence/manual hide/author appeal/restore and audit;Moderator build+actual Chrome |
| T039 | Existing Dataset Center reused;14backend+6actual upload/mapping/export/invalid-label UI checks |
| T040 | Existing annotation reused;6backend+6actual synthetic UI checks, same reviewer R1/R2, history and stale-R2 invalidation |
| T041 | 7guard/lifecycle tests; retained actual CPU-head run/checkpoint and concurrent47ms Social ACK receipt rehashed, no new training |
| T042 | 4guard tests; retained actual V1/r06/T041 paired4-comment report/models/cohort SHA verified and confusion/Macro-F1 recomputed; no new paired inference |
| T043 | 744root/startup+247Social Python tests,4transport tests,2frontend builds;7-context/10check Social Feed E2E and original3-context/8check neural E2E |

## Defects found and retained failures

- The new SSE scheduling probe failed before the fix. Synchronous SQL/pool
  waits inside the async SSE loop could prevent other request cleanup from
  running. `live_routes.py` now awaits `run_in_threadpool(read_page, ...)`.
  The unchanged probe and17related tests pass; full247Social regression and
  actual browser recovery pass. This does not alter model rules or policy.
- Windows Proactor accept WinError64 was observed on a failed browser run;
  demo Social uvicorn uses the opt-in Selector loop. This alone did not solve
  every freeze; subsequent SSE blocking was diagnosed and fixed above.
- Earlier send/login/restore timeouts are retained in T037/T043 failure logs;
  not every historical timeout can be attributed conclusively to one cause.
- An initial default-locale regression had3UnicodeDecodeError failures and
 741passes. With the documented Windows `-X utf8` invocation,744tests pass;
  no sealed research source, reference or dataset was modified.
- Failed browser setup now closes owned Chrome. Every new check retains a
  unique evidence directory instead of overwriting historical handoff reports.

## Current actual browser evidence

`reports/task_rollout_20261104/demo_ab4d39e9057bf41f/` contains the7-context run:
five distinct authenticated actors discover a UI-created post, comment/reply
without F5 or duplicates, real approved-default AI yields grounded repeated
evidence, moderator manually hides, author appeals and moderator restores.
Deep-link reauthentication, network reconnect, literal XSS rendering and a
thread over30comments pass. Owned AI is stopped, a new comment ACK persists
while analysis is pending/retrying, AI is restarted and processing completes
without duplicate comments. Stop script/owned-process cleanup pass.

`demo_d6c905446c193cbd/` contains the original3-context neural workflow8checks
and current component timing report. `demo_6a5b68a80812e8d6/` contains fresh
Dataset/Annotation browser evidence. Automated labels are synthetic tests,
never human gold. Original training/evaluation receipts are explicitly reused,
not presented as freshly executed training or inference.

## Demo and remaining limits

From project root, run `powershell -NoProfile -ExecutionPolicy Bypass -File
.\scripts\demo_realtime_studio.ps1`. Wait for DEMO_READY; seven Chrome contexts
open. Alice creates a post; other users select its feed card and comment/reply;
moderator reads evidence and makes manual decisions. Ctrl+C or
`scripts/demo_realtime_stop.ps1` stops the owned session. Detailed commands:
[demo guide](../ai-update/final-report/REALTIME_DEMO_GUIDE.md),
[Windows setup](../ai-update/final-report/WINDOWS_SETUP_GUIDE.md).

Feed discovery uses1.5second serialized polling with error backoff; opened
post/moderator updates use authenticated SSE. Public bodies remain subject to
existing policy publication; a reply alone never proves an attack. Filters in
Moderator are page-scoped. Other authors are displayed with pseudonymous IDs.
Each launcher invocation creates a separate isolated session; it does not resume
or merge existing demo sessions. Training remains an explicit operator action.
Tiny synthetic timing/metric samples are not capacity or quality guarantees.

V1/r06/default model,0.41,reference/test datasets and original readiness lock
remain unchanged (1311files verified). No production DB reset, deploy, push,
model promotion, r07 or new training. Formal T028/T029 remain BLOCKED and
T030–T033 PARTIAL. Next: operator demo/review, then permitted real-source intake
and genuine solo review rounds before independent evaluation/sign-off.

Full logs, performance definitions and SHA inventory:
`reports/social_feed_v2_20261104/` (PERFORMANCE.json, INTEGRITY.json,
ARTIFACTS.json and ARTIFACTS_ATTESTATION.json). Historical reports remain intact.
