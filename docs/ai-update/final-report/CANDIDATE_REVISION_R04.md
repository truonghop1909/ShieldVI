# Rework after candidate rejection — r04

## Scope and decision

The previous task review completed, but r03 promotion was rejected. This follow-up revises the research recipe, not the acceptance gates or labels. The renewed user request authorizes continued local work; one bounded CPU classifier-head experiment was actually executed. Full encoder, paid GPU and production activation remain outside this execution.

**Decision: REJECT_PROMOTION_KEEP_EXISTING_DEFAULT.** Promotion remains disabled even if validation screening passes. Historical test was already inspected in r03; it was not rescored here. This is exploratory validation reuse, not new blind evidence.

## Executed changes

- Lower synthetic sample weight0.5→0.1; lower learning rate3e-5→1e-5; increase original-head distillation0.5→1.0. No example-specific rule or annotation change.
- Preserve11340trainingrows (6942ViCTSD+4398AI references) and2000validationrows. Weighted synthetic share of supervised loss is approximately24%→6%; physical data share stays38.78%. AI labels remain synthetic references.
- Actual 356optimizersteps, 2epochs, 431.84seconds; max4CPUthreads/900seconds/cost0. Encoder unchanged, reload probe error 0.0. Selected epoch 1 by validation only.
- Added reusable validation-only screening with both baseline comparisons, integrity checks, output overwrite refusal and no promotion permission. Corrected two stale REAL200/BLOCKED document banners while retaining their historical text.

## Validation only — fixed threshold0.41

| Model | MacroF1 | Toxic precision | Toxic recall | TP/FP/TN/FN |
|---|---:|---:|---:|---|
| original_V1 | 0.763701 | 0.629442 | 0.534483 | 124/73/1695/108 |
| existing_default_V1_1 | 0.760205 | 0.648352 | 0.508621 | 118/64/1704/114 |
| r03_prior_candidate | 0.753042 | 0.613402 | 0.512931 | 119/75/1693/113 |
| r04_candidate | 0.756865 | 0.613065 | 0.525862 | 122/77/1691/110 |

Unchanged screen: MacroF1 must improve by≥0.005 and toxic precision/recall must not fall, against both originalV1 and defaultV1.1. The existing no-new-synthetic-error gate is also retained; it was not reassessed for this recipe. Test/regression inference, API shadow and production rollout were not performed for r04. The prior r03 local smoke remains historical evidence, not r04 evidence.

## Verification and files

- Full root regression: **448passed**, one known Starlette deprecation warning. Preflight40passed; initial sandbox temp-directory write failed, elevated rerun succeeded. No automatic approval rejection remained.
- Integrity:31protectedhashes;200legacy+500GenZthreads, frozen development split,12contextthreads/userreference, original validation/test/checkpoints/default/SQLite unchanged. No train on test or new uploads/downloads.
- Source: [validation reviewer](../../../scripts/review_t029_validation.py), [tests](../../../tests/test_t029_validation_review.py), [r04 config](../../../configs/t029_genz500_cpu_head_r04.json).
- Evidence: [predeclared protocol](../../../reports/ai_update/candidate_revision_20261103/predeclared_experiment.json), [training report](../../../models/candidates/T029_genz500_head_cpu_20261103_r04/training_report.json), [validation review](../../../reports/ai_update/candidate_revision_20261103/validation_review.json), [integrity audit](../../../reports/ai_update/candidate_revision_20261103/integrity_audit.json).
- Tracking: T029/T031 task files, TASK_ORDER_AI.md, TASK_ORDER.md and AUTO_PROGRESS.md updated with follow-up evidence. The27previously completed task states remain preserved.

## Next action

Stop this recipe; retain default and negative result. Do not relax gates or rescore test.
A quality failure is not resolved by rewriting release gates. Keep the approved default for the demo. Additional model research requires a separately declared experiment; paid/full-encoder GPU work and production activation require their existing approval.
