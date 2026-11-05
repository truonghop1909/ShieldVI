# 03 — Chính sách kiểm duyệt bán tự động

T016 chốt thiết kế MVP tại [T016_POLICY_SPEC.md](../architecture/T016_POLICY_SPEC.md), version thiết kế `social-policy-draft-0.2`. Chưa phải active config, chưa được phép bật HIGH auto-hold. Tài liệu này tóm tắt; dùng đặc tả T016 khi triển khai state/guard.

## 1. Mục tiêu vận hành
Admin **không phải trực 24/24**: nội dung ít rủi ro tự đăng, mơ hồ được theo dõi, nội dung nguy cơ cao có thể tạm giữ theo chính sách đã được kiểm chứng; admin xử lý queue khi có mặt. Tất cả nội dung vẫn được lưu, khôi phục được theo quyền và chính sách lưu trữ.

## 2. Nguyên tắc tách 3 lớp
1. **AI prediction:** `ai_label`/`ai_score`, ngưỡng model hiện tại 0.41 dùng cho dự đoán TOXIC của ViSoBERT V1.
2. **Policy risk:** `risk_tier=LOW|REVIEW|HIGH|UNKNOWN` do policy engine quyết định dựa vào ngữ cảnh, độ chắc chắn, lặp lại, reports và tín hiệu khác. Chưa có thresholds định lượng đã hiệu chuẩn cho HIGH.
3. **Visibility action:** `PUBLISHED|PUBLISHED_FLAGGED|HELD_FOR_REVIEW|HIDDEN` do Social API áp dụng theo **policy version** và/hoặc quyết định của người duyệt.

**CẤM:** `if score >= 0.41: hide()`; `if match_bad_word: hide()`; `if ai_label==TOXIC: ban_user()`.

## 3. Ma trận quyết định dự kiến cho MVP
| Risk tier | Điều kiện mô tả (chưa phải luật cứng) | Hiển thị | Admin |
|---|---|---|---|
| LOW | Không có tín hiệu đáng kể, hệ thống đánh giá đủ tin cậy | PUBLISHED | Không cần xem |
| REVIEW | Mơ hồ, chứa chửi thề không nhắm ai, tranh luận gắt, AI/lexicon bất đồng | PUBLISHED_FLAGGED | Xem theo ưu tiên thấp/qua báo cáo |
| HIGH | Nhánh tương lai cần bằng chứng đã kiểm định; heuristic V3 chưa đủ để tự gán HIGH | Shadow: PUBLISHED_FLAGGED, chỉ đề xuất HELD_FOR_REVIEW | Queue ưu tiên cao, cần phán quyết; auto-hold chỉ sau duyệt riêng |
| UNKNOWN | AI timeout, thiếu dữ liệu, schema error | PENDING_MODERATION / retry | Theo dõi lỗi, hỗ trợ manual review |

Chính sách bắt đầu **chỉ ở chế độ shadow**: ghi đề xuất HIGH nhưng vẫn đăng kèm cờ nội bộ và review thủ công. Repeated candidate V3 là REVIEW ưu tiên cao, chưa phải HIGH. Chỉ sau calibration, test FP/FN và duyệt kích hoạt riêng mới bật tự giữ. Không phải cứ AI báo TOXIC là HIGH.

## 4. Ví dụ
| Văn bản | Tín hiệu | Kỳ vọng |
|---|---|---|
| “Bài này hay.” | Không dấu hiệu | Tự đăng |
| “Đm, điện thoại hết pin.” | Từ tục không nhắm ai | Không kết luận công kích; cho theo dõi nếu policy cần |
| “Mày đúng là đồ ngu.” | Xúc phạm hướng người | Cảnh báo / có thể review, **không tự quy HIGH chỉ vì một bình luận** |
| “f.u.c.k you” | Biến dạng tiếng Anh + hướng người | Cảnh báo đáng chú ý |
| Nhiều lần cùng user công kích cùng target | Evidence từ nhiều comment và parent links | Xét HIGH khi được xác nhận đáng tin cậy |
| “Từ ‘đm’ nghĩa là gì?” | Trích dẫn/giải thích | Tránh nhầm câu giải thích thành tấn công |

## 5. Vận hành khi offline
- Worker tự xử lý các job; admin không cần online.
- Queue được xếp theo độ ưu tiên, thời gian chờ, lượng báo cáo; không thể cam kết thời gian phản hồi khi chỉ có một người quản trị.
- User nhìn thấy trạng thái thật: `Đã đăng`, `Đang chờ kiểm duyệt`, `Đang tạm ẩn`, `Đã được khôi phục`.
- Người khác không thấy nội dung bị giữ; người đăng có thể thấy nội dung và lý do tổng quát, không thấy dữ liệu nhạy cảm của người báo cáo.
- Không có auto-delete vĩnh viễn hoặc auto-ban dựa độc nhất vào model.

## 6. Cấu hình và triển khai chính sách
- Mỗi policy có mã version, chủ sở hữu, changelog và ngày bật; log số lượng tự đăng/giữ/FP/FN.
- Đánh giá offline trên dữ liệu thật được gán nhãn thủ công; đo tác động lên các nhóm teencode, tiếng Anh, viết không dấu, chửi không mục tiêu.
- Phần HIGH là **quyết định cần duyệt thêm trước triển khai**, không mặc định đã khả dụng trong phiên bản V3 hiện tại.
- Có kill switch chuyển hệ thống về `review-only` nếu tỷ lệ cảnh báo nhầm tăng.
- Kill switch chỉ chặn auto-hold mới, không tự công khai nội dung đã bị giữ/ẩn. Các flags, quyền thay policy, gate đánh giá và rollback nằm tại mục 4/8 của đặc tả T016.
