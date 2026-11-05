> CURRENT authority: latest PartsA/B/C restore T028-real200 + same human Round1/Round2, currently BLOCKED. Historical synthetic/CPU DONE is preserved, not real acceptance. Wikimedia paused/no more contact questions. No new training or production activation. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/INDEPENDENT_READINESS.md; older scope notices below are historical.

# 02 — Hướng dẫn gán nhãn và quản lý dữ liệu

> Current scope: T028 is synthetic-only/G2-S under the latest user instruction. REAL/contact/human gold is optional G2-R, not a current blocker. AI labels are references, never human gold. See current task files and AUTO_PROGRESS. The superseded banner below is retained as history.
>
> Historical banner, superseded: Current autonomous scope03/11/2026: T028=REAL200 (still0/BLOCKED); synthetic500/G2-S is a separate accepted-AI research dataset, not human/real gold. Independent research T029–T033 may proceed; CUDA/cost/production approvals remain gated. Later scope notes override older synthetic-only T028 wording below. See final-report and current task files.


## T028 hiện hành: nhãn AI cho synthetic (03/11/2026)

AI tự soạn và gán nhãn tham khảo; người dùng đã chọn dùng trực tiếp, không yêu cầu gán lại. Ghi `data_origin=synthetic`, `label_source=synthetic`, `human_gold=false`, manual_review_performed=false; quyết định sử dụng là AI_REFERENCE_ACCEPTED_BY_USER. Tự rà AI không phải VERIFIED_SOLO hay agreement giữa người. UNCERTAIN giữ riêng khỏi nhị phân. Quy trình solo review dưới đây chỉ áp dụng nếu thực sự có người duyệt hoặc mở rộng đánh giá real, không phải acceptance bắt buộc của T028 synthetic.

## Các cột dữ liệu (mức bình luận)

`thread_id,comment_id,user_id,parent_id,text_or_text_ref,source_type,source_url_or_id,split,comment_label,context_tags,target_user_id,target_confidence,attack_instance,review_status,annotator_id,reviewed_at,notes`

- `comment_label`: `CLEAN|TOXIC|UNCERTAIN` theo **một bộ quy tắc nhất quán**, không lấy nhãn model.
- `context_tags`: danh sách nhiều nhãn có thể cùng lúc (`APOLOGY`, `QUOTE`, `SET_BOUNDARY`, `DEFENSE`, `INTERVENTION`, `DIRECT_ATTACK`, `PROFANITY_NON_DIRECTED`, `UNCERTAIN`).
- `target_user_id`: ID người bị tấn công **nếu có đủ bằng chứng**, khác với parent author.
- `attack_instance`: yes/no/uncertain — có một lượt công kích hướng người trong bình luận này không?
- `review_status`: `DRAFT|VERIFIED_SOLO|UNCERTAIN`; một người đánh giá không phải “2 annotators”.
- `source_type`: `synthetic`, `real_licensed`, `real_anonymized`, etc.; giữ ghi chú giấy phép/chấp thuận.

## Quy tắc quan trọng

1. Chửi thề cảm thán không nhắm ai khác lời xúc phạm hướng người.
2. Câu có trích dẫn, thuật lại, xin lỗi, can ngăn không tự động thành TOXIC; nếu lại công kích tiếp thì vẫn TOXIC.
3. Target bắt buộc có bằng chứng văn bản, mention thật hoặc quan hệ rõ; không ép target nếu không chắc.
4. Để chống data leakage: split theo `thread_id`/nguồn và kiểm tra near-duplicate sau chuẩn hóa; không tách ngẫu nhiên từng comment từ cùng thread vào train và test.
5. Dữ liệu từ ViHOS mang nhãn offensive/hateful span, không đồng nhất nhãn ViCTSD; phải mapping và kiểm tra riêng.
6. Dữ liệu sinh bởi AI và nhãn AI dự thảo không được gọi là gold. Sau đánh giá bởi một người, vẫn ghi giới hạn single-annotator.
7. Không dùng cùng một bộ 150 câu vừa sửa rule vừa đo benchmark độc lập. Tạo tập blind evaluation riêng, không đọc/truy cập khi chỉnh heuristic hoặc chọn ngưỡng.

## Quy trình solo review

- Lượt 1: gán nhãn độc lập không nhìn điểm AI, đánh dấu UNCERTAIN khi không chắc.
- Cách tối thiểu vài ngày (nếu có thể) rà soát lại các case khó, ghi lý do đổi nhãn; đây là intra-review consistency, không tính Cohen's Kappa như hai người độc lập.
- Cho phép loại `UNCERTAIN` khỏi metric chính sau khi báo số lượng loại; luôn thống kê số này riêng và phân tích sensitivity.
- Giữ source, license, policy về dữ liệu cá nhân, làm sạch PII và không lưu nội dung nhạy cảm vào logs.

## Tiêu chí chất lượng dataset

JSON/CSV parse pass; ID duy nhất; parent hợp lệ; timezone; không leak giữa splits; metadata nguồn và sha256; tỷ lệ lớp và khó/dễ báo rõ; zero records silently dropped; mọi sửa nhãn có audit.
