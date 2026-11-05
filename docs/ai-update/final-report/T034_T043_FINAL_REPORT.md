# T034–T043 local implementation report — 04/11/2026

The ten new tasks are implemented and verified for local synthetic workflows.
This does not complete formal real-world acceptance: T028/T029 remain BLOCKED,
T030–T033 remain PARTIAL, and the27historical task status lines are preserved.
The source pack remains intact. No production model/default/threshold/DB was
changed, and there was no push, deploy, r07 or external data download.

## Structure and task status

The verified source pack was merged into the existing repository conventions:

```text
tasks/moderation-ai/       T034–T043, order, dependencies, acceptance, state
services/social-api/      additive live/Studio API, event/worker adapters
services/moderation-ai/   opt-in live endpoint, default-v5 incremental adapter
apps/social-web/          live.html + dedicated config/build
apps/moderation-web/      live.html, studio.html + dedicated config/build
scripts/ml_studio/        dataset/review/training/evaluation adapters
contracts/               live event and internal live-analysis schemas
docs/realtime_moderation/ docs/ml_studio/ and this existing final-report folder
reports/task_rollout_20261104/ source map, tests, screenshots, real artifacts/SHA
```

| Task | Result | Main evidence under reports/task_rollout_20261104/ |
|---|---|---|
| T034 | DONE_VERIFIED: architecture, SSE contract, limits | T034_tests_final.log |
| T035 | DONE_VERIFIED: durable content/job/events and replay | T035_tests_fixed.log, T035_social_regression.log |
| T036 | DONE_VERIFIED: bounded incremental/default-v5 analysis | T036_actual_benchmark.json, T036_root_regression.log |
| T037 | DONE_VERIFIED: two-client UI, reconnect, idempotency | T037_browser_result.json:12 checks |
| T038 | DONE_VERIFIED: moderator evidence/manual review/appeal | T038_browser_result.json:8 checks |
| T039 | DONE_VERIFIED: immutable dataset import/validation | T039_backend_final.log, T039_browser_result.json:6 checks |
| T040 | DONE_VERIFIED: blind solo Round1/2, history/snapshots | T040_backend_fixed.log, T040_browser_result.json:6 checks |
| T041 | DONE_VERIFIED: actual bounded CPU head training/reload | T041_run_manifest.json, T041_browser_result.json:6 checks |
| T042 | DONE_VERIFIED: paired inference, registry/shadow/fallback | T042_evaluation.json, T042_browser_result.json:5 checks |
| T043 | DONE_VERIFIED: actual-neural E2E, Windows start/stop, handoff | T043_browser_result.json:8 checks; T043_interactive_check.json |

Canonical live status: tasks/moderation-ai/AUTO_EXECUTION_STATE.json. Source
mapping, deduplication and the13source SHA entries are in MERGE_MANIFEST.json
and tasks/moderation-ai/TASK_MERGE_REPORT.md. Git metadata is absent; no Git
commit hash or clean working-tree claim is made.

## Implemented behavior, APIs and database changes

The opt-in factory reuses existing auth, Post/Comment, ModerationJob/Result,
visibility policy, review, appeal and audit. Content, job and notifications
commit atomically. Edits/manual decisions/parent changes cannot apply an
obsolete result. Bearer-authenticated fetch SSE replays durable cursors;
snapshots revalidate membership/visibility. Ordinary users receive no raw
moderation evidence. Pending text stays author/staff-only until publication.

Live APIs: `/api/live/threads/{id}/{join,messages,snapshot,events,events/poll}`;
staff `/api/live/moderator/{events,events/poll}` and audited clarification.
AI internal endpoint: `/api/live/moderate/comment`, service-authenticated.
Studio APIs: `/api/studio/datasets`, annotation/history/snapshot,
training-runs/preflight/status/cancel/logs, models and evaluations/exports.
Promotion returns409 even for admin; ordinary users receive403. Existing API
contracts and default entrypoints remain intact.

Social schema remains0004_review. Only explicitly initialized demo DBs receive
the additive live_schema_version/live_thread_members/live_events tables. Studio
owns a separate explicitly initialized SQLite DB, immutable version/source
files, solo review sessions, training/evaluation queues and registry snapshots.
There was no production migration, reset, DROP or existing DB deletion. Stop
signals the owning launcher and retains interactive demo data.

The new screens are Social Live, Moderator Live and Studio's Datasets,
Labeling, Training and Models & Evaluation. Dedicated live build output keeps
sealed original dist files intact. Existing roles remain user/moderator/admin;
Studio training privileges require admin rather than an unapproved new role.

## Model and data safeguards

Default approved V1.1 and original V1/r06 are unchanged, threshold0.41.
Default-v5 is wrapped by a separately reported, subtractive
live-provenance-v1 instance gate: base candidate/raw scores stay visible, while
reported/quoted-only predicates cannot create new live attack evidence. It does
not activate locked v6.1/v6.2. Raw, context, lexicon, target, repeated, policy
and manual visibility are separate. No AI auto-hide/ban is enabled.

Incremental analysis caches neural scores by text and immutable loaded-model
fingerprint; deterministic bounded context is recomputed. The measured
three-message CPU benchmark needed3neural texts instead of6full rescoring,
with identical current raw scores (222.98ms vs274.67ms in that tiny run).
Context/evidence is capped50comments/30minutes; old worker context text is
bounded1000characters per prior comment. This can miss long/distant attacks.
Rules retain known language-coverage limitations; no general accuracy claim is
made from positive workflow controls.

Dataset Center rejects malformed/oversized/unsupported archives and validates
schema, parent graph/time/target, duplicate IDs, exact/near overlap and pinned
development/supervised sources. PII, spreadsheet-formula risks, missing rights
and incomplete audits quarantine data. CSV exports escape formulas. Real
source claims are not automatically accepted. An uploaded human-label claim
is not gold. Source/annotation snapshots remain separate and immutable.

