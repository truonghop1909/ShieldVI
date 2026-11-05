# Fresh10 recovery — 04/11/2026

Đã sửa và kiểm chứng trong processor **v6.1 nghiên cứu, chỉ gọi bằng evaluator/test**. API/Dashboard vẫn dùng v5; chưa kích hoạt bản sửa trên demo. Giữ nguyên checkpoint V1/r05/r06/default, threshold 0.41 và readiness lock 1.311 file. Không training, deploy, sửa nhãn hoặc tập test độc lập.

## Dữ liệu và phạm vi bằng chứng

- [Fresh10 versioned](../../../datasets/fixtures/fresh10_regression_v1/manifest.json): 10 input JSON, 10 analysis JSON người dùng xuất, hai CSV tham khảo và bốn tài liệu nguồn được sao chép nguyên byte; 200 comment: 173 CLEAN, 22 TOXIC, 5 UNCERTAIN. Cả 26 file nguồn được kiểm SHA. Fresh10 là development/regression từ lần phân tích này; không dùng training.
- So sánh Fresh10 dùng **score cache r06 của người dùng**, không tuyên bố chạy lại neural inference trên 200 comment. Replay v5 khớp kết quả nhập. Hậu tố ViCTSD trong tên hiển thị adapter không chứng minh r06 được train bằng ViCTSD.
- Regression cũ 890 comment dùng **cache V1 lịch sử**, 886 nhãn nhị phân; không phải đánh giá classifier r06. Target có reference coverage trên 797 comment, 54 directed attacks.
- Hai lô bổ sung lần lượt 48 và 24 comment có actual r06 CPU inference offline, bốn threads xử lý CPU. Không thay weights hoặc threshold. Mỗi lô chỉ có một lần neural scoring; replay dùng cache cùng model/manifest hash.
- Tất cả nhãn là **synthetic_reference**, không human gold, không independent real-world evaluation. Cùng AI soạn và đánh giá; mẫu nhỏ, có selection bias. Không ước lượng hiệu quả ngoài thực tế từ các điểm này.

## Root-cause trước khi sửa

[ROOT_CAUSE.md](../../../reports/ai_update/fresh10_recovery_20261103/ROOT_CAUSE.md) được lưu trước implementation; [case_traces.json](../../../reports/ai_update/fresh10_recovery_20261103/case_traces.json) giữ raw/context/target/instance/policy/final trước–sau.

**Test09 c17:** raw 0.798809. DEFENSE chỉ match normalized span `[16,30)` = `khong co nghia`; đây là liên từ, không đủ bằng chứng tự bảo vệ. Grammar APOLOGY bỏ sót tiền tố “Nhưng t”, vocabulary không nhận “phông bạt…cringe”, nên `non_attack_context_confirmed` xóa TOXIC thành CLEAN. Reply trỏ vào chính apology c15 của U02; legacy recipient U01 không phải bằng chứng target. Bản thử nghiệm bỏ DEFENSE chỉ dựa liên từ, nhận công kích mới theo clause, kết hợp apology nhắc đích danh và lịch sử attack đã có bằng chứng để phục hồi U03.

**Test10 c14:** raw 0.011560. Accent folding biến **ngò → ngo**, khớp ATTACK `[28,31)`; `ban` làm direct-address cue, sinh attack span `[0,35)` và addressed reply U05 với evidence `[c14,c13]`. Bản sửa bảo toàn nghĩa đồng âm có dấu ở bước nhận diện cá nhân; không whitelist toàn câu. Unit test vẫn nhận công kích mới trong câu vừa có “hạt ngò” vừa chửi người, và nhận tên người Ngô. Span dùng tọa độ normalized/NFC, không phải offset byte UTF-8.

**Test05 c08/c10/c13, Test02 c10:** v5 không nhận được boundary, phân biệt góp ý với hạ nhục, hoặc tự trào về đồ vật; final rơi về raw TOXIC. Cues có phạm vi cụ thể bổ sung SET_BOUNDARY/INTERVENTION/ACKNOWLEDGEMENT. Chỉ kết luận non-attack khi không có công kích mới/unresolved clause; không có quy tắc “xin lỗi ⇒ CLEAN”.

