# T029 — PREPARED_NOT_TRAINED, 03/11/2026

**Task BLOCKED**, không phải đã train. Người dùng yêu cầu làm theo task và đã chọn dùng nhãn AI của 200 hội thoại, không gán lại. Phần chuẩn bị T029 đã làm; T028 đã chuyển G2-S synthetic; readiness code vẫn kiểm real cũ và chưa đồng bộ, G3/runtime chưa đạt nên không chạy optimizer hoặc CPU fallback.

## Artifact có thể xem và duyệt

- `configs/t029_candidate.json`: cấu hình đề xuất, chưa được duyệt thực thi.
- `scripts/prepare_t029_training.py`: kiểm schema/provenance/hash và làm sạch train với holdout chỉ đọc.
- `scripts/train_t029_candidate.py`: mặc định preflight; cần `--run`, receipt đúng SHA, G2-S theo scope mới và CUDA; code hiện vẫn kiểm G2 real cũ, cần cập nhật/kiểm thử trước khi chạy mới fine-tune. Không đổi default model hoặc xử lý visibility.
- `notebooks/T029_Train_Candidate_Prepared.ipynb`: notebook Colab chưa chạy, cell train còn comment; không có output giả.
- `reports/ai_update/T029/prepared/{train.jsonl,validation.jsonl,manifest.json}`: dữ liệu và audit tại máy hiện tại. Không copy đường dẫn Windows trong manifest này để chạy Colab; notebook chuẩn bị bản mới ở /content/t029_prepared.
- `reports/ai_update/T029/preflight.json`, `base_smoke.json`, `approval_PROPOSED.json`, `pytest.txt`: bằng chứng và receipt đề xuất approved=false.

## Cấu hình đề xuất G3

Base: **ViSoBERT V1 gốc**, path Colab `/content/drive/MyDrive/visobert_toxic_final`; hash V1 đã kiểm trong manifest chuẩn bị. Không tự chọn V1.1/default hiện tại để thay baseline nghiên cứu.

3 epochs tối đa; batch=8, gradient accumulation=2 (effective=16); AdamW LR=2e-5, weight_decay=0.01; max_length=128; seed=20261103; synthetic loss weight=1; full encoder fine-tune, không phải chỉ classifier head. Early stopping patience=1 theo validation Macro-F1 tại ngưỡng **0.41**. Không chọn checkpoint/threshold bằng test. Test scoring dành cho T030 sau khi chốt candidate.

Một GPU Colab do người dùng chọn, giới hạn thời gian train 3.600 giây; phí/runtime chưa biết, không tự mua tài nguyên. Máy hiện tại torch CPU, CUDA unavailable. Runner không chuyển sang CPU để train ngầm. Output mới: `/content/drive/MyDrive/shieldvi_candidates/T029_synthetic200_20261103_r01/`; folder tồn tại thì từ chối ghi đè. Không ghi vào V1, V1.1 hoặc experiment V2 đã có.

## Dữ liệu và leakage đã kiểm

- Train gốc: 6.942; synthetic: 1.994; tổng: **8.936**. Synthetic chiếm **22,31%**, dưới mức đề xuất 25%.
- Giữ riêng 54 UNCERTAIN; không giả nhãn người hoặc đưa synthetic vào blind benchmark.
- ViCTSD validation/test dùng so trùng dưới dạng chỉ đọc; test labels không dùng cho selection/scoring trong bước này. Prepared chỉ có train và bản sao validation, không tạo bản test mới.
- Exact matching sau NFC/casefold/space; near-duplicate char5 Jaccard ≥0.90 cho text ≥40 ký tự. Xóa khỏi train khi trùng holdout, không sửa heldout để hợp thức hóa. Lần chuẩn bị này số bị loại là 0; không chứng minh loại được mọi paraphrase.
- Kiểm thêm synthetic với train gốc: không có exact/near overlap theo ngưỡng trên. Schema/nhãn/provenance và tất cả checksum đầu vào được kiểm. Bản chuẩn bị từ chối ghi đè khi input/output khác hash.

## Chính sách hiện hành và đồng bộ runtime

Theo yêu cầu sửa T028 ngày 03/11/2026, [G2-S](05_RELEASE_GATES.md) cho phép thí nghiệm synthetic với nhãn AI được người dùng chọn dùng; không bắt buộc hội thoại thật hoặc nhãn người. Bộ 200 và bản xuất 1.994/54 là artifact dùng kiểm acceptance T028 mới. Chưa đánh dấu T028 DONE trong lần sửa docs.

Code train_t029_candidate.py hiện vẫn kiểm independent real lock/evaluation_manifest theo logic cũ. Cần cập nhật và test readiness cho protocol G2-S; không đổi training_allowed của manifest real hoặc giả VERIFIED_SOLO để né nhánh code cũ. Config, scripts, prepared artifacts và receipt chưa bị sửa. ViCTSD holdout vẫn là đánh giá lịch sử, không được đổi tên thành fresh real-thread benchmark.

G3 yêu cầu duyệt đúng dataset/base path/hyperparameters/resource/output/stopping. Receipt đề xuất có SHA config và prepared manifest nhưng approved=false/cost_acknowledged=false. Khi được duyệt thật, receipt phải khớp chính xác bản chuẩn bị trên môi trường sẽ chạy. Một cờ READY hoặc một receipt không thay thế kiểm chứng artifact/schema/source hash/leakage theo protocol. Kiểm real lock chỉ thuộc nhánh G2-R tùy chọn; code cần tách nhánh trước optimizer.

Theo task, bước tiếp theo là kiểm acceptance T028/G2-S, đồng bộ runtime và duyệt cấu hình/resource G3. Không bắt đầu T030–T033 hoặc deploy. Quyền dùng nhãn AI đã được lưu, không yêu cầu người dùng gán lại bộ synthetic.

## Lệnh kiểm tra local

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/prepare_t029_training.py --base-model $env:SHIELDVI_V1_CHECKPOINT
.\.venv\Scripts\python.exe -X utf8 scripts/train_t029_candidate.py --base-model $env:SHIELDVI_V1_CHECKPOINT
```

Đặt env tới V1 thực sự đang có trên máy; code không hardcode đường dẫn tài khoản Windows. Lệnh thứ hai chỉ preflight, exit 2/BLOCKED là kết quả chặn đúng, không phải train thành công. Khi gates đạt và approval đúng, Colab notebook mới cho phép bước `--run`; cell có thể chạy network/mount/GPU nên chưa được thực thi trong phiên này.

Runner hiện được kiểm bằng unit/gate tests, chưa có bằng chứng train GPU thật hoặc candidate reload mới. Base V1 forward inference CPU là smoke riêng, không phải optimizer training hoặc đánh giá candidate.
