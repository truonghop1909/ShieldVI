# Training Studio guide

Start the isolated demo using [REALTIME_DEMO_GUIDE.md](REALTIME_DEMO_GUIDE.md).
In its Studio browser, upload
`reports/task_rollout_20261104/T041_synthetic_smoke.json` in Datasets. Keep origin
synthetic, type SYNTHETIC and UTF-8. Validate and inspect the accepted version,
SHA, labels, locked thread split and warnings. This small hand-authored fixture
has18threads/36comments and is workflow data, not a benchmark.

Open Training, choose the accepted version, inspect the bounded CPU preset,
run preflight and explicitly start. QUEUED means waiting for the separate worker.
Watch stage, loss, per-epoch validation, optimizer count and final state. A
successful job must have real weights, hashes and a successful neural reload.
Download its run manifest. Cancel terminates only the owned child; failed jobs
are not silently retried or marked completed. No arbitrary Python/GPU/path
configuration is accepted. Full/real/mixed training remains gated by its missing
source/resource approvals.

The run already verified in this task is **01b3fced9ac2c540be01477d**. Its retained
root is listed in `reports/task_rollout_20261104/T041_retained.json`; weights are
under `training_runs/{run_id}/candidate/`. V1/encoder/source hashes remain
unchanged; threshold0.41; this is classifier-head training, not r07 or full
encoder fine-tuning. Validation10 rows / Macro-F1=1.0 is only a tiny synthetic
sanity check. Four held-out comments were scored separately in T042 after
candidate selection; raw candidate/V1 each missed one toxic row, while r06 did
not. Those results cannot establish a release improvement.

Models & Evaluation compares registered candidates on the same locked synthetic
holdout and exports JSON/CSV/Markdown with provenance. Target/repeated metrics
require actual reference metadata; unavailable denominators remain null. The
local shadow fallback demo restores verified V1 in an isolated loader, never
changes the service default. Promotion is blocked server-side.

The autonomous smoke is complete and is not automatically rerun by regression
or demo startup. Starting another job in the UI is an explicit operator action.
Operational details: [CPU worker](../../ml_studio/TRAINING.md) and
[registry/evaluation](../../ml_studio/EVALUATION.md).
