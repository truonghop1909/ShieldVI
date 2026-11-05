
ShieldVI Social AI — Instructions for Codex
Mục tiêu: xử lý một task mỗi lượt, thay đổi tối thiểu, tiết kiệm token và bảo vệ dữ liệu/mô hình. Chi tiết để trong tasks/, docs/, contracts/, .agents/skills/; không đọc tất cả theo mặc định.
Cấu trúc và ranh giới
- services/social-api/: FastAPI, auth, users/posts/comments, moderation state, sở hữu Social DB.
- services/moderation-ai/: FastAPI, ViSoBERT + lexicon Việt/Anh/teencode + target/repeated; chỉ trả tín hiệu, không ghi Social DB.
- apps/social-web/: React cho người dùng; apps/moderation-web/: React cho Admin.
- contracts/: schema/API liên dịch vụ; tasks/: nhiệm vụ; .agents/skills/*/SKILL.md: quy trình; docs/: thiết kế.
- Legacy app/, frontend/, tests/ vẫn cần bảo toàn. Thư mục mới có thể chưa tồn tại: kiểm tra code thực tế, không suy đoán.
Quy trình một task
1. Đọc đúng file task (tasks/**/Txxx-*.md) và skill liên quan; chỉ đọc tài liệu/source bổ sung khi cần.
2. Kiểm tra file liên quan và git status --short; chỉ sửa trong phạm vi task, không tự làm task khác.
3. Viết/sửa test và chạy kiểm thử liên quan. Chạy suite rộng hơn khi ảnh hưởng lớn hoặc task yêu cầu.
4. Cập nhật task (TODO, IN_PROGRESS, BLOCKED, DONE) kèm file sửa, lệnh test và kết quả thật. DONE chỉ khi đạt tiêu chí nghiệm thu.
5. Hỏi duyệt trước khi thay đổi phạm vi, thao tác tốn tài nguyên hoặc rủi ro. Nếu thiếu môi trường, ghi blocker.
Tiết kiệm token (mặc định)
- Không quét toàn repo hoặc đọc hết task, skill, docs, dataset, logs, checkpoints.
- Dùng tìm kiếm hẹp: rg --files <path>, rg -n '<pattern>' <path>; chỉ đọc đoạn liên quan.
- Không lặp prompt/task, không dán nguyên file, diff hay log dài; chỉ trích phần cần để giải thích lỗi.
- Ưu tiên chỉnh code có sẵn, tránh refactor/boilerplate/dependency ngoài phạm vi.
- Báo cáo cuối tối đa 120 từ, tiếng Việt, mẫu: Đã sửa | Test PASS/FAIL/CHƯA CHẠY | Rủi ro/cần duyệt.
- Tiết kiệm token không được bỏ qua kiểm thử, bảo mật hoặc lỗi quan trọng.
AI, dữ liệu và moderation
- Giữ checkpoint ViSoBERT V1 và ngưỡng dự đoán 0.41; không tự huấn luyện, đổi ngưỡng hay ghi đè checkpoint.
- Phân biệt AI prediction (ai_label/ai_score), policy risk (LOW/REVIEW/HIGH/UNKNOWN) và visibility (PUBLISHED/PUBLISHED_FLAGGED/HELD_FOR_REVIEW/HIDDEN). 0.41 không phải ngưỡng tự ẩn.
- Từ tục/teencode ≠ toxic; toxic ≠ kết luận bắt nạt. Không tự ẩn/khóa tài khoản chỉ vì từ khóa hoặc điểm ViSoBERT.
- Chế độ HIGH auto-hold chỉ được bật sau khi policy được duyệt và kiểm thử FP/FN; lỗi AI phải có retry/trạng thái UNKNOWN. Chính sách chi tiết: docs/design/03_CHINH_SACH_KIEM_DUYET.md.
- Social API quyết định trạng thái hiển thị, ghi audit (actor, thời gian, lý do, policy version), hỗ trợ duyệt lại/kháng nghị. AI API kết nối qua contract có version, timeout/retry; không dùng chung quyền ghi DB.
- Giữ nguyên test split; không dùng test để tối ưu threshold, không coi nhãn AI/tập tổng hợp là gold. Dataset ViCTSD/ViHOS khác định nghĩa nhãn; giữ provenance và license.
Quy tắc an toàn
- Không tự ý tải dữ liệu ngoài, train GPU, gọi API trả phí, deploy, push Git, tạo tài khoản thật, xóa/ghi đè DB, thay tập test hoặc di chuyển/xóa legacy.
- Không chạy lệnh phá hủy (git reset --hard, git clean -fd, xóa dataset/DB), không hardcode secret/token/JWT/đường dẫn cá nhân, không mở CORS * với credentials.
- Bảo vệ dữ liệu người dùng và quyền riêng tư; test/log ưu tiên dữ liệu giả hoặc ẩn danh.
- Migration chỉ sau regression tests và phê duyệt. Không coi mock test là inference thật.
Xác minh
- Backend: python -m pytest -q tại service có test. Frontend: npm run build tại app có package.json, nếu dependency sẵn.
- Không chạy được test/build: ghi CHƯA CHẠY + lý do; không tuyên bố PASS/DONE.
- Thứ tự ưu tiên: T007 → T016 → task tiếp theo theo dependencies trong tasks/README_SOCIAL.md; không thực hiện cả chuỗi trong một lượt.
AI Update T020–T033
- Root dự án thống nhất là thư mục này: tài liệu/task, code và datasets cùng ở `ShieldVI_V3_Hybrid_Review/`. Xem [ghi chú tích hợp](docs/ai-update/INTEGRATION_NOTES.md); không tạo service AI song song.
- Chỉ khi được giao task AI, đọc task đó, [skill AI Update](.agents/skills/shieldvi-ai-upgrade/SKILL.md) và tài liệu liên quan; cập nhật [thứ tự AI](tasks/moderation-ai/TASK_ORDER_AI.md) theo bằng chứng. [Thứ tự toàn dự án](tasks/TASK_ORDER.md) không thay trạng thái các task đã xác nhận.
- Giữ nguyên raw `toxicity_score`/`toxic_for_moderation`; context, lexicon, target và repeated là tín hiệu riêng. Không hardcode nhãn theo comment/thread ID để vượt regression.
- Fixture tổng hợp dùng phát triển không phải blind benchmark; một reviewer không tạo ra inter-annotator agreement.
- T029/T031 và thao tác mạng, tài nguyên hoặc dữ liệu nhạy cảm phải nằm trong phạm vi người dùng đã duyệt; chưa có ủy quyền phù hợp thì dừng để xin duyệt. Không tự train cả CPU lẫn GPU. Xem [release gates](docs/ai-update/05_RELEASE_GATES.md).
- Chạy kiểm thử liên quan trước khi hoàn thành; chỉ build frontend khi sửa frontend. Không đánh dấu DONE hoặc bắt đầu task tiếp theo nếu chưa có bằng chứng/ủy quyền. Báo cáo cuối tiếng Việt tối đa 120 từ.

