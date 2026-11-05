# 07 — Dữ liệu, nguồn và an toàn

- Không đăng dữ liệu người dùng thật lên API LLM hay dataset public nếu chưa có quyền. Giữ nguồn giấy phép rõ ràng, ẩn danh ID, loại bỏ PII trong báo cáo/log.
- ViCTSD là nguồn classification; ViHOS là span-level offensive/hate. Không hợp nhất nhãn 1:1.
- 5 Gen Z threads là synthetic fixtures, **không** mang tính đại diện cho mạng xã hội thật; số 150 là tổng số bình luận, không phải 150 sự kiện công kích.
- Khi sinh thêm synthetic: bắt đầu batch nhỏ, validate, giữ metadata seed/model prompt/license; chống template repetition/duplicates và không để rò vào test.
- Chính sách giải thích được: thuật toán phán đoán đối tượng và repeated chỉ là cảnh báo; có trường `abstain/unknown` và sự can thiệp của người kiểm duyệt.
- Hạn chế attack surface: từ điển chỉ là data, không `eval`, không tự chạy script của nguồn ngoài; kiểm tra license/terms trước khi tải và import.
- Tài khoản thật, JWT/DB secrets, Social moderation logs phải do Social API quản lý và không được đưa vào artifacts thử nghiệm.
