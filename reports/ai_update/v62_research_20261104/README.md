# Controlled v6.2 reproduction

No default/runtime activation. Latest report: `docs/ai-update/final-report/CONTROLLED_V62_RESEARCH.md`. Human preparation: **adjudication_v3/NOV10_ADJUDICATION.html** and cases_with_full_context.csv. V1/v2 are superseded export history; all owner decisions remain blank. V3 exports a fresh timestamped annotation version, never changes original reference.

From repository root:

```powershell
.\.venv\Scripts\python.exe -X utf8 -m pytest -q tests/test_research_v62.py tests/test_nov10_adjudication_export.py
.\.venv\Scripts\python.exe -X utf8 scripts/verify_ai_readiness_lock.py --lock reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json
.\.venv\Scripts\python.exe -X utf8 scripts/evaluate_research_v62.py --output reports/ai_update/v62_replay_new
```

The paired evaluator refuses existing directories and uses original cached model scores, no fresh training/inference. Original v6.1 quote probe2 reads old saved output; its historical failures remain. The migrated v6.2 tests preserve expectations and replay the original input through the new processor rather than rewriting historical output.

`V62_LOCK.json` freezes processor, frozen predecessors, tests, evaluator and model hash before authoring the new36comment challenge. `postfreeze_challenge/first_pass_metrics.json` is its only first-pass evaluation; `postfreeze_scores.json` holds actual offline r06 scores. Do not rerun author_challenge.py, evaluate_challenge.py, freeze.py or stabilize.py over completed versions. No post-score processor tuning.

`frozen_development/` is final paired development evidence; earlier phase1/phase3 directories preserve failed/intermediate work. `phase1_quote_source.py` is the quote-only snapshot, not an app entrypoint. `remaining_fp_fn.csv`, uncertain_reference_cases.csv and evidence_and_target_errors.json retain limitations.

Independent-evaluation leakage preflight must explicitly use the new versioned overlay (expected exit2 for excluded development input):

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/check_development_exclusions.py --manifest datasets/real_conversations/manifests/development_exclusions.research_v62_20261104.json --thread datasets/fixtures/nov10_regression_v1/inputs/TEST12_LUYEN_SPEAKING_IELTS.json
```

The sealed default exclusion manifest/loader is unchanged. No match never approves real-world independence.
