# T023 — Lexicon VI–EN teencode expansion

- **Status:** DONE
- **Priority:** P0
- **Dependencies:** T021
- **Owner:** Codex đề xuất code, người dùng duyệt
- **Scope:** cập nhật AI ShieldVI, không phải tự động bật xử phạt

## Mục tiêu

Nâng từ điển theo normalization có kiểm soát, chống false positives và không trộn dấu hiệu từ tục vào nhãn model.

## Các bước triển khai

1. Audit regex hiện có, rule IDs và false-match; giữ version `lexicon_version`.
2. Hỗ trợ `n0ob`, `l0ser`, `sh1t`, `f.u.c.k`, `f*ck`, `d.m`, `djt`, `vkl`, `NPC`, `cringe af`, `fake artist`... song song với biến thể không dấu, viết tắt, unicode, kéo dài ký tự.
3. Group: profanity, directed_insult, ambiguous_slang, quote_or_report; rule outputs gồm matched span/form, canonical, language, strength, provenance.
4. Test boundary chống match `dm` trong email/domain/word, `NPC` khi thảo luận game, `fake artist` trong việc dẫn lời, câu `đm máy hết pin` không thành directed attack.
5. Nếu nhập lexicon bên ngoài, kiểm license, lưu provenance/hash và file text-only; xin duyệt tải; không gộp tất cả làm toxic.
6. Đảm bảo regex chống catastrophic backtracking, matcher không tải mạng lúc runtime.

## Phạm vi file

- Codex **phải xác minh** service thực tế ở `app/` legacy hoặc `services/moderation-ai/`; chỉ tạo/sửa file hợp lý trong đó.
- Test và tài liệu trong `tests/`, `docs/ai-update/`, `datasets/` hoặc service-scoped equivalents.
- Không sửa Social DB, baseline checkpoint, train/test split hay nội dung fixture trừ khi task nêu rõ và người dùng duyệt.

## Kiểm thử / bằng chứng

Unit tests VI/EN/leet/context/benign; verify no changing `toxic_for_moderation`; compare new matches and FP on fixtures.

## Acceptance criteria (Definition of Done)

Thêm slang mới và giảm miss mà không nâng nhãn model/auto-hide; ghi rule list, data provenance, test FP.

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
- 4 new local reviewed slang rules plus vkl; original djt reused after duplicate-alias guard caught attempted duplicate. Offline rebuild reproducible; email/domain and benign NPC protected. No model score/policy changes.
- Files: services/moderation-ai/app/lexical.py, services/moderation-ai/app/data/lexicon/reviewed_rules.json, services/moderation-ai/app/data/lexicon/active.json, services/moderation-ai/app/data/lexicon/candidates.json, services/moderation-ai/app/data/lexicon/manifest.json, tests/test_lexicon_update.py
- Tests: Combined context/regression/lexicon suite: 128 passed, 1 warning
