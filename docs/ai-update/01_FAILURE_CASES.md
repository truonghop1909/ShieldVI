# 01 — Các lỗi quan sát được trong 5 thread Gen Z

Nguồn: người dùng cung cấp đầu ra AI cho 5 thread, mỗi thread 30 bình luận; fixture JSON đặt tại `datasets/fixtures/genz_regression/`.

| Thread (tên ngắn) | Comment | Điểm ViSoBERT đã báo | Dấu hiệu cần kiểm tra | Kỳ vọng *đề xuất* |
|---|---|---:|---|---|
| Game | c08 | 43.5% | `n0ob vl`, nhắm U03 | Nghi công kích; lexicon hiện bắt `vl` nhưng bỏ `n0ob` |
| Game | c11 | 85.8% | `ngu ... l0ser` | Nghi công kích; bổ sung leetspeak `l0ser` |
| Game | c12 | 45.4% | can ngăn lời chửi | Không tính là lần công kích mới |
| Game | c16 | 53.4% | người khác can ngăn | Không tính là lần công kích mới |
| Game | c23 | 53.1% | U02 xin lỗi U03, nhắc lại lời chửi | APOLOGY/QUOTE; giữ raw score, không thêm bằng chứng công kích |
| Game | c24 | 60.8% | U03 ghi nhận lời xin lỗi và nói buồn | DEFENSE/RECOVERY; không coi là tấn công |
| Camping | c17 | 53.2% | U03 nói bị sỉ nhục | SELF_DEFENSE, không thêm bằng chứng tấn công U04 |
| Camping | c23 | 46.7% | đề nghị không dùng lời xúc phạm | SET_BOUNDARY, không là tấn công |
| Camping | c24 | 57.5% | U04 xin lỗi, nhắc lại “thiếu não” | APOLOGY/QUOTE, không thêm lượt công kích |
| Dance | c07 | 33.6% | `nhảy như NPC bị giật lag` | Cần đánh giá là công kích gián tiếp, model gốc CLEAN |
| Dance | c15 | 65.3% | U04 hạ thấp U03, nhưng target suy U02 | Target candidate U03, không tin parent_id đơn lẻ |
| Dance | c23 | 36.7% | U04 xin lỗi, nhắc lại `cringe/NPC` | APOLOGY/QUOTE, không phải tấn công mới |
| Shop | c23 | 15.0% | Shop nhận lỗi và trích “đồ hãm” | Tránh công kích giả do lexicon |
| Fanart | c14 | 72.5% | `m vẽ như đấm vào mắt` | Công kích gián tiếp, từ điển có thể không phát hiện |
| Fanart | c24 | 32.5% | U05 thừa nhận quy chụp và xin lỗi | Không tính công kích mới |

## Nguy cơ khi sửa

- **Không hardcode** `thread_id/cXX` để đổi nhãn. Dùng test theo văn bản và ngữ cảnh khác.
- Bổ sung `APOLOGY` **không được** blanket suppression. Phản ví dụ: “Xin lỗi nhưng mày vẫn ngu” có thể chứa một công kích mới.
- `NPC` có thể trung tính trong game; `l0ser` có thể là tự trào, trích dẫn, tên sản phẩm. Dùng context/uncertainty và false-positive test.
- `parent_id` chỉ là link trả lời, **không đồng nghĩa** target của phát ngôn. `@U03` rõ hơn nhưng vẫn cần phân biệt ai được nhắc tới và ai bị xúc phạm.
- Score do người dùng copy từ Dashboard; không có snapshot model run được xác minh trong bộ tài liệu. Codex cần tái chạy khi có checkpoint thật và ghi phiên bản.

## Cách sử dụng fixture

- Gọi 150 comment này là **regression/development**. Có tag synthetic trong `synthetic_reference_tags.csv`, nhưng không được coi như gold độc lập.
- Yêu cầu người dùng tự kiểm tra nhãn theo hướng dẫn ở `02_ANNOTATION_GUIDE.md` trước khi dùng để tính metric.
- Khi so sánh before/after, luôn lưu `model_score_raw`, `lexical_signals`, `context_signals`, `target_candidate`, `repeated_evidence` riêng biệt.