Solo annotation enforces server reviewer identity, revision CAS and current
Round1 revision for Round2; changed Round1 invalidates the latter. Real review
needs a300-second gap; synthetic browser automation has zero gap and is labeled
synthetic reference. No second reviewer or inter-annotator agreement is invented.

## Actual training and paired evaluation

Run **01b3fced9ac2c540be01477d**, candidate SHA256
`908760d455d661df9385e58658d24ca8f1c39783fc2b9abf6079c51609c6d85c`:

- 18new hand-authored synthetic threads/36comments; locked train22/validation10/test4.
- Frozen V1 encoder,2CPUthreads,1epoch,3optimizer updates, trainer elapsed3.36s.
- Encoder/base/source hashes unchanged; reload score error0.0; separate safetensors,
 tokenizer/config/environment/provenance manifest retained via T041_retained.json.
- Validation Macro-F1=1.0 on10synthetic rows is only workflow evidence. No test
 row entered training/selection; no paid/GPU/external service or model promotion.

Actual V1/r06/T041 inference then used the same four locked held-out comments:

| Model | Raw TP/FP/FN/TN | Raw Macro-F1 | Final Macro-F1 |
|---|---|---:|---:|
| V1 |1/0/1/2|0.7333|1.0000|
| r06 |2/0/0/2|1.0000|1.0000|
| T041 smoke candidate |1/0/1/2|0.7333|1.0000|

The candidate supplies no demonstrated improvement over V1 on this tiny cohort;
raw false negatives are retained in per-comment predictions. Final scores
reflect v5 context/lexical processing. The source lacks target/repeated
reference annotations, so their metric denominators are unavailable/null;
none are fabricated. Separate grounded regression/live checks cover those
technical pipelines. All these data are development, never independent human
evaluation. Include new Studio exposure receipts in any future T028 audit.

Registry uses immutable hash snapshots and the existing LocalModelRegistry.
Explicit shadow loading and deliberately injected candidate-loader failure
produced actual V1 fallback inference. Default v1_1 remained unchanged.
Promotion is blocked pending independent human gold and explicit approval.

## Verification and measured latency

Final regression: **737AI/root +244Social =981Python PASS,0FAIL**; the same
Starlette/httpx deprecation warning appears once in each suite. Additionally,
**4frontend transport tests PASS**, both original app builds PASS into separate
regression directories, and new live/Studio builds PASS. No test is skipped
to manufacture success. Earlier failed attempts are retained; fixes addressed
actual reconnect/navigation races, test selectors/ACK synchronization, temp
permissions and environment selection. Reference labels were not changed.

The real neural E2E used the unchanged approved V1.1 checkpoint, worker HTTP,
SQLite and3authenticated browser contexts. It verified grounded repeated
evidence, preserved manual drafts, hide/appeal/restore and audit. Earlier
fixture-based tests are explicitly labeled as such; actual training/reload,
paired model inference and this real-neural workflow are separate evidence.
The four-context interactive launch path and actual PowerShell stop script
also PASS, with idle training workers and no extra training.

Local measured4message sample,3browser contexts, neural server capped2threads:

| Stage | P50 ms | P95 ms |
|---|---:|---:|
| Browser fetch ACK |20.50|31.00|
| Enqueue SQL INSERT before commit |0.157|0.179|
| Queue wait |37.50|50.00|
| Neural/cache + context analysis |74.22|123.39|
| Fanout/snapshot/render/observation |668.50|732.00|
| Compose/send through author analysis visible |880.00|900.00|

The optional local hook measures actual moderation-job SQL INSERT execution
before commit, correlating only committed message IDs and logging no text,
SQL parameters or tokens. Commit/lock time remains part of the fetch ACK.
Enqueue notification spacing was0ms at millisecond resolution in the shared
atomic commit. Three tests verify duration/privacy/idempotent hook registration
and that a log write failure cannot lose a message. Fanout
includes snapshot/render/Playwright observation. These tiny samples are not
production SLOs or load-test results. CPU/OS/methodology/raw timings are in
T043_performance.json and PERFORMANCE.md.

The read-only readiness verifier PASS on **1311files**. Original lock SHA256:
`ac21e3c29b358e9f9a1d8c1850d661e9c858f1c7270d4ae27b78d66dfe823ba3`.
It was not resealed. New source/evidence hashes are in ARTIFACTS.json, not
inserted into the old readiness baseline.

## Remaining acceptance and operator actions

T028 has0collected/allowed real threads and0human labels in its current manifest;
the200real-thread criterion is unmet. Wikimedia remains paused, without fake
contact/User-Agent or new downloads. T029 formal remains BLOCKED; formal
T030–T033 remain PARTIAL. Human source/privacy verification, your own two review
rounds, leakage/exclusion audit, independent evaluation and release sign-off
remain manual. No labeling is demanded during this session.

No production deployment, automatic source rights verification, dedicated
trainer-role migration, GPU training, model promotion, distributed event
retention or production-scale latency guarantee is included. Existing formal
gates and human decisions cannot be bypassed by the local technical results.

Start the local demo with `.\scripts\demo_realtime_studio.ps1`; stop using
`.\scripts\demo_realtime_stop.ps1`. The launcher opens and logs in all four
contexts; no hand-copying service secrets or source edits are needed. Upload
only permitted data and explicitly start an eligible training job if desired;
startup/regression do not automatically retrain. Guides:
[Realtime](REALTIME_DEMO_GUIDE.md), [Training](TRAINING_STUDIO_GUIDE.md),
[Dataset/annotation](DATASET_ANNOTATION_GUIDE.md), [Windows](WINDOWS_SETUP_GUIDE.md).
