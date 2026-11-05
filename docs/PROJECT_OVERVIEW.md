# Tổng quan đề tài ShieldVI

*Cập nhật 05/11/2026; dựa trên repository và bằng chứng đã lưu.*

## 1. Tổng quan

Tên hiện tại trong repository là ShieldVI Social AI; chưa xác minh văn bản phê duyệt tên đồ án. Tên đề xuất: “Xây dựng hệ thống hỗ trợ kiểm duyệt bình luận tiếng Việt gần thời gian thực bằng AI”.

Đề tài xuất phát từ khó khăn phân biệt lời xúc phạm với tranh luận, cảm thán, xin lỗi hoặc trích dẫn. Mục tiêu là phân tích bình luận và ngữ cảnh, cung cấp cảnh báo có bằng chứng; người kiểm duyệt quyết định xử lý. Đối tượng sử dụng gồm người đăng bài, moderator và admin.

## 2. Các hướng có thể lựa chọn

Các mức dưới đây là đánh giá định tính theo nền tảng hiện có.

| Hướng | Độ khó / khả thi | Code tận dụng |
|---|---|---|
| Phân loại độc hại tiếng Việt | Vừa / cao | ViSoBERT, từ điển, evaluator |
| Kiểm duyệt gần thời gian thực | Vừa / cao | Worker, SSE, Social Web |
| Công kích, bắt nạt theo hội thoại | Cao / trung bình | Context, Target, Repeated thử nghiệm |
| Kết hợp AI và quản trị | Vừa / cao | Queue, review, appeal, audit |

Nên kết hợp hướng thứ hai và thứ tư làm trục chính; hướng thứ nhất cung cấp mô hình nền. Hướng ngữ cảnh là phần nghiên cứu, không cam kết phát hiện toàn diện bắt nạt.

## 3. Các yêu cầu chính

- Chức năng: đăng nhập, đăng bài, bình luận/reply; phân quyền, duyệt/ẩn/khôi phục, kháng nghị và lịch sử xử lý.
- AI: xử lý tiếng Việt bằng ViSoBERT và tín hiệu ngữ cảnh; tách điểm độc hại, người nhận reply, mục tiêu công kích và bằng chứng lặp lại. Ngưỡng 0,41 không phải lệnh tự ẩn.
- Dữ liệu: truy nguyên nguồn/quyền sử dụng; chia tập theo hội thoại, chống rò rỉ; giữ UNCERTAIN riêng. Đánh giá Macro-F1, Toxic Precision/Recall và target/repeated riêng. Không gộp nhãn ViCTSD, ViHOS, ViLexNorm tùy tiện.
- Giao diện: Social và Moderator hiển thị rõ trạng thái, toàn văn, bằng chứng; Studio hỗ trợ dataset/gán nhãn. Thích ứng desktop, tablet, mobile.
- Demo/hiệu năng: xử lý bất đồng bộ, retry khi AI lỗi, chống trùng và kết quả cũ; cập nhật SSE. Độ trễ phải đo, chưa cam kết SLA hay tải production.

## 4. Tình trạng triển khai

| Mức độ | Hiện trạng có bằng chứng |
|---|---|
| Hoàn thành local | Social, worker/SQLite, SSE; Moderator review, appeal, audit; có E2E và kiểm tra responsive. |
| Có code và kiểm thử | Studio nhập dữ liệu, hai vòng review, CPU head-only, registry/evaluation; JSON export đã sửa nhưng cửa sổ cũ chưa nhận cấu hình mới. |
| Đang nghiên cứu | r06 và processor v6.2 tách khỏi mặc định; target/repeated còn bỏ sót. |
| Chưa nghiệm thu | T028/T029 formal BLOCKED; T030–T033 PARTIAL do thiếu đánh giá độc lập và điều kiện phát hành. |
| Vướng môi trường | Chín file V1 ngoài repo đang thiếu, cản trở khởi tạo lại đầy đủ Studio. |

Corpus r06 có 500 hội thoại/5.115 bình luận; train dùng 4.398 nhãn nhị phân, encoder đóng băng. Raw Macro-F1: validation 0,8238, challenge 0,8288, đều synthetic reference. Trên NOV10 development, v6.2 đạt Macro-F1 0,719137; target 2/22, repeated 1/8. Các kết quả khác tập/cấu hình không so sánh trực tiếp, không phải human gold hoặc kiểm chứng ngoài thực tế.

## 5. Tính khả thi

Đánh giá chung: **Trung bình**. React, FastAPI, SQLite cùng luồng tích hợp đã có nên phần kỹ thuật local thuận lợi. Phần khó còn lại là nhãn hội thoại thật, độ bao phủ ngôn ngữ và nghiệm thu AI.

Cần khôi phục artifact V1 đúng hash, bổ sung dữ liệu được phép, rà nhãn và chạy lại kiểm thử trước demo. Chưa có kiểm thử tải lớn hoặc điện thoại vật lý; chưa xác minh thời hạn nộp nên không kết luận kịp tiến độ.

## 6. Phạm vi đề xuất

- **Bắt buộc:** ổn định luồng bình luận–AI–moderator–kháng nghị; khắc phục môi trường; chứng minh quyền truy cập, retry, bảo toàn dữ liệu và đánh giá trung thực.
- **Nên thực hiện:** tận dụng công cụ gán nhãn hai vòng, phân tích FP/FN; củng cố so sánh có/không ngữ cảnh, bằng chứng target/repeated và rollback.
- **Tương lai:** đủ 200 hội thoại thật có quyền nguồn và nhãn người để nghiệm thu độc lập; sau đó mới xem xét fine-tune encoder và vận hành quy mô lớn.

## 7. Đề xuất với giảng viên

Chọn tên tại mục 1 và tập trung AI hỗ trợ kiểm duyệt gần thời gian thực có người quyết định. Nền tảng hiện tại phù hợp trình diễn sản phẩm local và thí nghiệm có giới hạn.

Cần xin chốt tên chính thức, phạm vi ngữ cảnh/bắt nạt, yêu cầu dữ liệu thật, tiêu chí đánh giá và thời hạn. Nếu đánh giá độc lập là bắt buộc, phải bố trí nguồn dữ liệu và công sức gán nhãn trước khi cam kết hoàn tất.

*Căn cứ: [phạm vi](design/01_PHAM_VI_MVP.md), [r06](ai-update/final-report/SYNTHETIC_R06_EXPERIMENT.md), [v6.2](ai-update/final-report/CONTROLLED_V62_RESEARCH.md), [tiến độ](../tasks/AUTO_PROGRESS.md), [kiểm tra mới](../reports/download_fix_20261105_verified.json).*

