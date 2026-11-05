# Error analysis — synthetic development, not real gold

Frozen60threads/620comments. All reference labels are AI-authored. No examples, labels, rules, model or threshold were changed to improve these results. Terminology in output keys was clarified from gold to reference after evaluation; numeric values stayed identical.

## Full counts

Raw23FP: {'defense': 4, 'intervention': 8, 'apology': 2, 'normal': 6, 'criticism': 2, 'quote': 1}

Raw15FN: {'indirect_attack': 6, 'mixed_apology_attack': 3, 'threat': 3, 'directed_insult': 3}

Hybrid target11correct emissions/35attacks;24abstentions. Context attack candidate13TP/2FP/22FN (see metrics); target grounding must be evaluated separately from toxicity. Repeated event recall fell from legacy diagnostic2/7 to Hybrid0/7, while false events fell2→0. Precision for zero emitted events is undefined. This does not meet an improvement claim.

## Deterministic illustrations

First3FP and first3FN in frozen ID order are illustrations; every error remains in the full artifacts.

- FP SGZ500_0217_C01 (defense), score=0.4473: Mình đã nói không muốn bị tag vào bài chê nhóm khác nữa.
- FP SGZ500_0217_C04 (defense), score=0.4446: Mình không tham gia công kích không có nghĩa phải nhận lời xúc phạm.
- FP SGZ500_0218_C04 (intervention), score=0.7664: Góp ý mốc thời gian được, đừng gọi tác giả ngu.
- FN SGZ500_0205_C07 (indirect_attack), score=0.1104: Đầu mày chắc chỉ đủ để đội cái nón thôi.
- FN SGZ500_0218_C06 (indirect_attack), score=0.2994: Chắc người nghe phải có lòng thương lớn lắm mới nghe hết giọng mày.
- FN SGZ500_0219_C02 (mixed_apology_attack), score=0.3793: Xin lỗi đã không hỏi, nhưng mày vô dụng nên giữ phần đó cũng thừa.

## Reproduction and limits

[All paired predictions](../../../reports/ai_update/T030/genz500/paired_predictions.csv), [all hybrid outputs](../../../reports/ai_update/T030/genz500/hybrid_outputs.jsonl), [error union](../../../reports/ai_update/T030/genz500/errors.json), [metrics](../../../reports/ai_update/T030/genz500/metrics.json), [per-scenario raw counts](../../../reports/ai_update/T030/genz500/paired_by_scenario.json). The error union includes target/context errors beyond raw FP/FN; it must not be counted as classifier errors alone.

The high raw accuracy mainly reflects CLEAN prevalence. A precision1.0target value over only11 emitted predictions coexists with low coverage; no repeated evidence means no supported correctness estimate. Missing attacks can arise from context detection, target grounding or the conservative raw-score qualification. These observations are hypotheses for separate future development, not proof that fine-tuning fixes them.

## Separate baseline replay supplement

The original T020 captures were found after the first scoped lookup. `regression_ablation` records B0–B3 on the exact5old fixtures, using cached real V1 scores and original lexical detection outputs for B2. Raw149known predictions stay identical;26old evidence comments include7not tagged DIRECTED_INSULT, versus7B3evidence comments all tagged DIRECTED_INSULT. No target/event gold exists there; no target precision or event recall is manufactured. These150previously used examples are separate from the60-thread challenge, whose0/7repeated result is unchanged. Do not report old-regression tag support as proof of new-domain improvement.
