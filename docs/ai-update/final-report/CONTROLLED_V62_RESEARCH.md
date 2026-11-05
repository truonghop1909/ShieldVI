# Controlled Context/Target v6.2 — 04/11/2026

Đã hoàn thành vòng nghiên cứu có kiểm soát theo năm pha. **V6.2 vẫn experimental, không đổi Dashboard/runtime mặc định, v6.1, checkpoint hoặc readiness lock.** Chưa có adjudication của người dùng; mọi performance dưới đây dùng synthetic reference.

## 1. Quote scope: red trước, green sau

Processor mới: `services/moderation-ai/app/experiments/research_v62.py`. Không sửa module v6.1 đã khóa, không monkeypatch global. Orchestrator dùng canonical raw/lexicon engine một lần, rồi tính context/target/instances/repeated riêng. Output ghi rõ `research_only=true`.

Hai kỳ vọng lỗi gốc được chuyển sang test v6.2 với cùng input/assertion. Stub v6.2 delegate v6.1 trước sửa: **2 FAIL**, [quote_red.log](../../../reports/ai_update/v62_research_20261104/quote_red.log). Sau sửa: **hai kỳ vọng PASS**, nằm trong43processor tests. Probe lịch sử thứ hai vốn đọc JSON v6.1 đã lưu; không sửa JSON đó để làm PASS. Test mới replay cùng input/cache qua v6.2. V6.1/probes lịch sử vẫn thể hiện lỗi cũ, được giữ như baseline.

Sửa kỹ thuật:

- Assignment phải nằm **trước dấu mở quote**, không lấy “mày…là” bên trong lời nhân vật làm assignment của người bình luận.
- Phân biệt attribution/reporting, negation, can ngăn và endorsement ngoài quote. Direct assignment “cậu là ‘đồ ngu’” vẫn là attack; kể lại lời đó hoặc xin lỗi thì không có attack mới.
- Predicate ở clause ngoài quote được xét riêng: trích dẫn rồi tiếp tục hạ nhục vẫn giữ attack mới. Không whitelist dấu ngoặc kép.
- Danh từ có dấu **câu** không làm addressee **cậu**; vẫn giữ semantics can ngăn/tự vệ của “câu này xúc phạm”. Tránh mất hai safe cues mà bản mask đầu tiên đã gây ra.
- Content-view giữ nghĩa “máy lặp lại”, “bản dịch”; addressee-view mask homograph. Trace chỉ rõ view, normalized spans end-exclusive và mapping về NFC. NFD input được chuẩn hóa; không nhầm span normalized với offset byte/NFD gốc.

Quote-only snapshot lưu `phase1_quote_source.py`; paired regression quote-only không thêm lỗi nhãn trên bảy cohort. NOVaudit24 trước đó có FP quote được sửa, Macro-F1 .946387→1.0; đây là development đã xem, không phải challenge mới độc lập.

## 2. Chuẩn bị human adjudication

Mở **[NOV10_ADJUDICATION.html](../../../reports/ai_update/v62_research_20261104/adjudication_v3/NOV10_ADJUDICATION.html)** hoặc [CSV đầy đủ](../../../reports/ai_update/v62_research_20261104/adjudication_v3/cases_with_full_context.csv).

- Đủ24case; mỗi case có toàn bộ20comment, không cắt context, cùng actor, parent/reply, timestamp, target và nhãn tham khảo. Case cần quyết định được tô sáng.
- Các ô adjudicated_label, target quyết định, lý do và reviewer **đều trống**. Không tự gán thay người dùng, không có lượt human review/gold được tạo.
- HTML chạy local, không gọi mạng hay tự lưu nhãn. Khi người dùng thực sự điền và xuất, mỗi file quyết định mang annotation version timestamp mới; reference gốc không bị sửa. Các bản xuất chưa được xem là independent human gold vì NOV10 đã dùng nghiên cứu.
- Tests kiểm24context đầy đủ/blank decisions, parse JavaScript và empty-form không xuất nhãn. Không gọi đó là browser E2E hoặc giả lập reviewer. HTMLv1 từng lỗi escape newline JavaScript, được giữ; v2 sửa parse, v3 là bản cuối có version mới mỗi lần xuất. Chỉ dùng **v3**.

## 3. Indirect attack research

[INDIRECT_DESIGN.md](../../../reports/ai_update/v62_research_20261104/INDIRECT_DESIGN.md) ghi ranh giới từng nhóm, assumptions và negative controls.

Sáu predicates bounded cho personal generalized incompetence, character absolutism, rhetorical mind denigration, dehumanizing machine comparison, personal English devaluation và humiliating silencing. Cần dấu hiệu quy chiếu tới người trong clause; chặn self-reference, product subject, quote/report, negation, xin lỗi và can ngăn. Không có câu NOV10 nguyên văn, thread/comment ID hoặc label lookup trong processor. Raw TOXIC không tự tạo instance.

