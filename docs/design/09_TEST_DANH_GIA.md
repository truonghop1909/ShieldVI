# 09 — Kiểm thử hệ thống và đánh giá AI

T014/T019 bổ sung [báo cáo kiểm chứng](../archive/implementation_reports/T014_T019_VALIDATION_REPORT.md) và [runbook local](../guides/RUN_LOCAL.md): E2E đủ 4 server + worker, security/privacy/backup và inference CPU thật trên ViCTSD, tách synthetic. T016 [đặc tả policy/state](../architecture/T016_POLICY_SPEC.md), test vectors và `tests/test_policy_design.py` vẫn là bằng chứng invariants thiết kế; runtime T009/T012/T017/T013/T018 được kiểm tra bằng các suite mới. Không coi unit/stub pass là chất lượng AI hay approval bật HIGH.

## A. Phân tách 3 bộ test
1. **Unit:** Social API (auth, validation, state machine), lexicon normalization, policy engine; mocked ViSoBERT.
2. **Integration:** Social API ↔ worker ↔ AI service với fake/stub + test checkpoint thật ở môi trường cho phép; job durability, idempotency.
3. **E2E:** React: đăng bài → comment → xem trạng thái → admin xét → user kháng nghị → restore.

## B. Bảng testcase nghiệm thu bắt buộc
| ID | Tình huống | Kết quả cần kiểm tra |
|---|---|---|
| E01 | Comment bình thường | Tự đăng **sau khi** policy LOW xác nhận |
| E02 | Từ tục không nhắm người (`đm điện thoại hỏng`) | Không tự kết luận HIGH / không auto ban |
| E03 | Teencode (`d.m`, `f.u.c.k`, `sh1t`) | Lexicon phát hiện nếu đã hỗ trợ, lưu reason, không chắc chắn thì review |
| E04 | Xúc phạm trực tiếp | Score/signal có thể được hiển thị, chính sách xử lý theo mức kiểm chứng |
| E05 | Cùng actor công kích lặp lại cùng target | Evidence nhiều comment, không gán target không có căn cứ |
| E06 | Trích dẫn/giải thích từ tục | Không mặc định chặn vì match keyword |
| E07 | AI timeout / 503 | Content+job không mất, hiển thị chờ, worker retry |
| E08 | Worker bị restart | Job recover, không mất/không xử lý hai lần |
| E09 | User không phải author truy cập HELD comment ID trực tiếp | 403/404 có chủ đích, không rò rỉ content |
| E10 | Admin approve comment đang HELD | Comment published, audit reason đầy đủ |
| E11 | Job cũ trả muộn sau admin approve | Không ghi đè trạng thái human decision |
| E12 | User report, appeal và admin restore | Audit đầy đủ, phản hồi trạng thái đúng |
| E13 | Sửa body sau khi có AI score | Tạo revision/job mới, không dùng score cũ |
| E14 | Hai người duyệt cùng nội dung | Conflict 409 hoặc optimistic concurrency |
| E15 | Người dùng gửi HTML/script trong comment | React escape, không XSS |
| E16 | Feed pagination lớn | Không trả item chưa public, latency chấp nhận được |
| E17 | Reviewer reload Dashboard | Không mất nhãn/decision, SQLite tồn tại |
| E18 | Mọi endpoints V3 legacy | Regression test không bị ảnh hưởng |

## C. Đánh giá chất lượng AI
- Baseline ViSoBERT V1, threshold hiện tại `0.41`; hệ thống Hybrid lexicon là nhánh bổ sung.
- So sánh trên **cùng tập đánh giá**: comment-level Precision, Recall, Macro-F1, confusion matrix; thêm lexicon hit rate, False Positive trên câu clean và teencode recall.
- Target detection: precision/recall trên actor→target có người gán nhãn, báo riêng unknown.
- Repeated harassment: F1 theo thread/event, phân tích sai trường hợp tranh luận/troll/trích dẫn.
- Moderation policy: FP khi tạm giữ bình luận vô hại, FN khi cho đăng nội dung nguy cơ cao, tỷ lệ cần review, median queue age, % appeal overturn.
- Tất cả policy thresholds/tinh chỉnh đo trên validation. **Tập test final giữ kín**; không tinh chỉnh dựa trên kết quả test.

## D. Nguồn dữ liệu và độ tin cậy
- ViCTSD test dùng riêng cho nhiệm vụ độc hại từng bình luận; ViHOS span labels không gộp trực tiếp vào cùng gold.
- Thread V3/V4 AI sinh là **synthetic**, dùng regression/demo/hard-case; không tuyên bố là hiệu năng trên mạng xã hội thật.
- 30 thread Wikipedia pilot có nhãn AI gợi ý không phải gold độc lập.
- Nếu chỉ một người gán nhãn, ghi rõ single-reviewer; tự kiểm tra sau thời gian khác không tương đương 2 independent annotators.

## E. Performance/SRE
- Đo thời gian `POST /comments` không chờ model; đo queue lag, retry attempts, AI latency, xử lý batch hợp lệ, số job FAILED.
- Fault injection tắt AI 10 phút, bật lại, xác nhận không mất nội dung và không có publish nhầm.
- Không công bố con số hiệu năng chưa chạy thực nghiệm; mọi báo cáo kèm command, version, dataset, git commit, timestamp.

## F. Bằng chứng Codex phải nộp
- `pytest` outputs, frontend `npm run build`, API smoke tests, schema/migration và screenshots UI khi có.
- Nếu model thật không có GPU/checkpoint: báo test mocked pass và đánh dấu inference thật chưa kiểm chứng.
