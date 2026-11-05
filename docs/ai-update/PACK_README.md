# ShieldVI AI Update — Codex Task Pack v1

**Mục đích:** cập nhật lớp AI kiểm duyệt ShieldVI theo các lỗi được quan sát trên 5 thread Gen Z (150 bình luận): false positive với lời xin lỗi/tự vệ/can ngăn, bỏ sót slang/teencode, sai đối tượng công kích, sai logic công kích lặp lại. Sau đó **có thể** tạo ứng viên ViSoBERT fine-tune nếu có dữ liệu thích hợp và người dùng duyệt.

**Đây là bộ tài liệu + 5 fixture tổng hợp + mẫu CSV/JSON, không phải mã nguồn đã được cập nhật và không phải checkpoint mới.**

## Chép vào VS Code

1. Giải nén và mở thư mục gốc ShieldVI (nơi có `AGENTS.md` và `tasks/`).
2. Sao chép **nội dung bên trong gói** vào project, **merge** thư mục `tasks/`, `docs/`, `.agents/`, `datasets/fixtures/`, `contracts/` và `templates/`; không xóa các file có sẵn.
3. **Không ghi đè `AGENTS.md` đang dùng.** Gộp các quy tắc trong `AGENTS_AI_ADDENDUM.md` vào `AGENTS.md`, hoặc yêu cầu Codex đọc cả hai file.
4. Dùng prompt ở `PROMPT_CODEX_BAT_DAU.md`. Chỉ chạy **T020** trước.
5. Sau mỗi task, Codex cập nhật `tasks/moderation-ai/TASK_ORDER_AI.md` và file task đó; không tự chuyển sang task tiếp theo.

## Đường dẫn repo: phát hiện, không giả định

Code V3 gốc nằm trong `app/engine.py`, `app/lexical.py`, `app/predictor.py`, `app/schemas.py`, `app/main.py` và `tests/`. Khi đã migrate, chúng có thể nằm ở `services/moderation-ai/`. Codex phải tìm vị trí đang thực sự chạy và test, **không tạo bản AI song song gây xung đột**.

## Quan trọng

- ViSoBERT V1 hiện tại, nhãn CLEAN/TOXIC và threshold 0.41 là **baseline bất biến**.
- `research_synthetic` dùng repeated-rule threshold 0.03 chỉ mang tính nghiên cứu, không dùng tự xử phạt.
- 150 bình luận trong fixture có tag tổng hợp, **không phải gold do người đánh giá độc lập**; cần rà soát trước khi tính metric có ý nghĩa.
- Không hứa các thay đổi sẽ cải thiện Macro-F1. Phải so sánh, báo cả số case cải thiện và số case tệ hơn.
- AI prediction, policy risk và visibility là 3 khái niệm khác nhau. Không bật tự ẩn HIGH chỉ vì model/lexicon.

## Trình tự nhanh

`T020 → T021 → (T022, T023, T024) → T025 → T026 → T027 → T028 → [DUYỆT TRAIN] → T029 → T030 → [DUYỆT DEPLOY] → T031 → T032 → T033`.

Các task T029 và T031 có thể **SKIPPED theo quyết định của bạn**; vẫn có thể bảo vệ kết quả hybrid không fine-tune.

Xem `tasks/moderation-ai/TASK_ORDER_AI.md`, `docs/ai-update/00_READ_ME_FIRST.md` và `docs/ai-update/05_RELEASE_GATES.md`.
