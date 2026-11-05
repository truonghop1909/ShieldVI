> Đã gộp tài liệu vào root dự án. File này giữ hướng dẫn nguồn để tra cứu; dùng [AGENTS hiện hành](../../../AGENTS.md) và [báo cáo gộp](../merges/REPOSITORY_MERGE_REPORT.md).

# Hướng dẫn áp dụng tài liệu vào ShieldVI V3 trong VS Code

1. Giải nén `ShieldVI_SocialAI_Design_Docs_v1.zip` vào thư mục tạm.
2. Mở thư mục gốc dự án ShieldVI (có `app/`, `frontend/`, `tests/`) trên VS Code.
3. **Gộp** các thư mục `docs/`, `contracts/`, `tasks/`, `.agents/skills/` từ gói tài liệu vào dự án. Nếu trùng file, so sánh trước, không chọn ghi đè hàng loạt.
4. **Không** copy `app/`, `frontend/` hay thay checkpoint. **Không ghi đè** `AGENTS.md` đang có. Gộp `docs/governance/AGENTS_SOCIAL_ADDENDUM.md` vào AGENTS.md nếu chưa có nội dung tương ứng.
5. Trong Codex, dùng prompt từ `docs/archive/legacy_guides/PROMPT_CODEX_TAI_LIEU.md` để chỉ khảo sát dự án T007.
6. Kiểm tra báo cáo T007 trước, sau đó yêu cầu Codex thực hiện T016 (chính sách), rồi T008/T009.

**Giải thích:** bộ ZIP này chỉ là tài liệu thiết kế, ví dụ JSON, tasks, skills. Nó không tạo/khởi động sẵn API hay website mới. Không có dữ liệu thật, mật khẩu hoặc checkpoint đính kèm.
