# Thực nghiệm synthetic r06 — EXPERIMENTAL

Đã thực sự train và đánh giá candidate riêng; không thay mô hình mặc định. Kết quả dưới đây chỉ dùng nhãn AI synthetic, không phải human gold hay real-world evaluation.

## Dữ liệu và kiểm tra

Tái sử dụng nguyên văn 500 hội thoại/5.115 bình luận từ `datasets/synthetic_conversations/genz_v2`; không sinh mới câu chữ trong lượt này. Nguồn có 200 hội thoại legacy và 300 hội thoại Codex đã viết trước đó. Xuất view mới tại `datasets/synthetic_genz`, giữ nguyên nguồn, nhãn và split gốc. Schema mới làm phẳng annotation nhưng không thay nội dung. Compiler và lịch timestamp là deterministic; không chứng minh hội thoại là dữ liệu thật.

Nhãn CLEAN4.667/TOXIC369/UNCERTAIN79; 102 cờ cần rà soát, chưa có human review. 3–6 người, 10–18 bình luận/thread. 20 nhóm tình huống; 272 thread không có TOXIC, 396 cấu trúc vai trò, cấu trúc phổ biến nhất xuất hiện12lần. Pilot20 rồi batch50, cuối30; checkpoint đủ500. JSON/schema/parent/timestamp/participant/target/repeated evidence PASS theo validator. Exact duplicate0, near-duplicate comment0/thread0 tại ngưỡng char5Jaccard0.85(min35ký tự)/0.60; không khẳng định hết trùng nghĩa hoặc diễn đạt tự nhiên.

View mới: train440/validation30/challenge30 theo scenario family và strata nhãn, seed20261103, không dựa score. Toàn bộ60family development cũ vẫn ngoài training. Train4.398binary (CLEAN4.085/TOXIC313), loại UNCERTAIN/cờ review và kiểm chống trùng heldout/regression. Validation306binary+2UNCERTAIN; challenge311binary+1UNCERTAIN. Không ép UNCERTAIN sang nhị phân. Nhãn đánh giá tách khỏi predictions/API input.

Validation/challenge đã được dùng trong nghiên cứu rule trước đây, không blind. Việc chia view mới không biến chúng thành test độc lập. Audit tập train r05 cho exact/near overlap với cả60heldout=0. Không đọc nhãn/chạy đánh giá tập test ViCTSD gốc. Không dùng ViCTSD để train r06 vì quyền sử dụng bản local chưa được xác minh lại.

## Huấn luyện thực tế

CPU4threads, một run, giới hạn900giây, chi phí ngoài0. CUDA không sẵn. AdamW LR1e-5,wd0.01,batch64,maxlen128,seed20261103; distillation V1 weight0.25,T2; positive weight sqrt(4085/313)=3.612633(cap4), áp dụng CE và distillation. Encoder96.975.360tham số đóng băng; classifier592.130tham số được train. 207steps/3epochs/79.75giây, chọn epoch3 bằng validation Macro-F1 ở0.41, reload sai số0. Encoder/baseline/source hashes giữ nguyên.

Khác r05: r05 dùng6.942ViCTSD+4.398synthetic, khởi tạo V1.1, early stopping trên ViCTSD validation, LR5e-6, distillation1.0 và synthetic weight0.1. r06 khởi tạo originalV1, chỉ synthetic, có class balancing và chọn bằng synthetic validation. Đây là so sánh các recipe, không phải ablation cô lập một biến. Checkpoint cũ không ghi đè.

Full/partial encoder fine-tuning chưa chạy. Notebook `notebooks/T029_Synthetic_Experimental_R06.ipynb` có5codecells, syntax PASS, tất cả unexecuted; mặc định chỉ preparation, ZIP bootstrap kiểm traversal/symlink, không upload/download/mount tự động. GPU/config/resource receipt mới phải phù hợp; không dùng lại quyền r06 để chạy full fine-tune.

## So sánh raw classifier, threshold0.41

| Split | Model | N | Accuracy | Macro-F1 | Toxic P | Toxic R | Toxic F1 | TP | FP | TN | FN |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| synthetic_validation | V1 | 306 | 0.934641 | 0.688581 | 0.368421 | 0.466667 | 0.411765 | 7 | 12 | 279 | 8 |
| synthetic_validation | r05 | 306 | 0.934641 | 0.670259 | 0.352941 | 0.400000 | 0.375000 | 6 | 11 | 280 | 9 |
| synthetic_validation | r06 | 306 | 0.964052 | 0.823834 | 0.611111 | 0.733333 | 0.666667 | 11 | 7 | 284 | 4 |
| synthetic_challenge | V1 | 311 | 0.942122 | 0.779884 | 0.541667 | 0.650000 | 0.590909 | 13 | 11 | 280 | 7 |
| synthetic_challenge | r05 | 311 | 0.945338 | 0.787645 | 0.565217 | 0.650000 | 0.604651 | 13 | 10 | 281 | 7 |
| synthetic_challenge | r06 | 311 | 0.954984 | 0.828798 | 0.625000 | 0.750000 | 0.681818 | 15 | 9 | 282 | 5 |

