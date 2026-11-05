# 00 — Phạm vi cập nhật AI cho ShieldVI

## Hệ thống hiện có (căn cứ mã V3 đã cung cấp trước đó)

| Thành phần | Tệp legacy tham chiếu | Hiện tại / rủi ro |
|---|---|---|
| ViSoBERT predictor | `app/predictor.py` | Tokenizer + classifier 2 lớp, batch 16, max_length 128; ngưỡng từ threshold_config.json hoặc 0.41 |
| Context/target/repeated | `app/engine.py` | Dùng prediction threshold và target dựa mention → reply parent → root fallback; repeated nếu nhiều comment cùng cặp actor→target |
| Từ điển | `app/lexical.py` | Regex Việt/Anh và ký tự biến dạng; chưa nhận đầy đủ `n0ob`, `l0ser`, `NPC`, xin lỗi có từ tục |
| API | `app/schemas.py`, `app/main.py` | `/api/analyze`, `CommentOut`, `AnalyzeResponse`; hiện có endpoint review SQLite |
| Regression hiện tại | `tests/test_engine.py`, `tests/test_lexical.py` | Đa phần mock predictor; không chứng minh ViSoBERT thật cải thiện |

**Quan trọng:** Đối chiếu lại workspace thật trước khi sửa; file có thể đã được Codex migrate/thay đổi. Các tên tệp trên chỉ là bản tham chiếu từ ZIP V3.

## 3 tầng kết quả không được nhập nhằng

- `raw_model_prediction`: `toxicity_score`, threshold `0.41`, và `toxic_for_moderation` **giữ nguyên**.
- `analysis_signals`: context categories (APOLOGY, QUOTE, INTERVENTION, DEFENSE, DIRECT_ATTACK, UNCERTAIN), lexicon, target & repeated evidence; có confidence và lý do, không phải nhãn gold.
- `moderation_decision`: policy risk LOW/REVIEW/HIGH/UNKNOWN và visibility do Social API thực thi, có audit. **Không dùng model threshold = policy auto-hold threshold**.

## Định nghĩa hoàn thành

1. Không phá API V3 hoặc Social API adapter; đổi schema additive, test backward compatibility.
2. Các lỗi được giảm trên regression, không nảy sinh lỗi nghiêm trọng trên counterexamples.
3. Có số liệu so sánh trên bộ evaluation độc lập và mô tả giới hạn; nếu chưa có thì không được tuyên bố cải thiện thực tế.
4. Candidate checkpoint, nếu có, chạy độc lập, có rollback, không ghi đè V1.
5. Tất cả nhiệm vụ được ghi trạng thái + bằng chứng test trong `TASK_ORDER_AI.md`.
