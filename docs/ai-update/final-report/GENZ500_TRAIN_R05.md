# Dataset GenZ500 — requested training r05

Người dùng yêu cầu: “hãy nạp dataset mới để train mô hình đi”. Đã thực sự nạp dữ liệu và train một candidate riêng. Máy chỉ có CPU; đây là **train classifier head**, không phải fine-tune toàn encoder. Base là V1.1 đang được duyệt, khác với hai lần r03/r04 khởi tạo từ V1 gốc.

## Dữ liệu và cấu hình

- Nguồn: datasets/synthetic_conversations/genz_v2 —500hội thoại/5115bình luận, nhãn AI tham khảo, không phải human gold. Giữ nguyên split440train/60development; không đưa development/reference vào train.
- Thực tế nạp 11340dòng = 6942ViCTSD + 4398synthetic đủ điều kiện nhị phân. Loại UNCERTAIN/review theo pipeline hiện có, không sửa nhãn để train. Validation2000dòng gốc giữ nguyên. Chỉ dùng text test để loại rò rỉ, không score hoặc chọn model trên test.
- Max4CPUthreads/900seconds/cost0; LR5e-6,batch64,max3epochs,patience1,seed20261103,syntheticweight0.1,distillation1.0,maxlength128. Encoder giữ cố định; không tải dữ liệu/model, không gọi dịch vụ phí.

## Kết quả train thực tế

- 534optimizersteps/3epochs/474.17seconds. Chọn epoch2 chỉ bằng historical validation. Thay 4tensor classifier; encoder/source/base hash không đổi.
- Đã lưu và nạp lại checkpoint; sai số probe0.0. Threshold0.41. Candidate chưa được kích hoạt hoặc đưa vào UI.

| Model | MacroF1 validation | Toxic precision | Toxic recall | TP/FP/TN/FN |
|---|---:|---:|---:|---|
| original_V1 | 0.763701 | 0.629442 | 0.534483 | 124/73/1695/108 |
| existing_default_V1_1 | 0.760205 | 0.648352 | 0.508621 | 118/64/1704/114 |
| r05_candidate | 0.755418 | 0.646067 | 0.495690 | 115/63/1705/117 |

**Quyết định: REJECT_PROMOTION_KEEP_EXISTING_DEFAULT**. Giữ nguyên tiêu chí: MacroF1 tăng≥0.005, precision/recall không giảm so với cả V1 và V1.1. Một validation screen không tự cho phép promotion; regression/API/shadow của r05 chưa được chạy và không được suy ra từ r03. Không thay mô hình mặc định.

## Kiểm chứng và giới hạn

-42regression liên quan PASS/1knownStarlettewarning trước train. Post-train: optimizer/source hash/reload/validation/integrity checks PASS.31protected artifacts +500GenZ/200legacy/contextfixtures/userreference/validation/test/SQLite không đổi.
- Đây là exploratory reuse của historical validation; tập test đã từng xem ở các thí nghiệm trước, không được gọi là benchmark blind mới. Không có metric test hoặc kết luận cải thiện ngoài đời cho r05.
- Các task DONE trước đây giữ nguyên; ghi thêm lần train được yêu cầu vào T029/TASK_ORDER_AI/TASK_ORDER/AUTO_PROGRESS. Việc hoàn tất train không đồng nghĩa candidate đạt chất lượng.

## File để xem

- [Checkpoint](../../../models/candidates/T029_genz500_head_cpu_20261103_r05/) · [Training report](../../../models/candidates/T029_genz500_head_cpu_20261103_r05/training_report.json)
- [Config](../../../configs/t029_genz500_cpu_head_r05.json) · [Dữ liệu đã nạp](../../../reports/ai_update/train_genz500_r05_20261103/prepared/manifest.json)
- [Validation review](../../../reports/ai_update/train_genz500_r05_20261103/validation_review.json) · [Integrity audit](../../../reports/ai_update/train_genz500_r05_20261103/integrity_audit.json)
- [Tiến độ](../../../tasks/AUTO_PROGRESS.md). Demo vẫn dùng V1.1; muốn thay model cần hoàn tất đánh giá còn thiếu và quyết định riêng.
