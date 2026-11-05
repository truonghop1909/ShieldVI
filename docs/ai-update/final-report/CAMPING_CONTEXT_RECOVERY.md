# Camping30 — context, target and repeated evidence recovery

## Result

The pasted30comments exactly match the existing camping fixture. Labels remain the existing synthetic reference projection, not user-confirmed human gold. Before: c09advisoryCLEAN, onlyc12/c15/c18advisoryTOXIC, no grounded attack/repeated evidence in either actual V1.1 or r05 demo. After: all30reference labels match and the exact U04→U03 chain is c09/c12/c15/c18; apology, recovery and acceptance do not become new attacks.

## Causes and general changes

- context-v2 lacked bounded disparagement constructions for personal incompetence/team burden. context-v3 checks such constructions together with an addressee or a local abuse-justifying clause; ordinary work criticism, negation, quoted reporting and new attacks after apology remain separate tests.
- c18matched a broad passive-abuse defense cue. Clause-level endorsement of abuse now establishes an attack candidate and removes the contradictory DEFENSE tag. A quoted/past apology for that same language remains non-attack.
- Existing target-v3 can ground c09/c12/c15from addressed replies, then continue the same grounded target at c18. The target module itself was not changed. Replies stay separate from directed attack targets; no parent/mention means no invented target.
- repeated-v4uses qualified clause evidence plus a medium/high-confidence target, rather than requiring raw>=0.41. Raw toxicity_score/toxic_for_moderation/toxic_for_repeated_rule and all legacy fields stay unchanged. attack_instance_basis is additive in V2; policy remains advisory/unexecuted.
- Can-ngan/boundary/self-responsibility cues now cover the missing discourse constructions. APOLOGY_ACCEPTANCE distinguishes receiving another person’s apology from ACKNOWLEDGEMENT of one’s own fault. Dashboard has the Vietnamese label “Chấp nhận xin lỗi”.

## Actual local inference, before versus after

| Demo | c09raw (unchanged) | Advisory before→after | Repeated before→after |
|---|---:|---|---|
| 8020 | 40.339% | CLEAN→TOXIC | none→U04→U03:c09/c12/c15/c18 |
| 8021 | 40.629% | CLEAN→TOXIC | none→U04→U03:c09/c12/c15/c18 |

Both actual APIs: health/model_loaded ready, legacy/V2 analysis200, Dashboard200 and new bundled UI served. Every one of the30 raw scores and legacy recipient fields matches before and the unchanged legacy API. This is actual model inference, not a constant-score test. Demo8020stilluses approvedV1.1;8021is the rejected-for-promotion experimentalr05. No model was retrained or promoted.

## Broader paired regression

Same890comments and same frozen original-V1 CPU score cache before/after. One improved advisory decision (campingc09), zero new label errors/abstentions, one changed event (camping now has4correct reference attack turns), no newly added evidence carrying a CLEAN reference. The original GAME exact4attack-chain tests remain passing. These are previously viewed synthetic development references, not a blind benchmark.

| Group | Known reference comments | Before TP/FP/TN/FN | After TP/FP/TN/FN | After abstentions |
|---|---:|---|---|---:|
| EXISTING_GENZ_DEVELOPMENT | 617 | 26/16/566/9 | 26/16/566/9 | 0 |
| GAME_USER_REFERENCE | 30 | 4/0/26/0 | 4/0/26/0 | 0 |
| NEW_SYNTHETIC_RECOVERY | 120 | 11/0/109/0 | 11/0/109/0 | 0 |
| OTHER_FOUR_REGRESSION | 119 | 15/4/99/1 | 16/4/99/0 | 0 |

Remaining errors in these groups are retained in the table and paired output; zero *new* errors does not mean all development cases are correct. Target/repeated reference checks do not establish real-world harassment accuracy.

## Verification

- New regression beforefix:18failed/73passed. Focused context/target/repeated suite196passed before the additional schema compatibility test. Final full root suite:540passed/1knownStarlettewarning.
- npm local buildPASS; old hashed assets kept for open tabs and prior index backed up. The first restart attempt stopped at a PowerShell nested-array ownership query before any file/process mutation; corrected array reading, verified exact owned PID/parent/repo/port, then restarted only these2demo processes.
-31protected originals + V1/V1.1/r03/r04/r05,200legacy/500GenZ, frozen splits/user references, original validation/test/SQLite unchanged. Raw engine, lexical module/signals and target module unchanged. No training, downloads, production deploy or auto-hide.

## Evidence and resume

- [Regression tests](../../../tests/test_camping_context_regression.py) · [Frozen synthetic reference](../../../tests/fixtures/ai_update/camping_reference.json) · [V2 schema](../../../contracts/analysis_response_v2.schema.json).
- [Paired report](../../../reports/ai_update/camping_context_20261103/before_after.json) · [Actual live checks](../../../reports/ai_update/camping_context_20261103/live_smoke.json) · [Integrity](../../../reports/ai_update/camping_context_20261103/integrity_audit.json).
- [Server state and owned PIDs](../../../reports/ai_update/camping_context_20261103/demo_after_server_state.json) · [Progress](../../../tasks/AUTO_PROGRESS.md).
- Demo http://127.0.0.1:8020/dashboard/ and experimental http://127.0.0.1:8021/dashboard/. Refresh Ctrl+F5 and analyze again; old results already displayed in a tab are not recomputed automatically.
