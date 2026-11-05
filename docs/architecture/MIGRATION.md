# Lộ trình tách ShieldVI V3 không phá hệ thống đang chạy

T015 đã được người dùng yêu cầu sau T014/T019. Canonical AI ở `services/moderation-ai/app`; React nghiên cứu V3 chuyển vào **`apps/moderation-web/legacy-v3`** vì dashboard Social đã tồn tại ở thư mục cha. Root app import bridge và frontend npm wrapper giữ lệnh cũ. Model/dataset/DB không move, không migrate schema DB demo; [báo cáo/rollback](../archive/implementation_reports/T015_MIGRATION_REPORT.md). Các bước dưới đây giữ thứ tự và gate thiết kế ban đầu.

**Không bắt đầu bằng việc chuyển `app/` và `frontend/` ngay.** ZIP V3 thực tế hiện có `app/main.py`, `app/engine.py`, `app/predictor.py`, `app/lexical.py`, `app/database.py`, `app/review_store.py`, `frontend/src/App.jsx`, `tests/`.

1. Ghi nhận `git status` và chạy baseline `pytest`, `npm run build` (nếu môi trường có dependency), lưu output. Nếu thiếu GPU/checkpoint chỉ chạy mocked tests và đánh dấu inference thật chưa kiểm chứng.
2. Tạo thư mục mới `services/social-api/` và `apps/social-web/`; không thay đổi V3 legacy.
3. Xây Social API + auth + post/comment bằng DB riêng và test.
4. Xây Social Web, kết nối Social API; kiểm thử đăng ký, đăng bài, comment, reply.
5. Bổ sung endpoint `POST /api/v1/moderate/comment` trong **AI legacy** theo adapter, giữ `/api/analyze` cũ nguyên vẹn.
6. Thêm worker/job và tích hợp hai API, timeout, retry, mock AI test và test với model thật trên môi trường được phép.
7. Tạo moderation-web dùng API review của Social API, hoặc ban đầu liên kết dashboard V3; tránh hai nguồn quyết định moderation mâu thuẫn.
8. Chạy end-to-end + bảo mật + migration DB; commit theo giai đoạn.
9. **Chỉ bây giờ** chuyển `app/` → `services/moderation-ai/app/`, `frontend/` → `apps/moderation-web/legacy-v3/` (giữ dashboard Social hiện có); cập nhật imports, notebook Colab, scripts, tests, paths; chạy lại đủ test.
10. Đừng tự xóa legacy cho tới khi xác thực API V3 và checkpoint hiện tại chạy được sau migration.

Giai đoạn MVP có thể làm T007–T012 trước, chưa cần app mobile native. React responsive là đủ để demo; sau đó cân nhắc React Native/Expo.
