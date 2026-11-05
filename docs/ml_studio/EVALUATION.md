# Models & Evaluation (T042)

Use the same retained Studio root as Training. Initialize the separate registry
explicitly, then start its CPU evaluation worker:

```powershell
$env:PYTHONPATH='scripts'
.\.venv\Scripts\python.exe -m ml_studio.evaluation --root $env:SHIELDVI_STUDIO_ROOT --initialize-only
.\.venv\Scripts\python.exe -m ml_studio.evaluation --root $env:SHIELDVI_STUDIO_ROOT
```

Registry snapshots are content-addressed and SHA-verified. Existing V1/V1.1/r06
entries reuse LocalModelRegistry and readiness-pinned hashes. Only COMPLETED,
verified Studio runs can be added as unapproved experimental candidates.
The default remains v1_1. No runtime selector or existing registry is rewritten.
Candidate loading requires explicit local shadow mode. Promotion endpoint is
blocked server-side, including for admin, until independent human gold, formal
gates and explicit production approval exist. No synthetic score grants approval.

The wizard chooses 2–3 distinct registered models and an accepted, locked
synthetic test partition, never training/validation input. A durable evaluation
job runs actual offline CPU inference separately from HTTP. Per-model raw,
context/advisory, lexical, policy, target and repeated outputs remain separate.
JSON/CSV/Markdown reports contain confusion counts, toxic P/R, Macro-F1, errors,
source/model/registry SHA and timing. Evaluated data is recorded in an additional
development-exclusion receipt; it must not become independent real evaluation.

The T041 source's four held-out comments carry binary reference labels but no
target/repeated gold. Their target/repeated/evidence denominators are explicitly
unavailable (null), not fabricated metrics. Existing grounded live/regression
fixtures provide separate technical target/repeated evidence. Before any future
formal T028 run, include Studio source/exposure receipts in its exclusion audit.
T028/T029 remain BLOCKED and T030–T033 PARTIAL.

T042_evaluation.json/csv/md under reports/task_rollout_20261104/ records actual
V1/r06/T041 inference on the same four comments. A deliberate shadow loader
failure invokes the existing verified V1 fallback and performs real probe
inference. The failure is isolated to the demo loader, not production. Tiny
synthetic results are workflow evidence only; no threshold tuning or selection
is justified. T042_browser_result.json has5 Chrome workflow checks;
T042_backend_tests.log has4 guard/RBAC/integrity tests. No new training occurred.
