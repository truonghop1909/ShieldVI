# Training Studio (T041)

Open studio.html → Training. Select 1–4 accepted dataset versions, run preflight,
then start the bounded CPU smoke. V1 is read-only; strategy is frozen encoder /
classifier head, synthetic-only. Mixed/real/GPU modes fail closed until their
source rights, resource and experiment approvals exist. This does not train r07.

Start the separate worker from the project root:

```powershell
$env:PYTHONPATH='scripts'
.\.venv\Scripts\python.exe -m ml_studio.training --root $env:SHIELDVI_STUDIO_ROOT
```

The HTTP process has no torch import and never starts training itself. SQLite
jobs/config/preflight are durable and idempotent per authenticated admin/key.
Preflight checks binary labels, accepted synthetic provenance, dataset hashes,
pinned exclusions, train/validation containing both classes, locked thread splits,
V1 SHA/threshold metadata and storage. UNCERTAIN/test-only/unlabeled/quarantined
inputs cannot train. Test rows never enter optimizer or model selection. There
is no arbitrary Python, pickle, model-path or output-path upload.

Worker executes an owned isolated child, offline/local-files-only, CPU thread
limit1–4, <=900 seconds, tokenizer parallelism disabled and Windows below-normal
priority. It permits one active run per Studio DB. Cancel affects only its child;
queued cancellation starts no process. Failed/crashed/unverified runs cannot
be COMPLETED. On worker crash, potential orphans are not retried; after >1020s
without heartbeat mark FAILED/WORKER_INTERRUPTED. The orphan also has a bounded
trainer deadline. Restart with the same root; do not create duplicate jobs to
hide a failure. There is no pause/resume promise or production resource SLO.

Metrics and bounded logs are polled with backoff. Completion requires actual
optimizer updates, unchanged encoder/base/source hashes, safetensors output,
real model reload scores within1e-5 and run manifest. Candidate/tokenizer/config/
environment/SHA files are separate under training_runs/{id}/candidate. No
MODEL_PATH, registry default, policy threshold or readiness lock is changed.

Verified run: reports/task_rollout_20261104/T041_run_manifest.json;
T041_retained.json locates the retained Studio root and candidate. The new
18-thread/36-comment hand-authored synthetic fixture is a workflow smoke, not a
benchmark. Locked counts: train22, validation10, test4. One epoch / 3 optimizer
steps,2CPUthreads; trainer elapsed3.36s; encoder/base/sources unchanged; reload
error0.0. Validation Macro-F1=1.0 on10 synthetic rows is only a tiny development
sanity check and supplies no independent real-world or release evidence.

T041_browser_result.json:6 Chrome checks including real training/reload/artifact
download and a Social message during training. The concurrent moderation side
used actual v5 rules with synthetic raw fixture, not a second neural model.
T041_backend_service_final.log covers permissions/config/preflight/idempotency,
queued/running cancel, worker restart/orphan handling and child crash.
