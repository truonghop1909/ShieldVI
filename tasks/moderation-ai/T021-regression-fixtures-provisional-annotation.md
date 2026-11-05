# T021 — Regression fixtures & provisional annotation

- **Status:** DONE
- **Priority:** P0
- **Dependencies:** T020
- **Owner:** Codex đề xuất code, người dùng duyệt
- **Scope:** cập nhật AI ShieldVI, không phải tự động bật xử phạt

## Mục tiêu

Tạo bộ regression 5 thread/150 bình luận và nhãn context tham khảo được rà soát; không dùng ID đặc thù làm production rules.

## Các bước triển khai

1. Dùng fixtures `datasets/fixtures/genz_regression/*.json` và CSV reference tags; kiểm tra đúng 5×30, 5 người/thread, ID/parent/time hợp lệ.
2. Tạo `tests/fixtures/ai_update/` hoặc vị trí phù hợp; giữ nguyên input. Viết test assertions dựa trên **ngữ nghĩa**: xin lỗi không được thêm evidence; có thể tồn tại attack trước đó.
3. Chuyển các case trong `docs/ai-update/01_FAILURE_CASES.md` thành bảng CSV reviewer-needed; người dùng rà soát `expected_context/target/attack` trước khi dùng như acceptance gold.
4. Tạo counterexamples tự nhiên với “xin lỗi nhưng mày vẫn ngu”, quote + attack, slang trung tính, root fallback sai, multiple mentions, repeated but apology follow-up.
5. Tách tests deterministic rule/contract khỏi integration `real_model` có checkpoint; không assert hardcode score như 0.531 khi dùng mock.

## Phạm vi file

- Codex **phải xác minh** service thực tế ở `app/` legacy hoặc `services/moderation-ai/`; chỉ tạo/sửa file hợp lý trong đó.
- Test và tài liệu trong `tests/`, `docs/ai-update/`, `datasets/` hoặc service-scoped equivalents.
- Không sửa Social DB, baseline checkpoint, train/test split hay nội dung fixture trừ khi task nêu rõ và người dùng duyệt.

## Kiểm thử / bằng chứng

`python -m pytest -q tests/test_ai_regression.py` (hoặc path Codex tạo); report synthetic vs human-verified, không tự xưng gold.

## Acceptance criteria (Definition of Done)

Fixtures pass, nhãn `NEEDS_REVIEW` được giữ nếu chưa duyệt; check bộ counterexamples và không dùng fixture/test để train.

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
- 5 immutable threads validated; 150 NEEDS_REVIEW rows and 21 semantic counterexamples. No gold labels invented; no fixtures copied twice. Initial tmp_path permission/setup errors resolved using workspace basetemp.
- Files: scripts/ai_regression_data.py, tests/test_ai_regression.py, tests/fixtures/ai_update/counterexamples.json, datasets/fixtures/genz_regression/reviewer_needed.csv
- Tests: pytest tests/test_ai_regression.py -q --basetemp reports/ai_update/test_tmp/T021_2: 4 passed, 1 warning
