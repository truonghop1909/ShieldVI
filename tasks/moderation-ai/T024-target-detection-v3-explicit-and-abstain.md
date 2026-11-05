# T024 — Target Detection v3: explicit and abstain

- **Status:** DONE
- **Priority:** P0
- **Dependencies:** T021,T022
- **Owner:** Codex đề xuất code, người dùng duyệt
- **Scope:** cập nhật AI ShieldVI, không phải tự động bật xử phạt

## Mục tiêu

Giảm nhầm target khi parent reply là người khác, cho phép target=null và evidence provenance.

## Các bước triển khai

1. Phân tích input `mentioned_user_ids` đã được platform resolve; mentions trong `text` chỉ thành trusted target sau khi map ID rõ.
2. Chọn target dựa vào cấu trúc lời công kích, reference người được nhắc, lịch sử người nói, author của parent; parent/root fallback chỉ là candidate low, không là confirmed target.
3. Đánh dấu `target_method`, `target_confidence`, `target_evidence`; cho abstain `target_user_id=null` nếu không chắc.
4. Không dùng nhãn gold hoặc bất kỳ trường annotation từ dataset trong inference.
5. Cases: dance c15 U04→U03 không được ép U02; Game U02→U03; Camping U04→U03; quotes, group mention, self reply, third-party reply.
6. Nếu cải tiến target làm đổi API cũ, dùng trường additive và compatibility tests.

## Phạm vi file

- Codex **phải xác minh** service thực tế ở `app/` legacy hoặc `services/moderation-ai/`; chỉ tạo/sửa file hợp lý trong đó.
- Test và tài liệu trong `tests/`, `docs/ai-update/`, `datasets/` hoặc service-scoped equivalents.
- Không sửa Social DB, baseline checkpoint, train/test split hay nội dung fixture trừ khi task nêu rõ và người dùng duyệt.

## Kiểm thử / bằng chứng

Unit tests unknown/null, explicit mention, reply target mismatch, third-party quotes, edge cases. Đo target precision vs coverage sau khi nhãn được rà soát.

## Acceptance criteria (Definition of Done)

Không tự suy actor==target; target confidence thấp phải không bị biến thành repeated alert bảo thủ; giá trị cũ không bị redefined âm thầm.

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
- Separate attack-target inference with mapped textual/platform references, conflict abstention, low parent/history candidates; no legacy target redefinition. Test exposed overly broad addressed-reply cue; restricted to second-person addressee.
- Files: services/moderation-ai/app/target_signals.py, tests/test_target_signals.py
- Tests: pytest target/context/engine: 39 passed, 1 warning

### User-authorized GAME_RANK_30 follow-up

Confirmed DONE status preserved. Context-v2/ACKNOWLEDGEMENT + clause scope, additive reply/attacktarget/assessment/policy fields, exact4attack GAMEevidence and localDashboardV2 updated. Root417PASS,Social177PASS,2browser checks/build/realV1smokePASS; residual GenZ repeated0/7 disclosed. Details: docs/ai-update/CONTEXT_RECOVERY_GAME_RANK_30.md and AUTO_PROGRESS. No labels/checkpoint/0.41/test changes or production deploy.


## CURRENT camping context follow-up — COMPLETE

Pastedcamping30reproduced at actual V1.1:8020/r05:8021; frozen existing AI references, not human gold. General clause patterns + abuse-endorsement disambiguation + APOLOGY_ACCEPTANCE distinguish accepting apology from self-blame. Contextv3/repeatedv4 qualifies grounded context attacks independently of raw0.41, additive attack_instance_basis. Existing target-v3/legacyengine/lexicon unchanged. Actual after:30/30reference labels bothmodels; exact U04→U03evidence[c09,c12,c15,c18], no apology/recovery added; c18notDEFENSE,c25acceptsapology. All rawscores/legacyfields unchanged.

Full540PASS/1warning, UIbuildPASS, servednewUI/actuallegacy+V2API200. Paired890originalV1cachedscores:1improvement/0newlabelerrors/1eventchange/no newCLEAN-reference evidence. Existing developmenterrors remain documented; no freshblind claim.31protected hashes+all datasets/test/SQLite/V1/V1.1/candidates unchanged. No train/promotion/deploy/auto-hide. Prior DONE and r03/r04/r05promotion rejections preserved.

Current report docs/ai-update/final-report/CAMPING_CONTEXT_RECOVERY.md. Evidence reports/ai_update/camping_context_20261103/; currentownedPIDs in demo_after_server_state.json, older demo PID files superseded. RefreshCtrl+F5 at8020or8021 and reanalyze. No other task started.


## Latest independent-readiness criteria

Historical status/evidence above preserved. Current scoped status: **DONE** — Target inference from actual attack clauses and available participant metadata. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/INDEPENDENT_READINESS.md. New criteria never turn missing real/human evidence into DONE. Evidence:574root/177Social/E2E/UI/registry/live smoke PASS; valid real0, no new training.
