# NOV10 root-cause audit — 04/11/2026

**Kết luận chính: 200/200 attack instances=false được tái hiện bằng đúng v6.1 hiện tại vì cả bảy họ predicate công kích đều không match.** Không có bằng chứng pipeline bị tắt, Dashboard dùng nhầm v5, hoặc time window làm mất tám event. Không đổi rule để ép đạt các nhãn mỉa mai còn mơ hồ. Audit hoàn tất; một lỗi quote riêng trong challenge bổ sung được tái hiện bằng red tests và **chưa sửa**.

## Import và nguồn bằng chứng

[NOV10 regression v1](../../../datasets/fixtures/nov10_regression_v1/manifest.json): 10 input JSON, 10 analysis JSON, hai reference CSV và hai tài liệu nguồn sao chép nguyên byte từ bộ `ShieldVI_10_Kich_Ban_Moi_20261104`. Hash input đối chiếu test_manifest nguồn. Không có file evaluation riêng trong pack; số liệu người dùng gửi được lưu riêng ở `source_metadata/user_reported_evaluation.json`, còn kết quả tính lại ở [metrics.json](../../../reports/ai_update/nov10_audit_20261104/metrics.json). Không gọi file tự tính là báo cáo nguồn đã nhập.

200 comment: **177 CLEAN / 22 TOXIC / 1 UNCERTAIN**, 199 binary. Nhãn giữ nguyên `synthetic_reference`, không human gold. Bộ này là development/regression sau audit, cấm training và không dùng cho independent real-world acceptance. Không chỉnh text, parent, timestamp hoặc nhãn để vượt test.

## Xác minh processor và đường chạy

1. Exact cached replay qua `analyze_thread_v6` rồi serialize bằng `AnalyzeResponseV2` **khớp toàn bộ 10 wire export**, không chỉ version string. Model name/profile/threshold/raw/lexicon/context/assessment/target/instance/evidence đều giữ nguyên.
2. Version khai báo và tái hiện: context-v6.1-research, target-v6.1-research, repeated-v6.1-research, context-assessment-v1; lexicon hash và serializer được ghi trong export. Source processor SHA256 `8f3a4fe5b78b99b126a418b8ef1c40c756c995c22c876265e09f419a60b7c493` khớp experiment_lock_v2 trước đó.
3. Probe canonical ASGI mới, r06 thật, CPU offline bốn threads: Test12/Test15/Test20, **60 comment**, mỗi thread gọi `context_v6` đúng 20 lần. Raw score khớp export, max absolute difference **0**. Thêm positive control ba comment tạo đúng B→A repeated evidence. [runtime_probe.json](../../../reports/ai_update/nov10_audit_20261104/runtime_probe.json) giữ call instrumentation, model/source hash và actual outputs.
4. Đây là bằng chứng runtime hiện tại tái hiện đúng lỗi; export gốc không có process/source-hash attestation nên không thể chứng minh cryptographic identity của process lịch sử. Không suy đoán lỗi version từ sự vắng mặt của target.
5. `research_trace` có trong output nội bộ nhưng không thuộc `AnalysisSignalsOut`, nên bị serializer bỏ khỏi JSON API. Absence của trace không chứng minh context không chạy. Positive-control test xác nhận serializer vẫn giữ `directed_attack_candidate=true`, instance và target khi processor thực sự tạo chúng.

Đường dữ liệu thực tế:

```text
input text/parent/user/time
  → r06 raw probability + frozen .41
  → legacy/lexicon signals
  → v6.1 context: NFC/homograph masking + 7 attack-pattern families
  → target_v6 → infer_target
  → qualified = attack AND context confidence AND target AND target confidence
  → group qualified instances by (actor,target), ≥2 timestamps
  → repeated evidence

assessment là nhánh riêng: nếu context chưa xác nhận gì → raw_model_fallback
```

v6.1 compose nền v5 trước khi tính lại các layer nghiên cứu. Điều này không biến output thành v5. Raw TOXIC không tự thành directed attack, reply recipient không tự thành attack target, policy risk không phải visibility action. Trường legacy `research_only` gắn với profile cũ không phải chứng nhận production; version nghiên cứu và mọi bằng chứng synthetic vẫn phải được tôn trọng.

## Vì sao 200/200 đều false

Trên cả masked và unmasked normalized text, **zero match** cho:

