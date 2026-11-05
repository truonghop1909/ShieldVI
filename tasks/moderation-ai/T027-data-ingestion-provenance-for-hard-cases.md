# T027 — Data ingestion & provenance for hard cases

- **Status:** DONE
- **Priority:** P1
- **Dependencies:** T021,T023
- **Owner:** Codex đề xuất code, người dùng duyệt
- **Scope:** cập nhật AI ShieldVI, không phải tự động bật xử phạt

## Mục tiêu

Xây pipeline dữ liệu phục vụ training candidate; không tự gộp synthetic và nhãn AI vào gold.

## Các bước triển khai

1. Audit datasets ViCTSD, ViHOS, V3/V4 synthetic và bảng 5 thread; ghi nguồn/giấy phép/schema/label semantics.
2. Tạo script idempotent import nguồn được duyệt; validate JSON/CSV, timezone, parent links, Unicode, raw_text preserved.
3. Tạo hard negatives: xin lỗi, quote, can ngăn, chửi cảm thán, phê bình bình thường; hard positives: teencode, indirect insult, directed non-profanity.
4. Dedupe chính xác & near-duplicate (nêu thuật toán/ngưỡng); split theo thread/source trước train; kiểm leakage.
5. Lưu `dataset_manifest.json` (hash, license, seed, model/prompt nguồn synthetic, counts, class balance, reviewer statuses). Báo tỷ lệ mô phỏng.
6. Xuất candidate `train/val/test` *trong vùng dữ liệu mới*, nhưng ViCTSD test V1 phải bất biến; chưa train.

## Phạm vi file

- Codex **phải xác minh** service thực tế ở `app/` legacy hoặc `services/moderation-ai/`; chỉ tạo/sửa file hợp lý trong đó.
- Test và tài liệu trong `tests/`, `docs/ai-update/`, `datasets/` hoặc service-scoped equivalents.
- Không sửa Social DB, baseline checkpoint, train/test split hay nội dung fixture trừ khi task nêu rõ và người dùng duyệt.

## Kiểm thử / bằng chứng

Data validation script + tests (roundtrip/readability, no duplicates/leakage), report summary và rejected rows. Nếu thiếu permission/license => BLOCKED cụ thể.

## Acceptance criteria (Definition of Done)

Có manifest nguồn hợp lệ, split sạch, dữ liệu raw/normalized tách, không đụng test gốc, ready-for-review chứ không tự train.

## Chặn rủi ro / stop conditions

- Nếu thiếu dữ liệu, license, nhãn người kiểm duyệt, checkpoint, GPU hoặc quyền phù hợp: ghi `BLOCKED` + lý do, không giả lập thành PASS.
- Nếu xuất hiện breaking change hoặc metric xấu đi rõ ràng: báo tác động, rollback và xin duyệt.
- Task chỉ `DONE` sau khi có evidence đúng; công việc chưa chạy cần ghi `CHƯA CHẠY`.

## Nhật ký thực hiện (Codex cập nhật)

- Ngày/commit:
- Các file đã sửa:
- Test/command thực tế:
- Kết quả PASS/FAIL/CHƯA CHẠY:
- Metric/số case thay đổi (nếu áp dụng):
- Blocker / rủi ro:
- Task đề xuất tiếp theo:

### Autonomous session 02/11/2026

- Status: DONE
- Local ingest prepared 1645 synthetic NEEDS_REVIEW records, 418 unique normalized texts; raw text preserved, exact/near-duplicate thread components audited. Empty train/validation/test partitions correctly enforce verification/license/development gates; not ready for training.
- Files: scripts/prepare_ai_update_data.py, tests/test_ai_data_ingestion.py, datasets/ai-update/review_v1/dataset_manifest.json, datasets/ai-update/README.md
- Tests: Data ingestion 7 tests passed; timezone-instant guard corrected and checked; all source rows accounted for


## Latest independent-readiness criteria

Historical status/evidence above preserved. Current scoped status: **DONE** — Source/inventory audit, paused collector guard, anonymized quarantine and human review preparation. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/INDEPENDENT_READINESS.md. New criteria never turn missing real/human evidence into DONE. Evidence:574root/177Social/E2E/UI/registry/live smoke PASS; valid real0, no new training.
