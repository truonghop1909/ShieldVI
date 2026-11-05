# Fresh10 recovery evidence

Opt-in offline v6.1 experiment. Live API/Dashboard remains sealed v5; no model activation. References are synthetic development, never human gold. Full analysis and limitations: `docs/ai-update/final-report/FRESH10_RECOVERY.md` from repository root.

Evidence order: ROOT_CAUSE.md → red_priority_tests.log → development_v1/v2 → experiment_lock.json → postfix_holdout_metrics.json → quote_scope_red_tests.log → development_v3 → experiment_lock_v2.json → final_challenge/metrics.json → full_tests.log → integrity.json. Original v6 snapshot is experimental_sources/v6_initial.py. First 48-comment challenge became development after its new FP was found; its original first-pass results are retained.

From repository root, using existing local environment:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest -q tests/test_fresh10_recovery.py
.\.venv\Scripts\python.exe -X utf8 scripts/verify_ai_readiness_lock.py --lock reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json
.\.venv\Scripts\python.exe -X utf8 scripts/evaluate_fresh10_recovery.py --output reports/ai_update/fresh10_recovery_replay_new
```

The evaluator refuses existing output directories. It reuses imported actual scores; it does not train/re-infer the original Fresh10. To replay the final challenge without another neural forward, use its captured scores and a new output path:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/evaluate_fresh10_challenge.py --dataset datasets/fixtures/fresh10_postfix_holdout_v2 --scores reports/ai_update/fresh10_recovery_20261103/final_scores.json --output reports/ai_update/fresh10_challenge_replay_new --lock reports/ai_update/fresh10_recovery_20261103/experiment_lock_v2.json
```

Do not rerun source-authoring/import helpers or overwrite historical evidence. Missing score cache triggers actual offline r06 CPU inference (four threads), not training. No frontend build required; UI unchanged. Root suite log: 648 PASS, one Starlette deprecation warning. Prior Social177/browser evidence is preserved, not a new run.

`T028_EXCLUSION_EXTENSION.json` is a pending extension for the next evaluation-lock revision, not an edit to the existing readiness-frozen runtime exclusion list. New fixture paths must be included before a future independent evaluation.
