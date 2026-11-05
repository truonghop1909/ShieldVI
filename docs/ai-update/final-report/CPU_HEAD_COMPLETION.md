# Remaining tasks completed — bounded CPU head experiment and local review

## Outcome and scope

All27existing repository task files are DONE under their declared scope; the2remaining tasks T029/T031 were revised and executed, not marked complete from a plan. T029 trained a new **classifier head only**, with V1encoder frozen. T031 completed actual local shadow/fallback/rollback review and **rejected promotion**. FullencoderGPUfine-tuning and production deployment were not performed. Prior confirmed Social/AI DONE states remain unchanged; absentT001–T006 were not recreated.

The user request explicitly allowed running remaining tasks and revising blockers. The local authorization record quotes that request and binds config/preparedSHA with max4CPUthreads/900seconds/externalcost0. It explicitly does not claim manual approval of exact hyperparameters, GPU spending or production changes. Older GPU-only gates still apply to the old fullfine-tune config.

## Actual T029 training

- New checkpoint: `models/candidates/T029_genz500_head_cpu_20261103_r03/`; originalV1,approveddefaultV1.1 and previousV2 were preserved.
-11340trainrows=6942originalViCTSD+4398eligible AI synthetic;2000validationrows.500syntheticthreads and12newcontextfixtures/userreference remain unchanged. The12contextfixtures/userlabels are not added to training. AI labels are not human gold.
-Max3epochs,4CPUthreads,batch64,LR3e-5,syntheticlossweight0.5,baselineheadKLweight0.5,maxlength128,seed20261103. Physicalsyntheticfraction38.78%; source exact/near exclusions/heldout/development isolation recomputed by the existing preparation pipeline.
-Actual3epochs/534optimizersteps/400.94seconds.96,975,360encoderparameters frozen;592,130headparameters trainable. Only classifier.dense/out_proj weights/biases changed. Encoder SHA and base/source hashes unchanged; selectedepoch3 from validation only. Reloadprobeerror0.
-HistoricalViCTSDtest labels were opened only in evaluation after model selection; no second training/model selection followed test results. Threshold stays0.41 for every model.

[Config](../../../configs/t029_genz500_cpu_head.json) · [Authorization record](../../../reports/ai_update/all_tasks_cpu_20261103/cpu_authorization.json) · [Prepared data audit](../../../reports/ai_update/T029/genz500_cpu_prepared/manifest.json) · [Training report](../../../models/candidates/T029_genz500_head_cpu_20261103_r03/training_report.json).

## Validation and final test audit

| Dataset | Model | n | MacroF1 | ToxicP | ToxicR | TP/FP/TN/FN |
|---|---|---:|---:|---:|---:|---|
| ViCTSD_validation | original_V1 | 2000 | 0.763701 | 0.629442 | 0.534483 | 124/73/1695/108 |
| ViCTSD_validation | existing_default_V1_1 | 2000 | 0.760205 | 0.648352 | 0.508621 | 118/64/1704/114 |
| ViCTSD_validation | candidate_head_CPU | 2000 | 0.753042 | 0.613402 | 0.512931 | 119/75/1693/113 |
| ViCTSD_test_final_audit | original_V1 | 1000 | 0.738958 | 0.542056 | 0.527273 | 58/49/841/52 |
| ViCTSD_test_final_audit | existing_default_V1_1 | 1000 | 0.742036 | 0.552381 | 0.527273 | 58/47/843/52 |
| ViCTSD_test_final_audit | candidate_head_CPU | 1000 | 0.748633 | 0.543860 | 0.563636 | 62/52/838/48 |

Candidate validation MacroF1 falls0.763701→0.753042 vs originalV1 and is below existingdefault0.760205. Test MacroF1 rises0.738958→0.748633, but test gains do not override the frozen validation gate. This is a negative promotion decision, not an overall model improvement claim.

## Synthetic development diagnostics and losses

| Group | Model | Raw TP/FP/TN/FN | Advisory TP/FP/TN/FN |
|---|---|---|---|
| EXISTING_GENZ_DEVELOPMENT | original_V1 | 20/23/559/15 | 26/16/566/9 |
| EXISTING_GENZ_DEVELOPMENT | existing_default_V1_1 | 19/22/560/16 | 25/16/566/10 |
| EXISTING_GENZ_DEVELOPMENT | candidate_head_CPU | 24/18/564/11 | 28/13/569/7 |
| GAME_USER_REFERENCE | original_V1 | 4/5/21/0 | 4/0/26/0 |
| GAME_USER_REFERENCE | existing_default_V1_1 | 4/5/21/0 | 4/0/26/0 |
| GAME_USER_REFERENCE | candidate_head_CPU | 4/4/22/0 | 4/0/26/0 |
| NEW_SYNTHETIC_RECOVERY | original_V1 | 9/11/98/2 | 11/0/109/0 |
| NEW_SYNTHETIC_RECOVERY | existing_default_V1_1 | 9/10/99/2 | 11/0/109/0 |
| NEW_SYNTHETIC_RECOVERY | candidate_head_CPU | 10/8/101/1 | 11/0/109/0 |
| OTHER_FOUR_REGRESSION | original_V1 | 15/9/94/1 | 15/4/99/1 |
| OTHER_FOUR_REGRESSION | existing_default_V1_1 | 14/9/94/2 | 15/4/99/1 |
| OTHER_FOUR_REGRESSION | candidate_head_CPU | 15/5/98/1 | 16/2/101/0 |

