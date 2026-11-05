# NOV10 audit reproduction

Report: `docs/ai-update/final-report/NOV10_ROOT_CAUSE_AUDIT.md` from root. No processor/model/default changes. Audit result is not a coverage fix: NOV10 target0/22,repeated0/8 remain. Separate challenge found an open quote/assignment bug, two red diagnostic probes retained.

From repository root:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/audit_nov10.py
.\.venv\Scripts\python.exe -X utf8 -m pytest -q tests/test_nov10_audit.py tests/test_development_exclusion_overlay.py tests/test_fresh10_recovery.py
.\.venv\Scripts\python.exe -X utf8 -m pytest -q reports/ai_update/nov10_audit_20261104/quote_scope_red_tests.py
.\.venv\Scripts\python.exe -X utf8 scripts/verify_ai_readiness_lock.py --lock reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json
```

The quote probe command deliberately currently exits1: two correct expectations FAIL, one control PASS. Root default testpaths=tests excludes evidence-directory probes; 677rootPASS must be reported alongside these two failures, not as all acceptance passed. No xfail or reference edits.

Exclusion check (expected exit2, EXCLUDED_DEVELOPMENT):

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/check_development_exclusions.py --manifest datasets/real_conversations/manifests/development_exclusions.research_20261104.json --thread datasets/fixtures/nov10_regression_v1/inputs/TEST12_LUYEN_SPEAKING_IELTS.json
```

Frozen default exclusion manifest/loader is unchanged. Future independent evaluation must use the versioned overlay preflight. Absence of a match is not approval of independence.

Inspect `comment_traces.json` for all200 predicate/gate traces, `event_audit.json` for eight timelines, `runtime_probe.json` for actual ASGI/r06 call counts/weights/source hashes, `metrics.json` for recomputed before=export/after=unchanged replay. `forced_target_diagnostic.json` is an oracle-only isolation experiment, never model metrics. `adjudication_candidates.csv` keeps24review candidates and blank reviewer decisions.

`old_regression/` holds new cached replay compared with previous v6.1 metrics; scores are r06 exports forFresh10 and V1 historical cache forold890. `new_challenge/` is first r06 scoring after `challenge_lock.json`, original labels unchanged. Its evaluator before column means v5 and after means v6.1, not a patch made by this audit. Do not rescore/tune the locked challenge or rerun authoring/import/exclusion preparation over existing versions.

`probe_actual_runtime.py` re-runs actual offline r06 CPU inference and process-local instrumentation in canonical ASGI; it does not start or modify live demo/production. Re-running is unnecessary for reading the saved evidence.
