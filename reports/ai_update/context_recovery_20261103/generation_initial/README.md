# Context recovery development dataset

12 newly AI-authored synthetic threads /120comments (3–4speakers,10comments each), authored and frozen before rules were edited. New text in scripts/synthetic_data/context_recovery_catalogue.txt. Labels are AI references, not human gold, and training_eligible=false because these are rule-development examples. No real dataset/contact/collector/manual labeling required.

GAME input is the unchanged existing fixture referenced by game_rank_30_reference.json; all30labels are the user-provided correction, reference-only/not independent human gold. ExpectedTOXIC only c08,c11,c15,c18; remaining26CLEAN. Original fixtures/test/GenZ500 are not overwritten.

Paired cases cover intervention, apology, responsibility, victim feelings, quoted/endorsed abuse, threats and new attacks after apology/acknowledgment separated by comma/period/contrast. Do not alter labels to pass a rule test. See reports/ai_update/context_recovery_20261103 for before/after and regressions.