| Họ predicate | Kết quả NOV10 |
|---|---:|
| v5 ATTACK | 0 |
| v5 DISPARAGEMENT | 0 |
| v5 INDIRECT | 0 |
| personal_conduct | 0 |
| personal_humiliation | 0 |
| english_personal_insult | 0 |
| sarcastic_incompetence | 0 |

Vòng xử lý không đến các nhánh suppression, quote, negation, self-reference hoặc addressee cho bất kỳ attack match nào: không có match để xét. Vì vậy không có bằng chứng homograph masking, quote stripping hoặc target conflict xóa các attack này. [comment_traces.json](../../../reports/ai_update/nov10_audit_20261104/comment_traces.json) lưu 200 normalized texts, hit arrays từng họ predicate, qualification gates và reply/target riêng; [unmasked_predicate_audit.json](../../../reports/ai_update/nov10_audit_20261104/unmasked_predicate_audit.json) xác nhận hit count trước masking cũng bằng 0.

Context vẫn tạo tags: APOLOGY3, QUOTE8, SET_BOUNDARY2, INTERVENTION1, ACKNOWLEDGEMENT1, PROFANITY_NON_DIRECTED5 (đếm tag, có thể chồng nhau). Positive control tạo được context→target→instance→event. **Phân loại nguyên nhân: thiếu coverage các diễn đạt gián tiếp/khả năng/mỉa mai, không phải global runtime disable.** Không lấy việc raw nhận TOXIC làm bằng chứng đủ để bỏ qua gate an toàn.

## Bốn ca ưu tiên: predicate từ chối chính xác

| Ca | Raw | Final basis | Điểm dừng |
|---|---:|---|---|
| Test12 c06 “Trình U02…band 7? ambitious dữ” | .598919 | raw_model_fallback → TOXIC | Cả 7 hit array rỗng; không có pattern cho câu hỏi mỉa mai năng lực |
| Test15 c07 “…thiếu hiểu biết…hại cả mèo” | .584926 | raw_model_fallback → TOXIC | Không có bounded predicate cho lời chê năng lực/chăm sóc này |
| Test15 c12 “…chưa biết gì…đòi làm người hùng” | .447230 | raw_model_fallback → TOXIC | Không match các pattern đã định nghĩa; chưa có xác nhận công kích cá nhân |
| Test20 c11 “…gom deadline…tự làm chẳng ra gì” | .502409 | raw_model_fallback → TOXIC | Không có predicate cho diễn đạt này; không phải target ID bị mất |

Cả bốn: `context.attack_candidate=false`, confidence low, `infer_target` trả sớm tại **`if not context.attack_candidate: TargetSignals(method='non_attack_or_uncertain')`**. `target_v6` cũng trả ngay khi context không attack; qualification false và không thêm pair history. Không có predicate kiểu “raw<.41” từ chối bốn câu này.

Diagnostic **oracle-only**, không dùng trong predictions/metrics: khi tạm cấp attack context cho 22 reference TOXIC, frozen target lookup tìm được đúng **22/22 explicit targets**. Điều này cô lập gate context là nút thắt trong các câu này; **actual target recall vẫn 0/22**, không được báo 22/22 như kết quả model.

## Mỉa mai, ẩn dụ và nhãn cần adjudication

Test11 phản ánh giao hàng trễ, quy trách nhiệm và mỉa mai “chuyên nghiệp theo kiểu ngược”; Test18 dùng ẩn dụ “bảng thông số biết đi”/trưng benchmark; Test19 phê bình copy Pinterest và “gợi ý rẻ tiền”. Không có matches tương ứng. Những lời này có thể chuyển từ phê bình hành vi/sản phẩm sang hạ thấp cá nhân tùy ngữ cảnh; **không thêm blanket sarcasm/criticism→TOXIC rule**.

[adjudication_candidates.csv](../../../reports/ai_update/nov10_audit_20261104/adjudication_candidates.csv) có **24 mục rà soát**: toàn bộ 22 reference TOXIC để kiểm lại ranh giới, một UNCERTAIN, và Test16 c04. Bao gồm cả ca tương đối rõ để đối chiếu, không khẳng định tất cả đều sai nhãn. Giữ original_label/target, câu hỏi theo từng chủ đề và các ô quyết định/reviewer trống. Chưa có human review, không loại các ca khó khỏi metrics, không yêu cầu gán ngay trong phiên này.

## Ba false positives

