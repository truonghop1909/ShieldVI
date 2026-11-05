# 10 — Kế hoạch thực hiện bằng Codex (một người)

## 1. Cách chạy an toàn
- Bạn làm 1 mình; Codex là công cụ viết và kiểm thử, không phải reviewer thứ hai.
- Mỗi lần giao **một task**; Codex đọc AGENTS.md + docs + task + skill trước khi sửa.
- Không tự `git push`, deploy, train GPU, overwrite checkpoint, tải dữ liệu ngoài chưa duyệt, đổi test split hoặc tự bật HIGH auto-hide.
- Báo trạng thái `TODO/IN_PROGRESS/BLOCKED/DONE` cùng test evidence. Không nói DONE nếu chưa chạy.

## 2. Thứ tự công việc khuyến nghị
| Thứ tự | Task | Kết quả |
|---|---|---|
| 1 | T007 | Kiểm kê mã ShieldVI V3, chốt boundary, baseline test |
| 2 | T016 (mới) | Chốt policy + state machine + các quyết định còn mở |
| 3 | T008–T009 | Social API, DB, auth, post/comment |
| 4 | T010 | Social Web (feed, post, comment, reply) |
| 5 | T011 | AI Adapter, giữ API cũ |
| 6 | T012 + T017 (mới) | Worker, hàng chờ, retry, admin offline |
| 7 | T013 + T018 (mới) | Admin queue, decision, appeal, audit |
| 8 | T014 + T019 (mới) | E2E, AI/policy evaluation, privacy/security |
| 9 | T015 | Chỉ migrate legacy sau khi regression pass |

## 3. Done = có bằng chứng
Task code chỉ DONE khi: chức năng chạy theo acceptance criteria, lint/typecheck (nếu có), test backend, build frontend, cập nhật tài liệu API/schema, không phá legacy, git diff có thể review.

## 4. Kế hoạch 6 chặng cho người làm một mình
- Chặng 1: Chốt thiết kế & baseline.
- Chặng 2: Social API auth/content + SQLite.
- Chặng 3: Social Web.
- Chặng 4: AI integration + worker + policy shadow.
- Chặng 5: Moderation Dashboard + appeal.
- Chặng 6: E2E, phân tích FP/FN, demo, báo cáo.

## 5. Các mốc demo
A. Đăng nhập → đăng bài → bình luận bình thường hiện feed.
B. AI đánh dấu câu chửi trực tiếp; Admin thấy evidence, không nhầm `ai_label` với `visibility_status`.
C. Tắt AI → comment không mất, chờ retry → bật AI → xử lý.
D. Công kích lặp lại có bằng chứng → queue ưu tiên; Admin quyết định và user kháng nghị.
