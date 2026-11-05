---
name: shieldvi-architecture-migration
description: Dùng khi kiểm kê repository hoặc di chuyển ShieldVI V3 legacy thành services/moderation-ai và apps/moderation-web theo bước an toàn.
---
# Workflow migration
1. Đọc T007/T015, docs/architecture/MIGRATION.md, git status và test baseline.
2. Không di chuyển code legacy ở T007, chỉ báo cáo kiến trúc và test hiện trạng.
3. Khi đã được duyệt T015, chuyển file ít nhất có thể, có rollback và giữ contract cũ.
4. Update Python imports, module run configs, React build/static paths, Colab notebooks và startup scripts.
5. Chạy pytest/npm build/API smoke sau mỗi thay đổi, ghi failed/blocked rõ ràng.
