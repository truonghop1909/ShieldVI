# Completed r06 experiment — reproduction and evidence

Start at repository root with the existing .venv. No dataset/model download or paid API is required for the completed local experiment. Dataset: datasets/synthetic_genz (500 reused JSONs, unchanged synthetic references). Full comparison/error analysis: [report](../../../docs/ai-update/final-report/SYNTHETIC_R06_EXPERIMENT.md). Checkpoint: models/candidates/T029_synthetic_only_head_cpu_20261103_r06; never activated.

## Safe revalidation

```powershell
.\.venv\Scripts\python.exe -X utf8 -c "import sys;sys.path.insert(0,'scripts');from synthetic_data.experiment import verify_view; m,t,q=verify_view('datasets/synthetic_genz');print(m['threads'],m['comments'],q['status'])"
.\.venv\Scripts\python.exe -m pytest -q tests/test_synthetic_experiment.py
```

Use a fresh --basetemp under reports/ai_update/test_tmp if Windows temporary-directory permissions require it. final_tests.log records actual full root591PASS/0FAIL. Training_execution.json records actual207optimizersteps/79.75seconds. evaluation/ contains saved same-input three-model predictions, metrics, hybrid outputs, errors and paired wins/losses. teencode_reporting_v2.json only recomputes the corrected slice mask from saved predictions, never model inference. Integrity audit is integrity.json; output checksums are ARTIFACTS.json.

## Dataset resume

scripts/synthetic_data/experiment.py export_dataset uses the existing canonical export, not a template text generator. It validates complete canonical content first, processes pilot20/batches50/final30, writes checkpoints and resumes only identical existing files. A completed export is revalidated, never silently replaced. Its original source style/content limitations still apply. Do not run prepare_run.py again: it is the initial exact-request/config/data authorization orchestration, refuses an existing run, and the one-run authorization is now consumed.

## Training/evaluation provenance

The actual command was scripts/train_t029_candidate.py --config configs/t029_synthetic_only_cpu_r06.json --prepared reports/ai_update/synthetic_experiment_r06_20261103/prepared --base-model <original-local-V1-directory> --approval reports/ai_update/synthetic_experiment_r06_20261103/cpu_authorization.json --run --report reports/ai_update/synthetic_experiment_r06_20261103/training_execution.json, executed using the repo Python. Protocol/config/data hashes were fixed before training. Existing candidate output and consumed scope block reruns. No production registry changes were made.

The comparison was scripts/evaluate_synthetic_candidate.py --config configs/t029_synthetic_only_cpu_r06.json --prepared reports/ai_update/synthetic_experiment_r06_20261103/prepared --output reports/ai_update/synthetic_experiment_r06_20261103/evaluation. Use the saved results for review; repeating research inference does not produce independent evidence and must never be used to tune against challenge labels.

For a genuinely new authorized experiment choose new run ID, output directory, config, prepared manifest and matching resource receipt. Never overwrite r06 or reuse its one-run receipt. Full encoder GPU fine-tune is only prepared in notebooks/T029_Synthetic_Experimental_R06.ipynb (unexecuted, approval false by default). No implicit API/upload/download/mount occurs. GPU approval must match actual resource/config; changing a notebook boolean alone does not grant it. Optimizer-state resume is not implemented; incomplete training is not a completed model.

T028 real200 remains BLOCKED; no real/human-gold metrics, no release/promotion approval. Original V1, threshold0.41, canonical datasets/test split and SQLite remain unchanged.
