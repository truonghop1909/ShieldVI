> CURRENT authority: latest PartsA/B/C restore T028-real200 + same human Round1/Round2, currently BLOCKED. Historical synthetic/CPU DONE is preserved, not real acceptance. Wikimedia paused/no more contact questions. No new training or production activation. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/INDEPENDENT_READINESS.md; older scope notices below are historical.

# 03 — Kế hoạch thực nghiệm chuẩn cho AI Update

> Current scope: T028 is synthetic-only/G2-S under the latest user instruction. Bounded local CPU research and isolated review are authorized; paid GPU/full fine-tuning and production are not. r03 promotion was rejected, not the task execution. r04 is validation-only exploratory follow-up with no historical-test rescore. The superseded banner below is retained as history.
>
> Historical banner, superseded: Current autonomous scope03/11/2026: T028=REAL200 (still0/BLOCKED); synthetic500/G2-S is a separate accepted-AI research dataset, not human/real gold. Independent research T029–T033 may proceed; CUDA/cost/production approvals remain gated. Later scope notes override older synthetic-only T028 wording below. See final-report and current task files.


## Câu hỏi nghiên cứu

- H1: tín hiệu context + lexicon + target/repeated **giảm trường hợp cảnh báo sai bằng chứng** so với pipeline V3 cũ; raw ViSoBERT giữ nguyên.
- H2: tăng lexicon teencode bắt thêm dạng lạ nhưng có thể tăng false positives; đo riêng precision của tín hiệu lexicon.
- H3 (tùy chọn sau phê duyệt): fine-tune candidate với hard negatives/toxic teencode có nhãn AI được người dùng chọn dùng (hoặc nhãn người nếu có) có thể cải thiện Macro-F1 độc lập so với V1; **không bảo đảm**.

## So sánh bắt buộc / ablation

| ID | Model | Lexicon | Context | Target/repeated | Mục tiêu |
|---|---|---|---|---|---|
| B0 | V1 gốc (0.41) | V3 gốc | V3 gốc | V3 gốc | baseline bất biến |
| B1 | V1 gốc | Lexicon mới | V3 gốc | V3 gốc | ảnh hưởng lexicon |
| B2 | V1 gốc | V3 gốc | Context mới | V3 gốc | ảnh hưởng context |
| B3 | V1 gốc | Lexicon mới | Context mới | Target+repeated mới | hybrid candidates |
| B4 (optional) | Candidate fine-tune | Các module như B3 | như B3 | như B3 | đo việc thay model thật |

**Cẩn thận:** nếu cả B3 và B4 dùng policy khác nhau, không quy tác động cho mô hình. Giữ configs/threshold/inputs giống nhau.

## Bộ dữ liệu

- Regression: 5 thread / 150 comment synthetic; **development**, không dùng làm test độc lập.
- ViCTSD test V1: cố định, không dùng để tune model hoặc chọn threshold; có nguồn/label phù hợp comment toxicity.
- T028 hiện hành: AI-authored synthetic augmentation, kiểm G2-S và dùng nhãn AI theo quyết định người dùng; không bắt buộc tập hội thoại thật/nhãn người.
- Separate blind real-thread test là mở rộng tùy chọn G2-R; chỉ gọi là độc lập khi thực sự đủ quyền/nhãn/isolation. Không thay điều kiện đó bằng nhãn AI.
- Synthetic training augmentation: tái sử dụng bộ 200 ở training partition, ghi source và tỷ lệ, giữ UNCERTAIN riêng; không trộn cùng near duplicates sang validation/test. ViCTSD historical holdout tiếp tục dùng trong thí nghiệm classifier và không được gọi fresh blind benchmark.

## Metrics

- Comment classifier: Macro-F1, per-class precision/recall/F1, confusion matrix; toxic precision & recall; calibration nếu có.
- Lexicon: match recall trên nhóm teencode đã xác nhận; FP trên benign and quote/apology.
- Context: precision/recall/F1 theo từng tag; do tags có thể chồng nhau, multi-label metrics.
- Target: precision/recall/F1 trên directed comments và tỷ lệ abstain (`target=null`), không chỉ accuracy trên target đã đoán.
- Repeated: event detection precision/recall, đúng actor→target, evidence correctness, false alerts per 100 threads.
- Moderation policy: số REVIEW/HIGH đề xuất, manual review load, wrongly-held cases trong shadow replay, không dùng kết quả synthetic để bật auto-hold.

## Kỷ luật đánh giá

- Chạy B0 và B3 trên **cùng một danh sách example IDs**, không sửa ví dụ khi thấy khó.
- Thống kê paired wins/losses, nhóm lỗi mới và lỗi tồn tại; không chỉ chọn vài ví dụ cải thiện.
- Ghi seed, package versions, source commit, data hashes, config, timestamp, checkpoint path/sha256 nếu khả thi, output path.
- Nếu dùng test nhiều lần để quyết định, không được tiếp tục gọi nó là blind test; ghi evaluation exploratory.
- Nếu thiếu nhãn tin cậy: chỉ báo regression behavior, **không công bố tăng Macro-F1 thực tế**.