Mỗi hàng dùng cùng tập bình luận. Encoder/tokenization ba model bằng nhau được kiểm hash; shared-encoder inference dùng ba head thật, đối chiếu full-forward probes sai số tối đa <4e-8, không có score trong1e-5 quanh0.41. R06 được chọn trước challenge; chỉ một lượt challenge sau chọn, không train/tune lại sau khi xem kết quả.

## Hybrid advisory tách riêng

| Split | Model | Macro-F1 | P | R | TP | FP | TN | FN |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| synthetic_validation | V1 | 0.833325 | 0.600000 | 0.800000 | 12 | 8 | 283 | 3 |
| synthetic_validation | r05 | 0.813149 | 0.578947 | 0.733333 | 11 | 8 | 283 | 4 |
| synthetic_validation | r06 | 0.906574 | 0.736842 | 0.933333 | 14 | 5 | 286 | 1 |
| synthetic_challenge | V1 | 0.868246 | 0.680000 | 0.850000 | 17 | 8 | 283 | 3 |
| synthetic_challenge | r05 | 0.877713 | 0.708333 | 0.850000 | 17 | 7 | 284 | 3 |
| synthetic_challenge | r06 | 0.887577 | 0.739130 | 0.850000 | 17 | 6 | 285 | 3 |

Context-v4/lexicon/target-v4/repeated-v4 giữ nguyên. Raw score, context_tags, lexical_signals, reply_to_user_id, directed_at_user_id, policy risk và advisory lưu riêng trong prediction/hybrid outputs. Policy không thực thi visibility; không tự ẩn. Hybrid gains không phải classifier gains và không có nhãn tham khảo trong request phân tích.

## Phân nhóm và lỗi còn lại

Toàn bộ Accuracy/Macro-F1/P/R/confusion theo nhóm nằm trong comparison.json; dưới đây giữ số lượng sai raw/hybrid của r06 để thấy giới hạn. Sarcasm chỉ là proxy nhóm indirect_attack do tác giả gán, chưa có nhãn sarcasm riêng. Nhóm chỉ có một lớp dùng fixed two-class Macro-F1 nên không diễn giải như benchmark cân bằng; n=0 là thiếu bằng chứng, không phải điểm0.

| Split | Group | N | Raw FP/FN | Hybrid FP/FN |
|---|---|---:|---:|---:|
| synthetic_validation | direct_insults | 12 | 0/3 | 0/1 |
| synthetic_validation | indirect_insults | 3 | 0/1 | 0/0 |
| synthetic_validation | sarcasm | 3 | 0/1 | 0/0 |
| synthetic_validation | teencode | 13 | 1/0 | 1/0 |
| synthetic_validation | apology | 7 | 1/0 | 0/0 |
| synthetic_validation | quote | 0 | N/A | N/A |
| synthetic_validation | intervention | 14 | 0/0 | 0/0 |
| synthetic_validation | self_defense | 15 | 1/0 | 0/0 |
| synthetic_challenge | direct_insults | 14 | 0/2 | 0/1 |
| synthetic_challenge | indirect_insults | 6 | 0/3 | 0/2 |
| synthetic_challenge | sarcasm | 6 | 0/3 | 0/2 |
| synthetic_challenge | teencode | 0 | N/A | N/A |
| synthetic_challenge | apology | 4 | 1/1 | 0/0 |
| synthetic_challenge | quote | 1 | 1/0 | 0/0 |
| synthetic_challenge | intervention | 19 | 5/0 | 4/0 |
| synthetic_challenge | self_defense | 14 | 1/0 | 1/0 |

Teencode mask bản đầu bỏ sót t/m/k/đm/vl. `teencode_reporting_v2.json` sửa riêng bộ lọc báo cáo từ predictions đã lưu, không inference/train mới, không đổi nhãn/score/global metrics. Validation13mẫu phù hợp; challenge0theo bộ lọc này nên chưa có bằng chứng challenge teencode. Giữ nguyên comparison ban đầu để truy vết. Bộ dữ liệu tổng thể có57comment teencode theo heuristic nguồn khác; hai mask không đồng nhất.

| Split | Target đúng/reference | Target P/R | Repeated TP/FP/FN | Repeated F1 |
|---|---:|---:|---:|---:|
| synthetic_validation | 8/15 | 1.0000/0.5333 | 1/0/1 | 0.6667 |
| synthetic_challenge | 9/20 | 1.0000/0.4500 | 0/0/5 | 0.0000 |

