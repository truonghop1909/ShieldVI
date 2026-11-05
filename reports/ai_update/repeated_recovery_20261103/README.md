# Completed repeated recovery v5 — safe reproduction

Report: [REPEATED_RECOVERY_V5.md](../../../docs/ai-update/final-report/REPEATED_RECOVERY_V5.md). Current acceptance: tasks/CURRENT_AI_SCOPE.json. T028real/T029formalBLOCKED; T030–T033PARTIAL, safe development/local mechanics verified. No r07/training/production changes.

## Commands actually executed (repository root)

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp reports/ai_update/test_tmp/repeated_final_utf8
```

610rootPASS; use a new unique --basetemp for a rerun. The original red five-event test results are red_tests.log; final root log root_tests_verified.log. tests/test_repeated_recovery.py freezes the five original reference events and negative controls; test_repeated_evaluation_artifacts.py checks locked labels/populations/evidence accounting, not a forced performance target.

Social suite was run from services/social-api with its own .venv/Scripts/python.exe -m pytest -q --basetemp ../../reports/ai_update/test_tmp/repeated_social_own (177PASS). The rootvenv lacks Alembic, so do not use it for Social. No packages installed. Services/DBs in five-process browser E2E are temporary/owned; runner run_e2e.py reused the existing run_fullstack with isolated artifact and temp paths, invoked using services/social-api/.venv/Scripts/python.exe. Browser1PASS,2retry attempts,1resolved synthetic appeal, cleanup/privacyPASS; AI is a fixture there. Actual r06/V1 model API shadow/rollback is separately registry_smoke.json.

## Immutable experiment evidence

before_sources/ contains exact v4source snapshots, before_lock.json binds archived r06 outputs. five_events_before.json records root causes. frozen_rule_lock.json was written before fresh challenge authoring; fresh_audit.json checks no later rule edits and exact/near overlap0. datasets/fixtures/repeated_holdout_20261103 has12new scenes, never training/human gold. Canonical500 and r06 model/splits remain unchanged.

Actual comparison command: .venv/Scripts/python.exe -X utf8 scripts/evaluate_repeated_recovery.py --output reports/ai_update/repeated_recovery_20261103/evaluation. The evaluator refuses a completed output, uses actual three-model fresh scores once, and immutable r06 score cache for old620comments. Do not repeat inference to tune against this now-seen challenge. evaluation/evaluation.json stores raw metrics, matrices and before/context-only/target-repeated-only/after ablation; outputs.json retains separate raw/context/lexicon/target/policy/advisory fields. fresh_scores.json records actual model SHAs. error_analysis.json includes remaining errors and pairs. Full890cached replay is development_verified/metrics.json (no new model inference).

registry_smoke.py created configs/model_registry.repeated_recovery.local.json only, with candidate_r06 unapproved; actual load/fallback/isolated API200→503→200 succeeded. It refuses overwriting that registry; do not rerun it or change default to replay evidence. No running server was reconfigured. Current checkpoints and threshold0.41 are unchanged.

Historical summaries overcounted a target/event relative to coverage; archived/recomputed validated baseline33/54targets and2/10events is used, DANCE emission excluded because no target reference exists. Synthetic metrics never substitute for T028. See integrity.json/ARTIFACTS.json for protected artifacts and final file hashes. No Git metadata exists.

Next work requires a fresh predeclared holdout for new rule tuning, or permitted real sources and same-human two-round review for independent acceptance. No automatic new training, model switch, auto-hide or deploy.
