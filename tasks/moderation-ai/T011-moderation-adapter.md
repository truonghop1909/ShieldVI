# T011 — Tạo API adapter AI

**Trạng thái:** DONE — 130 test V3/adapter pass với predictor giả; inference checkpoint thật chưa kiểm chứng.  
**Phụ thuộc:** T007

## Mục tiêu
Expose endpoint nội bộ cho từng bình luận nhưng giữ nguyên ViSoBERT V3.

## Phạm vi và việc cần làm
- Tạo `/api/v1/moderate/comment` theo contracts, adapter từ predictor/lexical hiện có.
- Không tự kết luận từ tục = toxic; repeated cần context thật.
- Không thay checkpoint, threshold 0.41 hay routes `/api/analyze`, `/api/reviews/*`.
- Rate limit/service authentication nội bộ, validate input và response.

## Tiêu chí nghiệm thu
- Existing pytest hồi quy vẫn pass; contract test pass.
- Test không có checkpoint rõ ràng mock vs actual inference.

## Kết quả kiểm thử / thay đổi
Đã thực hiện 30/10/2026 theo xác nhận của người dùng làm T011 trước T012/T017. Áp dụng skill shieldvi-ai-integration.

- Thêm internal route service auth/rate/payload limit, contract schemas/examples và advisory adapter; bảo toàn /api/analyze, /health, reviews, model selection và threshold 0.41. Không di chuyển app/.
- `V3 root/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider`: **130 passed, 1 warning**, 1.57s. Mốc riêng trước worker: 128 pass. Không checkpoint/fake probabilities trong production fallback; test dùng predictor stub.
- File sửa/thêm, command/evidence và giới hạn: [T012_T017_WORKER_REPORT.md](../../docs/archive/implementation_reports/T012_T017_WORKER_REPORT.md). Real inference/GPU/Colab chưa kiểm chứng. Không train/deploy/sửa checkpoint.