Target/repeated giống nhau ở ba model vì rule engine không đổi: validation abstain7/15attack, challenge abstain11/20attack. Repeated challenge bỏ sót cả5event (TP0/FN5); không được tuyên bố đã giải quyết harassment. Ngưỡng/rule target yêu cầu chứng cứ nên nhiều câu công kích vẫn thiếu target; câu có actor-target nhưng không đủ nhiều attack có chứng cứ không tạo repeated event. Head-only training không sửa được dependency này.

### Paired wins/losses và ví dụ

- So V1, synthetic_validation: sửa đúng 11, mới sai 2 bình luận.
  - Mới sai: `SGZ500_0242_C02` referenceCLEAN, score0.4842: “t ngồi thảm được, ghế chiếm chỗ quá”
  - Mới sai: `SGZ500_0358_C04` referenceCLEAN, score0.4123: “Bạn có thể chê món, đừng gọi mình ngu.”
- So V1, synthetic_challenge: sửa đúng 4, mới sai 0 bình luận.
- So r05, synthetic_validation: sửa đúng 11, mới sai 2 bình luận.
  - Mới sai: `SGZ500_0242_C02` referenceCLEAN, score0.4842: “t ngồi thảm được, ghế chiếm chỗ quá”
  - Mới sai: `SGZ500_0358_C04` referenceCLEAN, score0.4123: “Bạn có thể chê món, đừng gọi mình ngu.”
- So r05, synthetic_challenge: sửa đúng 3, mới sai 0 bình luận.

Ví dụ r06 còn sai (không sửa reference):
- `SGZ500_0218_C04` referenceCLEAN, rawTOXIC(0.7627), advisoryCLEAN: “Góp ý mốc thời gian được, đừng gọi tác giả ngu.”
- `SGZ500_0218_C07` referenceCLEAN, rawTOXIC(0.4707), advisoryTOXIC: “Câu này vẫn hạ người dù không có từ tục.”
- `SGZ500_0242_C02` referenceCLEAN, rawTOXIC(0.4842), advisoryTOXIC: “t ngồi thảm được, ghế chiếm chỗ quá”
- `SGZ500_0205_C07` referenceTOXIC, rawCLEAN(0.3771), advisoryTOXIC: “Đầu mày chắc chỉ đủ để đội cái nón thôi.”
- `SGZ500_0218_C06` referenceTOXIC, rawCLEAN(0.3498), advisoryTOXIC: “Chắc người nghe phải có lòng thương lớn lắm mới nghe hết giọng mày.”
- `SGZ500_0265_C02` referenceTOXIC, rawCLEAN(0.0730), advisoryTOXIC: “Xin lỗi đóng thiếu, nhưng khách ngu như bạn mới không biết tự mua thêm.”

## Kiểm thử và toàn vẹn

Pretrain60PASS. Full root lần đầu586PASS/1FAIL do notebook thiếu bootstrap/path theo migration convention; đã sửa notebook, kiểm liên quan17PASS; root587PASS. Bổ sung4test mask teencode, full root cuối591PASS/0FAIL trong52.93giây, một Starlette/httpx deprecation warning. Không sửa nhãn kỳ vọng để PASS; không train lại. Frontend/backend runtime không sửa trong lượt này nên không chạy npm build hay giả nhận test Social cũ là test mới.

Hash audit PASS: 259 file bảo vệ/hash-bound,500canonical+500derived+200legacy thread kiểm tra,27trạng thái task lịch sử giữ nguyên. V1/default/checkpoints r03/r04/r05/testsplit/SQLite giữ nguyên. Xem integrity.json. Khóa quyền r06 sau một run; general training vẫn false. Sau khi khóa,45test liên quan PASS; dry preflight thực tế BLOCKED vì hết quyền và output đã tồn tại, không chạy optimizer. Checkpoint manifest riêng, artifact index kèm SHA. Không deploy/push, không tự chuyển demo sang r06.

## Trạng thái và tiếp tục

5mốc thực nghiệm hoàn tất: dataset reuse/validation, chuẩn bị train, train thật, comparison/error analysis, tài liệu/checkpoint/progress. T028 independent real vẫn BLOCKED:0/200thread hợp lệ,0human labels, bộ30thread/313comment cũ NOT_FOUND theo audit trước. Collector Wikimedia tiếp tục PAUSED. Không đánh dấu mới T028 DONE hoặc xóa trạng thái DONE lịch sử. Formal T029/T030 real acceptance và kết luận real-world T033 chưa đạt; r06 chỉ EXPERIMENTAL. Không promotion dựa synthetic.

Tiếp theo: human review synthetic nếu cần nâng chất lượng nhãn; regression riêng cho target/repeated còn bỏ sót trước khi thay rule. Real evaluation cần dữ liệu có quyền nguồn, provenance/privacy/leakage kiểm chứng, cùng một người Round1/Round2 và khóa bộ đánh giá. Full GPU fine-tune chỉ sau receipt/resource/config mới được duyệt; notebook hiện chưa chạy. Hướng dẫn tái kiểm và provenance: reports/ai_update/synthetic_experiment_r06_20261103/README.md.