| Ca | Raw | Context / final | Phân tích |
|---|---:|---|---|
| Test16 c04 | .652878 | Không safe tag, raw fallback TOXIC | Chê chiều sâu review; không nhận được cue phân biệt phê bình nội dung với công kích. Không có directed instance. Ranh giới được đưa vào adjudication. |
| Test18 c20 | .414980 | PROFANITY_NON_DIRECTED, raw fallback TOXIC | Cảm thán deadline “vl”; tag này không nằm trong SAFE_TAGS nên không tự hạ raw. Đây là giới hạn assessment/coverage, chưa phải bằng chứng cần coi mọi non-directed profanity là CLEAN. |
| Test20 c08 | .410180 | Không safe tag, raw fallback TOXIC | “Góp ý nhạc…đâu có nói leader kém” chưa khớp intervention/negation hiện có. Không có attack predicate để negation logic hoạt động. |

Raw FP4→final FP3 là do Test18 c12 raw .549342 được QUOTE/bounded_non_attack_context chuyển CLEAN. Điều này cũng chứng minh context có tác dụng trên pack, dù không tạo directed attack nào.

## Tám repeated pairs

| Thread | Actor→target | Evidence | Span phút | Qualified instances |
|---|---|---|---:|---:|
| 11 | U02→U03 | c06,c10,c14 | 16 | 0 |
| 12 | U04→U02 | c06,c12,c16 | 20 | 0 |
| 14 | U03→U01 | c08,c13,c17 | 18 | 0 |
| 15 | U02→U03 | c07,c12,c17 | 20 | 0 |
| 16 | U04→U02 | c09,c14 | 10 | 0 |
| 18 | U02→U03 | c09,c14 | 10 | 0 |
| 19 | U04→U02 | c07,c12 | 10 | 0 |
| 20 | U05→U01 | c06,c11,c15 | 18 | 0 |

21 reference evidence comments có actor/target/timestamp nhất quán, tối thiểu hai thời điểm khác nhau; [event_audit.json](../../../reports/ai_update/nov10_audit_20261104/event_audit.json). Không có instance đi vào `pairs`, nên không thể qua điều kiện ≥2instances/≥2timestamps. Với explicit grounded pairs, v6.1 hiện không áp gate30phút/16comment trong vòng group; bounded root-exchange resolution là nhánh khác. Không dùng mô tả window trong README pack để suy đoán runtime. Test20 c09 thuộc actor U02, **không** được cộng vào pair U05→U01.

## Metrics trước/sau audit — không có rule patch

| Cohort / processor | TP | FP | FN | TN | Macro-F1 | Target recall | Repeated recall |
|---|---:|---:|---:|---:|---:|---:|---:|
| NOV10 raw r06 | 7 | 4 | 15 | 173 | .686094 | N/A | N/A |
| NOV10 export v6.1 | 7 | 3 | 15 | 174 | .694160 | 0/22 | 0/8 |
| NOV10 replay sau audit, nguyên v6.1 | 7 | 3 | 15 | 174 | .694160 | 0/22 | 0/8 |
| Fresh10 v6.1, cũ→replay | 18→18 | 1→1 | 4→4 | 172→172 | .931861→.931861 | 16/22→16/22 | 6/7→6/7 |
| Regression cũ 886 binary/V1-cache, v6.1 | 62→62 | 18→18 | 4→4 | 802→802 | .917892→.917892 | 41/54→41/54 | 8/10→8/10 |

NOV10 toxic P/R .70/.318182. Zero target emissions và zero event emissions: precision **không xác định** (JSON helper quy ước số0), recall0. Evidence correctness **0 emitted, không thể kết luận precision1**; reference coverage0/21. Một UNCERTAIN vẫn được đếm riêng.

## Challenge mới và lỗi kỹ thuật riêng chưa sửa

[nov10_audit_challenge_v1](../../../datasets/fixtures/nov10_audit_challenge_v1/manifest.json): 4 scene AI soạn riêng/24comment, 6TOXIC/17CLEAN/1UNCERTAIN, ba người/scene. Hash rule khóa trong challenge_lock.json **trước khi soạn**, manifest/input/labels khóa trước inference. One actual offline r06 scoring; không tune sau scoring. Same-author synthetic controls/coverage probe, không blind/human/real-world evaluation. Exact duplicate0 và near warnings0 trên các cohort được manifest nêu rõ; không khẳng định semantic independence.