- Yêu cầu GAME_RANK_30 mới nhất chuyển T028 sang synthetic-only: tự viết dữ liệu/nhãn AI, không cần REAL/contact/human gold. Giữ reference người dùng riêng, không sửa kỳ vọng để pass. Scope cũ là lịch sử; xem task nguồn/AUTO_PROGRESS. Giữ V1/0.41/test độc lập và quyền GPU/cost/production.

- Latest all-task request authorizes the current bounded localCPU head-only experiment (max4threads/900s,cost0) and local shadow/rollback review under revised T029/T031. This session authorization overrides older stop/no-CPU boilerplate within that scope; it does not authorize paidGPU, fullfine-tune or production changes. Keep actual evidence and protected artifacts.

- Latest PartsA/B/C request restores T028 real/human criteria (BLOCKED separately from historical synthetic DONE). Wikimedia paused, no contact questions/fake contact/browser impersonation. Continue safe independent development/preparation; no new training or production activation. Current criteria: tasks/CURRENT_AI_SCOPE.json. Earlier CPU permissions are historical for completed runs.

- Latest attached synthetic-experiment request authorized one hash-bound r06synthetic-only CPUhead experiment(max4threads/900s/cost0), separately from blocked real acceptance. Completed and authorization consumed; no further training authorized. Reuse500/AI labels, no paid API/GPU, no production switch. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/SYNTHETIC_R06_EXPERIMENT.md; real T028 and formal T029/T030 gates remain unmet.