Các cues mỉa mai trình độ, personification/ẩn dụ yếu và Việt–Anh về khả năng chỉ ghi **exploratory trace**, không override final/target/instance trong lúc24reference chưa adjudicate. Không biến mọi câu hỏi, chê bai hoặc so sánh thành toxic. Không nới rule để đủ8NOV10events.

Target reuse conservative frozen infer_target/v6.1 history-conflict handling; không lấy recipient heuristic làm target. Repeated group `(actor,target)` với distinct timestamps và grounded instances; tests giữ riêng hai actor cùng nhắm một người. Không sửa cửa sổ hoặc evidence để ép recall.

## 4. Paired evaluation: v6.1 → v6.2

Cùng raw cache, threshold.41, text và reference. Old890 dùng **V1 historical cache**, không phải classifier-r06 metrics. Fresh10/NOV10 dùng user-exported r06 cache; các challenge nhỏ đã xem dùng captured actual-r06 scores. Raw/legacy recipient/lexicon invariants được assert khi replay.

| Cohort | Binary n | TP | FP | FN | TN | Macro-F1 |
|---|---:|---:|---:|---:|---:|---:|
| NOV10 development | 199 | 7→8 | 3→3 | 15→14 | 174→174 | .694160→.719137 |
| Fresh10 development | 195 | 18→18 | 1→1 | 4→4 | 172→172 | .931861→.931861 |
| Old890/886binary | 886 | 62→62 | 18→18 | 4→4 | 802→802 | .917892→.917892 |
| Postfix48 đã xem | 47 | 8→8 | 1→1 | 0→0 | 38→38 | .964095→.964095 |
| Postfix24 đã xem | 24 | 5→6 | 1→1 | 1→0 | 17→17 | .888889→.947253 |
| NOVaudit24 đã xem | 23 | 6→6 | 1→0 | 0→0 | 16→17 | .946387→1.0 |
| Repeated74 đã xem | 74 | 17→17 | 3→3 | 1→1 | 53→53 | .929187→.929187 |
| Challenge36 mới sau freeze | 36 | 3→6 | 0→0 | 5→2 | 28→28 | .731744→.911330 |

NOV10 toxic P/R .7000/.3182→.7273/.3636. Challenge36 P/R 1/.375→1/.75. Challenge36 raw Macro-F1 .7000 (TP3/FP1/FN5/TN27), giữ nguyên giữa hai processors. UNCERTAIN giữ riêng: bảy cohort development có tổng12referenceUNCERTAIN; không đổi nhãn hoặc bỏ thêm ca khó. Không có new label errors ở paired development hoặc challenge cuối.

| Cohort | Target đúng/reference | Target precision sau | Repeated TP/reference | Repeated P/R sau | Evidence đúng/emitted sau |
|---|---:|---:|---:|---:|---:|
| NOV10 | 0/22→2/22 | 1 | 0/8→1/8 | 1/.125 | 2/2 |
| Fresh10 | 16/22→16/22 | 1 | 6/7→6/7 | 1/.8571 | 15/15 |
| Old890 | 41/54→41/54 | 1 | 8/10→8/10 | 1/.8 | 20/20 |
| Postfix48 | 8/8→8/8 | 1 | 3/3→3/3 | 1/1 | 6/6 |
| Postfix24 | 5/6→6/6 | 1 | 1/2→2/2 | 1/1 | 4/4 |
| NOVaudit24 | 5/6→5/6 | 1 | 1/2→1/2 | 1/.5 | 2/2 |
| Repeated74 | 14/18→14/18 | 1 | 4/6→4/6 | 1/.6667 | 8/8 |
| Challenge36 mới | 1/8→6/8 | 1 | 0/3→2/3 | 1/.6667 | 4/4 |

Repeated FP=0 ở các cohort. Precision khi chưa emit gì là N/A (helper JSON ghi0), không diễn giải là đã đúng. Correctness của evidence khác completeness:

- **NOV10 chỉ2/21 reference evidence**, **0/8 event có đủ toàn bộ evidence**. Event mới là Test20 U05→U01 `[c11,c15]`; c11 đã raw/finalTOXIC từ trước, giờ mới có instance; c15 thêm được finalTOXIC. c06 vẫn thiếu. Actual target recall vẫn chỉ2/22.
- Fresh10 evidence15/19, full5/7events; Repeated74 evidence8/12, full4/6; challenge36 evidence4/6, full2/3.

## Challenge mới: khóa trước tạo, một lần scoring

[V62_LOCK.json](../../../reports/ai_update/v62_research_20261104/V62_LOCK.json) khóa source v6.2/v6.1/base layers, tests, evaluator, model hash và development summary **trước khi soạn** sáu scene/36comment. [Manifest input](../../../datasets/fixtures/v62_postfreeze_challenge_v1/manifest.json) khóa reference/input SHA trước inference. Actual r06 CPU offline bốn threads chấm một lần; các pipeline replay cùng score cache. Không train, không tune sau score.

