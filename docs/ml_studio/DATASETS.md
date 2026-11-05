# Local Dataset Center

Opt-in only. Initialize a **new empty directory inside this project**:

```powershell
$env:PYTHONPATH='scripts'
.\services\social-api\.venv\Scripts\python.exe -m ml_studio.datasets --initialize datasets/studio_local
$env:SHIELDVI_STUDIO_ROOT=(Resolve-Path datasets/studio_local).Path
```

Run the live Social factory against an explicitly initialized local Social DB
(see ../realtime_moderation/RUN_LOCAL.md). Serve `apps/moderation-web/studio.html`
using vite.live.config.js. Existing Social/admin accounts remain authoritative;
Studio requires admin. Tokens stay in memory, Authorization headers only, no
cookies or credentials in URLs. Stopping the app does not remove Studio data.

CSV/JSON/JSONL are UTF-8, <=1MiB and <=1000 comments; HTTP JSON envelope <=2MiB.
ZIP/model/pickle/code uploads are not supported, including oversized archives.
No extraction/virus-scanner capability is claimed. CSV column mapping is
canonical name → source column. JSON can be rows or threads with comments.
Required: text, thread_id, comment_id, user_id, timezone-aware timestamp.
Labels CLEAN/0 and TOXIC/1 map explicitly; UNCERTAIN stays separate and cannot
train. UNLABELED requires absent labels. Optional parent, target, category,
severity and source are preserved; target/repeated metadata is not binary text.

Source bytes, normalized JSONL, manifest and quality report are content-hashed.
Imports use PENDING validation internally before atomic ACCEPTED/REJECTED/
QUARANTINED registration. Failed rows remain visible in reports, not silently
accepted. Identical requests replay one version; changed metadata for the same
source requires an explicit parent_version. Parent snapshots remain immutable.

Checks cover schema, graph/chronology/target, exact/near duplicates, pinned
development and supervised split overlap. Near comparisons use normalized
5-gram Jaccard >=.90 (comments >=40 chars, full threads >=80). A 1M comparison
budget fails closed into quarantine. Other accepted Studio imports also produce
overlap warnings and block training. Thread SHA fixes 70/15/15 group splits;
holdout is immutable and never part of training. Small datasets can lack a
partition; training preflight must reject that condition.

Actor IDs become keyed local pseudonyms. PII patterns and CSV formula risk
quarantine the import; original bytes stay private to admin, never public feeds.
CSV exports escape spreadsheet formulas. Name/address recognition is incomplete:
human privacy review is still required for real data. This is not anonymization
certification. Real sources always await manual rights verification, even when
URL/license/consent/receipt fields are supplied. HUMAN_REVIEWED upload claims do
not create human gold. No real-world acceptance or new collection is performed.

The server verifies the versioned v6.2 development exclusion snapshot and its
source SHA records; the sealed default loader/readiness lock is unchanged.
Unknown encoder pretraining overlap cannot be audited. No data download,
training or production activation occurs in Dataset Center.

Evidence: reports/task_rollout_20261104/T039_backend_final.log (17 related PASS),
T039_browser_result.json (6 real Chrome workflow checks), T039_build.log. E2E
source/export/screenshot are synthetic, not independent evaluation data.
