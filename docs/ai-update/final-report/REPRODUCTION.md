# Reproduction and safe local demo

Run PowerShell at repository root. Use existing virtualenvs; no package/model/data download is needed for verified commands. All commands below are local. They do not start GPU training.

## Dataset and preparation

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/generate_genz_dataset.py --through 500
.\.venv\Scripts\python.exe -X utf8 scripts/prepare_t029_training.py --config configs/t029_genz500_candidate.json --output reports/ai_update/T029/genz500_prepared --base-model C:/Users/admin/Downloads/visobert_toxic_final
.\.venv\Scripts\python.exe -X utf8 scripts/train_t029_candidate.py --config configs/t029_genz500_candidate.json --prepared reports/ai_update/T029/genz500_prepared --base-model C:/Users/admin/Downloads/visobert_toxic_final --report reports/ai_update/T029/genz500_preflight.json
```

Last command is preflight only and returns BLOCKED (CUDA/G3). Do not add `--run` or fake a receipt. The existing Colab notebook is now prepared for configs/t029_genz500_candidate.json and scratch /content/t029_genz500_prepared, and remains unexecuted. Review the exact resource/cost receipt before any train cell. G2-S permits research while REAL remains blocked, not an external-cost approval.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --basetemp reports/ai_update/test_tmp/next_root_run
Push-Location services/social-api
$env:PYTHONPATH='src'
.\.venv\Scripts\python.exe -m pytest tests -q -p no:cacheprovider --basetemp ../../reports/ai_update/test_tmp/next_social_run
Pop-Location
$env:PYTHONPATH=(Join-Path (Get-Location) 'services/social-api/src')
.\services\social-api\.venv\Scripts\python.exe -X utf8 scripts/run_ai_update_e2e.py
```

Use a fresh basetemp for each rerun. E2E automatically creates isolated SQLite/testaccounts and stops only owned processes; no live database is reset. Its AI scores are fixtures. Do not add fixture users to your existing DB. Frontend builds: `npm.cmd run build -- --outDir <new-absolute-report-directory>` from each app, including moderation-web/legacy-v3. Outputs in this session are under reports/ai_update/autonomous_20261103/build_*.

## Real model experiment

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/evaluate_genz_development.py --base-model C:/Users/admin/Downloads/visobert_toxic_final --output reports/ai_update/T030/new_untuned_rerun
.\.venv\Scripts\python.exe -X utf8 reports/ai_update/autonomous_20261103/registry_smoke.py
```

Evaluation refuses overwriting completed results, checks frozen data hashes and loads V1 offline. Reruns do not turn synthetic development into independent validation. Registry smoke deliberately faults the primary loader, actually loads V1 on fallback and compares V1 with itself to test mechanics; there is no candidate accuracy comparison.

## Five AI demos

In a separate PowerShell window, set MODEL_PATH to the desired existing local checkpoint for that process. To reproduce this report use original V1; the normal approved default is V1.1. Keep STORE_SUMMARIES=0 for this demonstration.

```powershell
$env:MODEL_PATH='C:/Users/admin/Downloads/visobert_toxic_final'
$env:STORE_SUMMARIES='0'
$env:HF_HUB_OFFLINE='1'
.\.venv\Scripts\python.exe -m uvicorn app.main:app --app-dir services/moderation-ai --host 127.0.0.1 --port 8020 --no-proxy-headers
```

Open http://127.0.0.1:8020/docs and use POST/api/v2/analyze. If Dashboard is served, open /dashboard/ and choose an API-clean JSON from dashboard_threads; this is the AI Dashboard, not the optional labeling reviewer on8011 (which still shows the original200). Annotated JSON is for reading and is not the API upload shape. On the Dashboard verify the requested V2 endpoint; Swagger V2 is the authoritative signal view if a legacy UI does not render all V2 fields. Never expect keyword presence to force a TOXIC result.

| JSON file | What to inspect |
|---|---|
| [dashboard_threads/SGZ500_0205.json](../../../datasets/synthetic_conversations/genz_v2/dashboard_threads/SGZ500_0205.json) | repeated attack with earlier actor/target evidence |
| [dashboard_threads/SGZ500_0209.json](../../../datasets/synthetic_conversations/genz_v2/dashboard_threads/SGZ500_0209.json) | attacker apology after earlier attack |
| [dashboard_threads/SGZ500_0211.json](../../../datasets/synthetic_conversations/genz_v2/dashboard_threads/SGZ500_0211.json) | quotation must not become a new attack solely from words |
| [dashboard_threads/SGZ500_0203.json](../../../datasets/synthetic_conversations/genz_v2/dashboard_threads/SGZ500_0203.json) | profanity as non-directed exclamation |
| [dashboard_threads/SGZ500_0207.json](../../../datasets/synthetic_conversations/genz_v2/dashboard_threads/SGZ500_0207.json) | indirect non-profane attack |

Record raw0.41prediction separately from lexical/context/target/repeated signals. Missing targets/repeated warnings are observable limitations, not a reason to alter the example. Synthetic AI labels are references; no human gold claim. The automatic E2E separately demonstrates admin review/appeal/retry on fresh synthetic accounts, without making the AI responsible for visibility or enabling HIGH auto-hide.

## Historical B0–B3 replay

`python scripts/evaluate_regression_ablation.py` produced reports/ai_update/T030/regression_ablation and refuses overwriting a completed experiment. It verifies original fixture/weight hashes and that engine.py is byte-identical to T020 before isolating lexical changes. B0uses cached real inference; B2injects original per-input lexical outputs only within that offline process. View existing outputs for reproduction; use a new output version in a future code revision to rerun, never delete completed evidence. It cannot reconstruct the old detector for new texts.
