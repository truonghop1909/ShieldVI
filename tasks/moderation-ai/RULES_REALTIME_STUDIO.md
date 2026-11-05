# Common safeguards T034–T043

- Trước khi sửa code, đọc `AGENTS.md`, `tasks/AUTO_PROGRESS.md`, `tasks/moderation-ai/TASK_ORDER_AI.md`, và contracts / task thực tế trong repository; cập nhật đường dẫn/endpoint theo mã nguồn hiện có, không mặc định dự án đã có tên bảng hoặc route đề xuất.
- Không ghi đè V1, ViSoBERT r06, checkpoint cũ, threshold V1 `0.41`, model mặc định, readiness lock hoặc evidence đã khóa. Processor v6.1/v6.2 chỉ ở chế độ nghiên cứu cho đến khi có quy trình nghiệm thu/promotion riêng.
- `toxicity_score` (raw), `moderation_assessment` (advisory), `directed_at_user_id` (target có bằng chứng), `reply_to_user_id` (người nhận reply), `policy_risk` và `visibility` phải là dữ liệu/khái niệm riêng. AI không tự ghi social DB, tự ẩn, tự ban hoặc tự trừng phạt.
- Dữ liệu thử nghiệm và nhãn AI là **synthetic/development**, không phải human gold. T028/T029 formal giữ BLOCKED khi chưa đủ điều kiện; task kỹ thuật mới không thể bỏ qua acceptance criteria cũ.
- Không sử dụng nội dung người dùng thật để huấn luyện mặc định. Chỉ dùng bản ghi có quyền/đồng ý phù hợp, được ẩn danh và có audit. Không dùng challenge đã xem hoặc tập test đã khóa để train/tune.
- Không sử dụng API/GPU có chi phí, tải weights, triển khai công khai, đổi default, migrate DB thật hoặc git push khi chưa được người dùng phê duyệt riêng. Dev/test dùng tài nguyên, dữ liệu và DB cách ly.
- Luôn có test tái hiện, regression, logs và báo cáo thực hiện trung thực; không tự đánh dấu DONE nếu thiếu evidence. Nếu bị thiếu hạ tầng, ghi PARTIAL/BLOCKED kèm nhánh công việc có thể hoàn thành.

Latest user authorization allows automatic local implementation/testing and an eligible bounded CPU Studio smoke, not r07, paid GPU or production. Existing locked files remain a baseline: prefer additive opt-in extensions; do not rewrite any readiness manifest.

## Social Feed v2 source safeguards

- Đọc `AGENTS.md`, task này, code liên quan, `tasks/AUTO_PROGRESS.md` và task order đang có. **Code thực tế là nguồn sự thật**; đường dẫn và API trong task chỉ là gợi ý nếu repo chưa xác nhận.
- Ưu tiên tái sử dụng `services/social-api/`, `services/moderation-ai/`, `apps/social-web/`, `apps/moderation-web/`, `contracts/`, worker và database có sẵn. Không tự làm thêm sản phẩm chat riêng; **demo trung tâm là bài đăng → nhiều nick comment/reply**.
- Giữ nguyên ViSoBERT V1, r06, ngưỡng **0.41**, model/default processor đã khóa, readiness lock; v6.1/v6.2 chỉ experimental/shadow theo cấu hình riêng. Không tự train r07, promote/deploy, auto-hide/ban, reset dữ liệu hay ghi đè bằng chứng.
- Phân biệt `raw_score`, `moderation_assessment`, `policy_risk`, `visibility` và `review_decision`. Social API sở hữu DB/trạng thái hiển thị; AI là advisory.
- Synthetic/development không phải human gold; T028/T029 formal BLOCKED và T030–T033 PARTIAL trừ khi có bằng chứng nghiệm thu thật. Không dùng dữ liệu thiếu quyền, dữ liệu riêng tư hay holdout để train.
- Tự thực thi **trong phạm vi phiên và quyền hiện có**, chạy test thật, lưu evidence, ghi `NOT_RUN` nếu thiếu môi trường. Khi xong task, cập nhật task progress + `AUTO_PROGRESS.md`; tuân thủ giới hạn `AGENTS.md` về số task mỗi lượt. Khi phiên kết thúc phải có checkpoint/resume, không hứa tự chạy nền.

Current user explicitly requests continuation through dependencies, overriding the older one-task-per-turn limit for this session. Paid resources, external data transfer and production changes remain outside scope.
