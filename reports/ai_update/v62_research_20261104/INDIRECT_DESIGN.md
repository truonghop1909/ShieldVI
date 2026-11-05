# Controlled predicates before final freeze

V6.2 dùng v6.1 làm nguồn semantics ổn định, sửa quote scope trong revision riêng; không monkeypatch global hoặc sửa service mặc định. Orchestrator gọi canonical raw/lexicon engine một lần rồi tính lại context/target/evidence. `research_only=true` được ghi rõ cho output nghiên cứu.

| Nhóm ngôn ngữ | Cơ chế thử nghiệm | Điều kiện không đủ để kết luận attack |
|---|---|---|
| Mỉa mai năng lực | personal_generalized_incompetence: người nhận rõ + đánh giá tổng quát khả năng tự làm | Chê chất lượng một bản dịch/đoạn mã; câu hỏi trình độ đơn thuần chỉ là exploratory trace |
| Câu hỏi tu từ hạ thấp | rhetorical_mind_denigration: ngôn ngữ hạ nhục đầu óc gắn với người | Dấu hỏi, hỏi mục tiêu học tập hoặc phản biện kỹ thuật không đủ |
| Ẩn dụ | dehumanizing_machine_comparison: so người với máy nhai/copy kèm phủ nhận suy nghĩ riêng; humiliating_silencing ghép đuổi im với “phí oxy” | Ẩn dụ chuyên môn, tự trào, ví trí nhớ tốt hoặc “bảng thông số biết đi” chưa adjudicate không tự thành TOXIC |
| Teencode/không dấu | Accent-fold + b/m/u và bounded human-reference cues, kiểm đúng participant | Không chuẩn hóa mọi slang thành lời chửi; unknown target vẫn abstain |
| Việt–Anh | personal_english_devaluation: chủ ngữ người + brainless/pathetic... và biến thể fkn | Tên thư viện, nhân vật được trích hoặc đánh giá sản phẩm không đủ |
| Hành vi→nhân cách | personal_character_absolutism: “kiểu/loại người chỉ biết…” + hành vi tiêu cực | Khiếu nại một hành vi, tố cáo có căn cứ hoặc lời góp ý đơn lẻ không tự thành công kích |

Không có thread/comment ID, câu NOV10 nguyên văn, raw threshold override hay reference lookup trong processor. Các grammar được thiết kế từ phân tích development; NOV10 đã dùng nghiên cứu, không independent. Chưa có quyết định human cho24case; không dùng nhãn mơ hồ để nới rule cho đủ8events.

Mọi match có clause span và normalized span. Content-view giữ danh từ máy/bản dịch để đọc nghĩa; addressee-view mask từ đồng âm có dấu nhằm không coi máy/câu là mày/cậu. Trace ghi rõ view và mapping về NFC; không dùng offset byte hoặc offset NFD gốc như normalized span.

Quote gate kiểm assignment trước dấu mở quote, attribution/reporting, negation/intervention và endorsement ngoài quote. Câu chứa quote không tự CLEAN: predicate ngoài quote được xử lý riêng. Các safe cues gốc về “câu này xúc phạm” vẫn được giữ; suppress một attack trong quote không xóa attack mới ở clause khác.

New predicates cần người nhận ở phạm vi clause, hoặc direct assignment ngoài quote. Negative controls gồm self-reference, product subject, legitimate criticism, apology, negation, reported speech, intervention và pure profanity. Raw TOXIC không tạo target/instance. Target reuse conservative infer_target và v6.1 conflict/history handling; không fallback vào legacy reply recipient. Repeated nhóm theo actor→target, chỉ evidence của instances đã grounded, ít nhất hai timestamp; actor khác không gộp.

Development được đánh giá trên7cohort: old890(V1 cache), Fresh10/NOV10(r06 exports), postfix48/24, NOVaudit24, repeated74(r06 caches). Tất cả dùng nhãn nguồn bất biến. Bản đầu nounmask làm mất2safe cues, đã lưu kết quả thất bại và sửa trước freeze. Hai control content/actor-view ban đầu FAIL, đã sửa coordinate semantics trước freeze; không thay assertion.

V6.2 luôn experimental. Freeze sau controls/regression, trước khi soạn challenge mới; inference challenge một lần, giữ FP/FN/target/evidence errors và không tune sau score. Nếu challenge xấu đi, báo thay vì chọn lại label hoặc checkpoint. Không chọn model/default hay nghiệm thu real từ số synthetic.