**Test07:** cả c06/c07/c11/c12 đều raw TOXIC nhưng `directed_attack_candidate=false`, target method `non_attack_or_uncertain`, instance=false. Bộ repeated không bị lỗi gom nhóm; thiếu attack predicates trước nó. Bổ sung predicates hạn chế cho hạ nhục/conduct (“sống kiểu vô ý thức”, “cãi cùn”…), có kiểm quote/report/intervention và target evidence. Phục hồi đúng hai cặp riêng U02→U03 `[c06,c11]`, U03→U02 `[c07,c12]`. Raw TOXIC một mình vẫn không sinh attack instance.

**Test03/Test08:** Test03 c07 thiếu conduct predicate và cần đi qua self-reply đến exchange có người nhận; evidence mới `[c07,c06,c04]`, target U02. Test08 c13 thiếu English/personal-humiliation predicate; explicit U01 được giữ làm target evidence. Hai event nay bao phủ đủ `[c07,c12,c16]` và `[c08,c13,c17]` tương ứng. Không tăng evidence bằng mọi reply trong thread.

**Test05 actor separation:** hai attack tham khảo thuộc U02 và U03 cùng hướng U01, không đủ repeated cho từng actor. Group key luôn `(actor,target)`; kết quả không event. `target_user_id` legacy được giữ nguyên như recipient heuristic; `directed_at_user_id` chỉ phát ra khi attack và target đủ bằng chứng. Có reply không đồng nghĩa công kích.

**Indirect/ambiguous references:** [reference_review_notes.csv](../../../reports/ai_update/fresh10_recovery_20261103/reference_review_notes.csv) đánh dấu chín trường hợp cần adjudication, gồm toàn bộ Test01 c06/c11/c15, Test06 c07/c11/c15. Không đổi nhãn hoặc bỏ các lỗi khỏi mẫu số. Không nâng mọi sarcasm/coaching/phê bình tập thể thành công kích để đạt điểm. Test01 c15 và Test06 c07/c15 vẫn FN.

## Before/after với cùng raw score

| Cohort | TP | FP | FN | TN | Macro-F1 |
|---|---:|---:|---:|---:|---:|
| Fresh10, 195 binary | 15→18 | 6→1 | 7→4 | 167→172 | .830105→.931861 |
| Cũ, 886 binary | 62→62 | 18→18 | 4→4 | 802→802 | .917892→.917892 |
| Lô 48 đã chuyển development, 47 binary | 4→8 | 3→1 | 4→0 | 36→38 | .722363→.964095 |
| Lô mới sau freeze v6.1, 24 binary | 4→5 | 2→1 | 2→1 | 16→17 | .777778→.888889 |

Fresh10 raw Macro-F1 .803968 giữ nguyên. Final toxic P/R .714286/.681818 → .947368/.818182. UNCERTAIN được đếm riêng (Fresh10:5, lô48:1); không đổi thành CLEAN. Không có abstention mới bị bỏ khỏi mẫu số nhị phân.

| Cohort | Target đúng/reference | Target precision | Repeated TP/reference | Repeated P/R sau | Evidence đúng/emitted sau | Reference coverage sau |
|---|---:|---:|---:|---:|---:|---:|
| Fresh10 | 5/22→16/22 | .8333→1 | 2/7→6/7 | 1/.8571 | 15/15 | 15/19; 5/7 full events |
| Cũ | 41/54→41/54 | 1→1 | 8/10→8/10 | 1/.8 | 20/20 | Không có CSV evidence-completeness tương đương |
| Lô48 development | 2/8→8/8 | .5→1 | 0/3→3/3 | 1/1 | 6/6 | 6/6; 3/3 full |
| Lô24 mới | 4/6→5/6 | 1→1 | 1/2→1/2 | 1/.5 | 2/2 | 2/4; 1/2 full |

Mỗi cohort repeated FP=0. Evidence precision không đồng nghĩa evidence đầy đủ; Fresh10 còn thiếu bốn reference comment. Grounding yêu cầu actor-target đúng, comment tách biệt và ít nhất hai thời điểm khác nhau. Reply/context/lexicon/raw/policy risk/final assessment vẫn là các trường riêng; schema V2 và raw/legacy/lexicon invariants được xác minh khi replay.

## Lỗi mới và kỷ luật challenge

