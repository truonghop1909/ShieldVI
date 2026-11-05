# T007 — Khảo sát legacy và chốt kiến trúc

**Trạng thái:** DONE — đạt tiêu chí khảo sát/kế hoạch T007; inference thật và Colab chưa kiểm chứng (xem giới hạn bên dưới).  
**Phụ thuộc:** Không

## Mục tiêu
Xác nhận cấu trúc code V3 hiện tại và kế hoạch tách an toàn.

## Phạm vi và việc cần làm
- Kiểm kê `app/`, `frontend/`, `tests/`, notebook, checkpoint path, routes và DB.
- Xác định nơi social API và moderation AI tương tác, schema/contract.
- Chạy baseline tests/build khi có môi trường; không sửa logic.
- Viết checklist migration từng bước; không move file.

## Tiêu chí nghiệm thu
- Có báo cáo kiểm kê, lệnh chạy test thực tế hoặc blocker.
- Không thay đổi checkpoint, API, DB, frontend runtime.

## Kết quả kiểm thử / thay đổi
- Ngày khảo sát: 30/10/2026 (Asia/Saigon). Báo cáo: [docs/archive/implementation_reports/T007_REPO_BLUEPRINT.md](../../docs/archive/implementation_reports/T007_REPO_BLUEPRINT.md).
- Kiểm kê mã nguồn, toàn bộ route hiện hành, 6 module test/111 cases, 2 notebook, static build, DB và checkpoint paths; manifest SHA-256 68 file tại [source-manifest.json](../../docs/baseline/T007/source-manifest.json).
- Lần khảo sát đầu chưa có `AGENTS.md`; sau khi người dùng bổ sung đã đọc file tại design root và đối chiếu T007. Thứ tự tiếp theo theo hướng dẫn mới: **T016**, rồi các task theo dependencies; chưa triển khai task mới. Đã đọc addendum và skill architecture-migration. Workspace gồm V3 và design docs ngang hàng; `git status --short` tại cả hai báo không phải Git repository; kiểm tra lại design root vẫn cùng kết quả.
- Baseline từ V3 root: `STORE_SUMMARIES=0`, `./.venv/Scripts/python.exe -m pytest -v -p no:cacheprovider`: **111 passed, 1 warning**, exit 0, 1.42s. [Output](../../docs/baseline/T007/pytest.txt). API dùng FakePredictor, không phải inference thật.
- Frontend build đổi outDir sang design baseline: lần đầu fail EPERM `.vite-temp`; retry `npm.cmd run build -- --configLoader runner --outDir ../../ShieldVI_SocialAI_Design_Docs_v1/docs/baseline/T007/frontend-build --emptyOutDir false` **pass**, exit 0. [Lỗi đầu](../../docs/baseline/T007/frontend-build.txt), [retry](../../docs/baseline/T007/frontend-build-retry.txt). Không build đè `app/static`.
- [Smoke](../../docs/baseline/T007/smoke.txt): root/health/recent-disabled/dashboard/assets/OpenAPI/docs/redoc 200 với model path giả không tồn tại; Torch CPU, CUDA False. Real model load/inference, Colab/Drive, browser E2E, clean npm install và summary storage bật **chưa kiểm chứng**.
- Blueprint chốt boundary/DB ownership, ghi khoảng trống contract/context/version/state, checklist đủ 10 bước MIGRATION.md, rollback/gate, và danh sách file dự kiến T008 tại mục 8. Runtime auto-select refined V1.1 approved khác V1 baseline trong thiết kế; giữ nguyên hành vi và threshold `0.41`.
- File sửa: task T007 này. File thêm: `docs/archive/implementation_reports/T007_REPO_BLUEPRINT.md`, `docs/baseline/T007/` (manifest, output baseline, build tách biệt, kiểm tra hash sau baseline). Không tạo service, không di chuyển source, không train/sửa checkpoint/API/DB/frontend runtime. T008 và các task sau **chưa thực hiện**.