V6.1: 23binary, **TP6/FP1/FN0/TN16, Macro-F1 .946387**, target5/6 (precision5/6), repeated1/2 (P1/R.5), evidence2/2đúng nhưng coverage2/4. Không có thay đổi rule trước/sau audit nên các số này không chứng minh bản sửa cải thiện NOV10. Evaluator còn lưu v5 diagnostic side-by-side (.897321); cột `before` trong raw challenge JSON là **v5**, không phải “trước audit v6.1”. Không tráo hai phép so sánh.

Lỗi quote ở `NOV10_AUDIT_CHALLENGE_02 c02`: “Tác giả viết câu ‘mày đúng là đồ ngu’…” có normalized attack span **[30,36)** bên trong quote **[17,37)**. `assigned` xét toàn prefix nên nhận chủ ngữ “mày…là” **bên trong** quote như external assignment; PAST_REPORT chưa nhận attribution này. Ngoài quote, “câu” fold→`cau` tại **[13,16)** còn bị ADDRESS hiểu thành “cậu”. Kết quả tạo bogus target N01 theo parent và attack instance của người đang kể lại. Đây là lỗi scope/attribution có bằng chứng, **tách biệt** với zero attack-pattern coverage ở NOV10.

Hai explicit red probes FAIL, một direct-assignment control PASS: [quote_red_tests.log](../../../reports/ai_update/nov10_audit_20261104/quote_red_tests.log). Không xfail, không sửa kỳ vọng, không gọi lỗi đã sửa. Các probe nằm trong evidence directory, chạy bằng lệnh riêng; **không thuộc con số677 root PASS**. Giữ revision/challenge đã khóa trong đợt root-cause audit này; sửa quote phải là revision nghiên cứu tiếp theo, giữ các red expectation và dùng challenge mới trước đánh giá. Không broad whitelist quoted text vì công kích mới ngoài quote vẫn phải được giữ.

Challenge còn thiếu instance cho `NOV10_AUDIT_CHALLENGE_01 c05` dù raw/final đều TOXIC; cùng hiện tượng raw fallback không đủ grounding. Actor separation ở scene04 đúng: hai actor một attack không tạo repeated chung.

## Exclusion, kiểm thử và trạng thái

- [Exclusion overlay có version](../../../datasets/real_conversations/manifests/development_exclusions.research_20261104.json) giữ parent SHA, hợp nhất34thread mới: Fresh10/old small challenges20 + NOV10 10 + challenge mới4. Dùng lại frozen development_index để xác minh **10/10 NOV10 bị EXCLUDED_DEVELOPMENT**. Guard cũng chặn đổi thread ID nếu còn long-text match; không match không có nghĩa được approve độc lập.
- **Không sửa default exclusion manifest/loader đang readiness-locked.** Future evaluation preflight phải chỉ định overlay mới; không tuyên bố pipeline mặc định tự đọc nó. CLI và SHA được ghi ở exclusion_verification.json. Đây là đăng ký exclusion kiểm chứng được, không phải independent evaluation admission.
- Standard root **677 PASS/0FAIL/1 Starlette deprecation warning**, gồm29test mới; targeted54PASS trước khi thêm ba overlay tests (không cộng trùng). Supplemental quote red probes **2FAIL/1PASS**, lỗi còn mở. Actual ASGI r06 probes63comment PASS. Fresh10+890comment cached replay không suy giảm.
- V1/r06/default/threshold.41, readiness1.311file, dataset test độc lập và source labels giữ nguyên. Không training r07, download, frontend build, deploy hoặc ghi DB live. Không đổi app/main.py hoặc processor v6.1. Social/browser tests cũ được hash-verify, không chạy lại trong audit này.
- T028/T029 formal BLOCKED; T030–T033 PARTIAL, historical DONE giữ nguyên. Root-cause audit hoàn tất, coverage chưa sửa và quote bug vẫn mở. Real/human acceptance vẫn thiếu dữ liệu thật/nhãn người. Tiếp theo: adjudicate danh sách, rồi thiết kế thí nghiệm indirect coverage; quote scope có thể sửa bằng revision riêng sau các red tests, không thay frozen v6.1 hoặc default.

File inventory/SHA và trạng thái: [ARTIFACTS.json](../../../reports/ai_update/nov10_audit_20261104/ARTIFACTS.json), [README chạy lại](../../../reports/ai_update/nov10_audit_20261104/README.md), [AUTO_PROGRESS](../../../tasks/AUTO_PROGRESS.md).