1. `development_v1` từng gây lỗi mới ở lời chấp nhận xin lỗi, “bản dịch”, và lời từ chối bị xúc phạm. Không xóa kết quả thất bại; `development_v2/v3` sửa bằng phạm vi và dấu tiếng Việt, regression cũ trở lại baseline.
2. `experiment_lock.json` khóa v6 **trước** khi soạn lô48. Lần chấm đầu có **một FP mới**, câu xin lỗi “đã gọi bạn là thiên tài tự phong”: reporting bị address-assignment ghi đè. Kết quả gốc TP8/FP2/FN0/TN37, Macro-F1 .931287 và snapshot source vẫn nguyên. Lô này đã được chuyển development; không tiếp tục gọi là holdout chưa thấy.
3. Hai red tests tái hiện lỗi reporting; sửa chung cho explicit reporting, vẫn cho phép endorsement/direct assignment và công kích ở clause mới. 28 targeted tests PASS. `experiment_lock_v2.json` giữ parent hash và khóa v6.1 sau sửa, trước khi soạn lô24 khác.
4. Lô24 mới được chấm sau freeze v6.1, không có rule tuning sau scoring. Còn FP `FRESH10_FINAL_02 c05` phê bình độ sáng ảnh (raw .565035); FN `FRESH10_FINAL_04 c05` hạ nhục bằng ẩn dụ “phí oxy” (raw .150386), kéo theo mất event thứ hai. Không hardcode ẩn dụ để đạt 2/2. Các FN/FP khác còn trong JSON metrics và CSV review notes; không che giấu.

## Kiểm thử, tính toàn vẹn và triển khai

- Full root **648 PASS / 0 FAIL / 1 deprecation warning**, gồm 28 test Fresh10; log `full_tests.log`. Red reporting: 2 FAIL/1 PASS trước sửa, lưu `quote_scope_red_tests.log`.
- Replay 890 comment cũ giữ nguyên toàn bộ classification/target/repeated metrics, không thêm lỗi nhãn. Test09/Test10, bốn FP yêu cầu, actor separation, quote/apology/new attack có unit/regression cụ thể.
- [integrity.json](../../../reports/ai_update/fresh10_recovery_20261103/integrity.json): 26 SHA nguồn, parent/chronology/unique IDs, 272 distinct texts, exact duplicates=0, near-duplicate warnings=0 tại ngưỡng .85 so với bộ synthetic500 và các lô mới. SHA readiness 1.311 file PASS, không reseal. Không thay source text/expected labels.
- Social177, browser E2E và shadow/rollback cũ được giữ và hash-verified qua readiness; **không chạy mới** ở công việc này vì không sửa API/UI/DB/default.
- Module `app/experiments/fresh10_v6.py` là opt-in nghiên cứu compose sealed v5, không được import bởi app mặc định. Các thay đổi chưa có hiệu lực trên Dashboard. Cần quy trình release riêng nếu muốn tích hợp; không sửa readiness lock hiện tại để lách điều kiện.
- [T028_EXCLUSION_EXTENSION.json](../../../reports/ai_update/fresh10_recovery_20261103/T028_EXCLUSION_EXTENSION.json) liệt kê 20 thread mới phải loại khỏi evaluation độc lập sau này. **Chưa gộp vào runtime exclusions đã khóa**; lần tạo evaluation lock tiếp theo phải gộp extension và chạy leakage audit. Không coi corpus hiện tại tự động bảo vệ các fixture mới này.

## Trạng thái và tiếp tục

T028/T029 formal **BLOCKED**: real valid 0/200, human labels 0; không có quyền training mới. T030–T033 **PARTIAL**, giữ historical DONE; bổ sung Fresh10 development evidence không nghiệm thu độc lập hoặc production. T031 registry/default và T032 integration giữ nguyên.

Hoàn tất scope sửa/kiểm chứng nghiên cứu của yêu cầu Fresh10. Tiếp theo: adjudicate chín reference mơ hồ trước khi mở rộng indirect rules; giữ nguyên challenge24 đã thấy cho regression tương lai; cần cohort mới được khai báo trước cho lần thử tiếp theo. Independent real acceptance vẫn cần nguồn hợp lệ, review người và evaluation lock. Không yêu cầu người dùng gán nhãn ngay.

File thêm/sửa và SHA: [ARTIFACTS.json](../../../reports/ai_update/fresh10_recovery_20261103/ARTIFACTS.json). Lệnh chạy lại: [README](../../../reports/ai_update/fresh10_recovery_20261103/README.md). Resume: [AUTO_PROGRESS](../../../tasks/AUTO_PROGRESS.md).