GAME30 advisory labels and exactU02→U03 evidence[c08,c11,c15,c18] are preserved. Newcandidate creates1new GenZadvisoryfalsepositive relative to originalV1: `SGZ500_0242_C02`, “t ngồi thảm được, ghế chiếm chỗ quá”, rawscore0.447190. These labels are AI references, not independent human gold. Net synthetic gains do not hide this new loss.

## T031 decision, shadow and rollback

`REJECT_PROMOTION_KEEP_EXISTING_DEFAULT`: validation gates against originalV1 and existingV1.1 fail, and no-new-synthetic-error gate fails. Test gates and exactGAME checks pass. No threshold, labels or acceptance criteria were changed to get a positive verdict. Candidate remains unapproved for default selection; local shadow loading is explicit. Production activation remains outside this revised task.

-Actual baseline/candidate/default checkpoints loaded with artifactSHA checks; local shadow candidate loads; non-shadow selection is refused.
-Deliberate candidate-loader RuntimeError triggers V1 fallback using the already-loaded verified real V1. Rollback selects that V1; actual ASGI recovery503→200 verified. This is local in-process load/selection recovery, not a production service restart.
-Candidate legacy/V2 routes return200 with identical raw scores for the same model; authenticated Social contract1.0 returns200. No SocialDB or visibility/policy state changed. MODEL_PATH was changed only inside the isolated test process and restored; runtime default before/after matches.

[Local registry](../../../configs/model_registry.cpu_r03.local.json) · [Review and all gates](../../../reports/ai_update/all_tasks_cpu_20261103/candidate_evaluation.json) · [Prediction audit](../../../reports/ai_update/all_tasks_cpu_20261103/heldout_predictions.csv) · [Synthetic pairs](../../../reports/ai_update/all_tasks_cpu_20261103/synthetic_paired.csv).

## Evaluation method and reproducibility

A direct full-forward attempt was stopped during validation for runtime efficiency, before any test prediction metrics; its code/log/progress are preserved under direct_forward_attempt*. No model/config/gates were changed. Final evaluation verifies identical encoderSHA across all3models and tokenization equality every batch; one real encoder forward feeds each real classifier head. Per-model full-forward probes on each dataset agree within1.79e-7. No heldoutscore is within1e-5of0.41. This is real component inference with explicit reuse, not fabricated or copied model predictions. Test is a single final audit after selection; it is a historical holdout, not a fresh blind benchmark.

[Frozen protocol](../../../reports/ai_update/all_tasks_cpu_20261103/evaluation_protocol.json) · [Environment](../../../reports/ai_update/all_tasks_cpu_20261103/environment.json) · [Numerical check](../../../reports/ai_update/all_tasks_cpu_20261103/numerical_threshold_check.json).

## Verification and integrity

434root testsPASS/1knownStarlettewarning, including CPU resource/receipt guards, actual trained checkpoint invariants, frozen gates, API/context/legacy regressions and unapproved registry selection.25preflight checks are included/overlapping, not an additional25unique tests. Frontend/Socialsource/default deployment did not change in this run; earlier integration evidence remains historical. The current candidate adds actual-model local API/fallback/rollback verification.

31protected artifact hashes, original200threads/2CSV, GenZ500/exports/developmentlock,12contextfixtures/userreference, originalViCTSDvalidation/test and liveSQLite remain unchanged. FullGPU mode is still unexecuted; no externalpaidAPI,datasetdownload,checkpointoverwrite,DBreset,push,auto-hide or productiondeploy.

[434test log](../../../reports/ai_update/all_tasks_cpu_20261103/root_tests.txt) · [Integrity audit](../../../reports/ai_update/all_tasks_cpu_20261103/integrity_audit.json) · [Current progress](../../../reports/ai_update/all_tasks_cpu_20261103/progress.json).

## Safe continuation

Use the existing demo/default. The new checkpoint is a rejected-for-promotion research artifact; do not replace the active model with it. CLI source is scripts/train_t029_candidate.py plus scripts/t029_cpu_head.py, configured by t029_genz500_cpu_head.json. A default call is preflight, not training; the existing output refuses overwrite. scripts/evaluate_cpu_candidate.py preserves completed audit output. Optional fullGPU notebook stays unexecuted and needs a separately approved resource/config; it does not inherit this CPU authorization. No remaining task is started automatically after this handoff.
