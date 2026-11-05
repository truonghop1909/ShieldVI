# Task bổ sung — ShieldVI Social AI

**Các task T001–T006 cũ vẫn giữ tại `tasks/`**. Mỗi task ở đây có trách nhiệm riêng; trạng thái ban đầu là TODO và cần kiểm tra lại code trước khi xác nhận.

| ID | Nhóm | Việc cần làm | Điều kiện |
|--|--|--|--|
| T007 | integration | Kiểm kê legacy, thiết kế boundary/migration | Bắt đầu |
| T008 | social-api | Auth và DB users, roles, security | T007 |
| T009 | social-api | Post/comment/reply/feed APIs | T008 |
| T010 | social-web | Social UI React với auth/feed/post/comment | T009 |
| T011 | moderation-ai | Adapter moderation endpoint, giữ API cũ | T007 |
| T012 | integration | Job worker AI, policy moderation + integration tests | T009, T011 |
| T013 | moderation-web | Hàng chờ, bằng chứng, duyệt, kháng nghị | T012 |
| T014 | integration | E2E/security/deployment tài liệu | T010,T012,T013 |
| T015 | integration | Move legacy sau khi regression tests đã pass | T014 |

Dùng `tasks/<group>/Txxx-*.md`, áp dụng skill `.agents/skills/shieldvi-social-*` hoặc `shieldvi-ai-integration` phù hợp, cập nhật trạng thái và bằng chứng test.

## Bổ sung quyết định kiểm duyệt không cần Admin trực liên tục
| ID | Nhóm | Việc cần làm | Phụ thuộc |
|---|---|---|---|
| T016 | integration | Chốt policy và state machine (nên làm ngay sau T007) | T007 |
| T017 | integration | Durable worker/retry/AI offline | T009, T011, T012 |
| T018 | moderation-web | Admin queue/appeal/audit | T013, T016 |
| T019 | integration | Đánh giá policy, test E2E/security | T012, T013 |

**Ghi chú:** T016 là bước thiết kế cần chốt **trước** khi Codex viết rule auto-hide; không có threshold HIGH mặc định. Xem `docs/design/10_KE_HOACH_CODEX.md`.

## AI Update bổ sung

Giữ nguyên task và trạng thái Social. Xem [TASK_ORDER toàn dự án](TASK_ORDER.md), [thứ tự AI](moderation-ai/TASK_ORDER_AI.md) và [README nhóm AI](moderation-ai/README_AI_UPDATE.md). T020–T033 mới được nhập tài liệu, chưa bắt đầu.
