# Fresh10 — verified causes before experimental changes

Imported source/reference CSVs and all10analysis exports are byte-preserved in datasets/fixtures/fresh10_regression_v1. Scores are user-exported r06 values; current frozenv5 replays the200outputs exactly after JSON tuple/list normalization. No fresh model inference claimed. Baseline final TP15/FP6/FN7/TN167,MacroF1.830105; raw.803968; target5/22,repeated2/7. Synthetic development only, not human gold/independent real evaluation.

## Test09 c17

Text: “Nhưng t xin lỗi không có nghĩa b hát hay đâu, cái kiểu lên sân khấu phông bạt vẫn cringe lắm.” Raw.798809 isTOXIC. DEFENSE matches only normalized[16,30)="khong co nghia", a causal connector, not evidence of victim self-defense. APOLOGY does not match because its sentence-start grammar does not accept initial “Nhưng t”. No bounded attack vocabulary matches phông_bạt/cringe here; unresolved_new_clause also fails on initial teencode t. non_attack_context_confirmed=True then context_assessment.assess choosesCLEAN. Target/instance vanish before repeated grouping. Reply is to U02's own apologyc15; legacy recipient U01 is not the attack target and must never be reused as such.

## Test10 c14

Text: “Quá tuyệt, t đổi bạn ít hạt ngò nha.” Raw.011560 isCLEAN. NFC/accent folding turns ngò into ngo, matching ATTACK normalized[28,31). DIRECT matches the addressed word ban. Context creates attack span[0,35), then infer_target returns addressed_reply,U05,medium,evidence[c14,c13], so assessment becomesTOXIC. This is lexical ambiguity introduced before target inference, not proof of an actual interpersonal attack.

## Proposed scope

Keep immutablev5/checkpoints/default/readiness files untouched. Implement an opt-in research processor under app/experiments, called only by offline evaluation/tests. Reuse v5 outputs/raw/legacy fields. Preserve accented plant meanings; do not whitelist a whole sentence/thread. Remove bare causal connectors as defense evidence; protect apology/defense/quotes per clause while retaining new attacks. Add bounded conduct/humiliation predicates and evidence-backed addressee resolution, not raw-score-only attack instances. Keep actor-target grouping separate and report evidence coverage as well as correctness.

Before extending indirect rules, flag Test01c15 and Test06c07/c15 as annotation-review candidates: sarcasm, team accountability and legitimate coaching can overlap. Existing expected labels stay fixed; no relabeling/exclusion to raise metrics. UNCERTAIN5 remain excluded only from binary metrics and separately counted. Do not make all sarcasm/criticism/ra_oai/profanity automaticallyTOXIC. New post-fix challenge will be authored only after experimental code freeze, scored once and never used to tune this revision.
