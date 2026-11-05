# Kết quả phiên tự động AI Update — 02/11/2026

Hoàn thành T021–T027 (7 task), T028 BLOCKED (1), WAITING_APPROVAL 0; T020 đã DONE trước phiên. Không còn TODO đủ dependency. Không train, download/upload ngoài, đổi checkpoint/default/0.41, sửa holdout hoặc production deploy.

## Đã thực hiện

- T021: 5 fixture bất biến, 150 dòng NEEDS_REVIEW và 21 counterexamples; không biến nhãn AI thành gold.
- T022: context typed đa nhãn, phân biệt xin lỗi/trích dẫn/tự vệ/can ngăn với công kích mới. Có kiểm thử mixed apology+attack và phản ánh bị chửi.
- T023: 24 lexicon rules nội bộ, thêm leet/slang, giữ provenance/offsets, không match domain/email, không đổi model labels. Không tải nguồn ngoài.
- T024: target candidate theo ID map rõ hoặc reply được address; ambiguity/conflict/root-only có abstain hoặc low confidence; legacy recipient fields không đổi nghĩa.
- T025: evidence v3 theo actor→target, distinct timestamps, context và model threshold; không đưa apology/recovery-only vào evidence. Model raw flags không bị sửa.
- T026: typed /api/v2/analyze, schema mới và UI hiển thị raw/context/target/human authority; tương thích API cũ bằng endpoint riêng.
- T027: 1645 dòng synthetic review, 418 normalized texts; source metadata, raw Unicode, exact/near duplicates và grouped splits. Train/validation/test đều rỗng vì chưa được verify/approve, không gọi dữ liệu sẵn sàng train.
- T028: công cụ metric/gate và manifest đã có nhưng thiếu nguồn real được phép và nhãn người; gate trả BLOCKED/metrics=null. Chặn exact/near-duplicate corpus đã phát triển/train, dữ liệu synthetic, review chưa xác nhận và cohort prediction sai.

## Kiểm thử và giới hạn

- **265 tests passed, 1 warning**, exit 0: [log](../../reports/ai_update/final/pytest.txt), [command/result](../../reports/ai_update/final/pytest_result.json). Warning Starlette/httpx hiện có không sửa dependency.
- Build Dashboard cuối PASS, 1578 modules; artifact ở reports/ai_update/frontend_build_final. Chưa test browser UI; build không ghi vào served static và không phải production deployment.
- Inference CPU thật trên 5 fixture so sánh API v1/v2: raw scores/labels giống nhau; [evidence](../../reports/ai_update/T026/real_smoke.json). Đây là synthetic developer behavior, không phải gold/blind benchmark và không có claim tăng Macro-F1.
- 31 file checkpoint/config/tokenizer, test/validation holdout, fixture gốc và SQLite không đổi hash so với T020. [Guard và source snapshot](../../reports/ai_update/final/session_verification.json).
- **Social API worker vẫn dùng contract/API v1 legacy. Không tuyên bố đã sửa end-to-end Social.** T032 phải chờ T030/T028; v3 evidence hiện phục vụ research API/Dashboard source. [Chi tiết tương thích](V2_COMPATIBILITY.md).
- Git metadata không có; dùng manifests/hashes thay commit. Các lỗi temp-dir/alias trùng/biến local/Unicode phát hiện trong phiên đã sửa trong scope và chạy lại test, không nới assertions.

## Cần để tiếp tục

Người dùng cung cấp hội thoại thật được phép sử dụng/ẩn danh và nhãn solo được xác nhận trên tập blind độc lập. Không lấy synthetic fixtures/100 hội thoại đã train làm independent evaluation. T028 phải đạt gate trước T029/T030; T029 train và T031 deploy vẫn cần duyệt riêng nếu đủ dependency.

[Tiến độ tiếp tục](../../tasks/AUTO_PROGRESS.md) · [Trạng thái máy đọc](../../reports/ai_update/auto_session.json) · [Manifest review](../../datasets/ai-update/review_v1/dataset_manifest.json) · [Gate T028](../../reports/ai_update/T028/evaluation_gate.json)