Same AI soạn và đánh giá; challenge cố ý kiểm các grammar cùng diễn đạt chưa có coverage. Đây là synthetic research controls, **không author-blind, không human gold, không independent real-world evaluation**. Exact duplicate0, near warnings0 ở các cohort được manifest nêu rõ; không khẳng định loại hết trùng nghĩa hoặc overlap với mọi dữ liệu training.

Còn hai FN ở `V62_POSTFREEZE_04`: c03 “cục đá buộc vào chân cả đội” (raw.031809), c05 “chỉ tổ chật chỗ…không ai cần…” (raw.018134). Chưa có predicates đủ coverage cho hai diễn đạt này, mất pair N02→N03. Giữ nguyên cả hai nhãn/kết quả; không hardcode ẩn dụ hoặc chỉnh rule để đạt3/3. Không phát sinh degradation cuối cùng được quan sát; giới hạn mẫu nhỏ vẫn không cho phép promotion.

## Lưu lỗi và quá trình tự sửa trước freeze

- [remaining_fp_fn.csv](../../../reports/ai_update/v62_research_20261104/remaining_fp_fn.csv): **52 lỗi còn lại** trên tám cohort, gồm14FN/3FP NOV10. Không che các FP gốc hoặc chỉ chọn ca thành công.
- [evidence_and_target_errors.json](../../../reports/ai_update/v62_research_20261104/evidence_and_target_errors.json): 0 emitted target errors, 0 emitted evidence errors trên reference có grounding; lưu riêng missing reference evidence. Không coi reference UNKNOWN/UNCERTAIN là đã xác nhận.
- [uncertain_reference_cases.csv](../../../reports/ai_update/v62_research_20261104/uncertain_reference_cases.csv):12ca UNCERTAIN chưa có quyết định người. Bộ24adjudication gốc vẫn giữ labels và reviewer trống.
- Bản quote đầu làm mất2safe cues “câu…”; kết quả còn ở `phase1_quote/`. Đã sửa semantics và xác minh ở `phase1_quote_verified/` trước mở rộng indirect. Lỗi format cache repeated74 ban đầu cũng có log, không giả định là inference PASS.
- Hai control ban đầu FAIL ở máy-lặp-lại/product-subject; tách content/addressee view và giữ assertion, kết quả cuối43processor testsPASS. Các failure/log/source snapshot giữ trong inventory. Không có post-challenge chỉnh sửa processor/test đã khóa.

## 5. Stabilization, exclusions và trạng thái

- **722 standard root tests PASS/0FAIL/1 Starlette deprecation warning**;45targeted PASS (43processor+2adjudication, đã nằm trong root), cuối cùng hai adjudication tests rerunPASS sau thay version xuất. Không cộng trùng số test.
- Hai red expectations v6.2 PASS sau khi baseline2FAIL; original v6.1 historical red behavior giữ nguyên. Không sửa reference/assertion để tạo PASS.
- V1/r06/default/threshold.41 và readiness1.311SHA **PASS/không đổi**. Không frontend build, Dashboard/ASGI-default edit, DB live, trainingr07, paid API, deploy hoặc model promotion. Không chạy lại Social177/browser E2E; evidence đã khóa được hash-verify, không tuyên bố đó là test mới.
- [Exclusion v6.2 có version](../../../datasets/real_conversations/manifests/development_exclusions.research_v62_20261104.json) kế thừa overlay trước, giữ NOV10/Fresh10/challenges đã xem và thêm sáu thread mới. **16/16 checks** (10NOV10+6new) đều EXCLUDED_DEVELOPMENT. Default exclusion manifest/loader đã khóa giữ nguyên; future independent preflight phải chỉ định overlay mới, không tuyên bố default tự dùng nó.
- T028/T029 formal **BLOCKED**, T030–T033 **PARTIAL**; historical taskDONE giữ nguyên. Human real-cohort acceptance vẫn0/200 và thiếu human review/lock. Vòng nghiên cứu safe scope hoàn tất, không nghiệm thu formal.

Next: người dùng có thể adjudicate24case trong HTMLv3 khi thuận tiện; chỉ dùng quyết định thật và annotation version mới. Các weak sarcasm/metaphor còn lại cần thí nghiệm mới có negative controls và fresh challenge, không tự nới rule theo các challenge đã xem. Không tự bật v6.2 vào demo/default.

Reproduction/evidence: [README](../../../reports/ai_update/v62_research_20261104/README.md). File thêm/sửa và SHA: [ARTIFACTS.json](../../../reports/ai_update/v62_research_20261104/ARTIFACTS.json). Resume: [AUTO_PROGRESS](../../../tasks/AUTO_PROGRESS.md).
