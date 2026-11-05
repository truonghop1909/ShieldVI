# ShieldVI V3 — Hybrid Lexical + ViSoBERT + Human Review

Ứng dụng demo cho đồ án *Phát hiện nội dung độc hại và bắt nạt trực tuyến trong hội thoại tiếng Việt*.

## Tính năng V3 mới

Dữ liệu MXH/teencode mới nằm trong **`datasets/`**. Xem [danh mục và đường dẫn
dataset](datasets/README.md): ViLexNorm, ViHOS, ViCTSD local và mẫu hội thoại nói lái
chờ rà soát. Việc nhập dataset chưa thay checkpoint hoặc tự huấn luyện mô hình.

- **ViSoBERT V1** giữ nguyên checkpoint và ngưỡng `0.41` đã chọn từ ViCTSD, không cần train lại.
- **Phát hiện từ tục/từ lóng Việt–Anh** bằng từ điển heuristic bổ sung. Nhận các dạng phổ biến `đm`, `d.m`, `vcl`, `đéo`, `óc chó`, `não tàn`, `f.u.c.k`, `f*ck`, `f**k`, `sh1t`, `b1tch`, `idiot`...
- **Nhận diện từ tục khác với toxic và bắt nạt**: có từ tục **chưa có nghĩa** là xúc phạm ai. Chẳng hạn “đm máy hết pin” là tiếng chửi cảm thán; “f.u.c.k you” có dấu hiệu trực tiếp hơn. Trích dẫn để lên án hoặc xin lỗi là trường hợp có ngữ cảnh cần người đọc.
- Bảng phân tích thêm cột **Từ lóng / tục** và nút lọc. Các tín hiệu được lưu trong `lexical_signals`, với `lexical_review_recommended`, `profanity_detected`, `directed_insult_candidate`. Trường hợp chỉ có tín hiệu từ vựng sẽ chuyển sang **Cần xem xét**, không tự động chuyển thành nhãn toxic của ViSoBERT hoặc bằng chứng bắt nạt lặp lại.
- **Human-in-the-loop review:** chọn `CLEAN`, `TOXIC`, `CHƯA CHẮC`; nhấn **Lưu vào SQLite**. Có nút **Tải nhãn đã lưu** khi trở lại hội thoại. Nút **Xuất nhãn CSV** vẫn có; tab **Thống kê kiểm duyệt** báo TP/TN/FP/FN theo nhãn bạn lưu.

## Tải và chạy bằng Google Colab

1. Giải nén ZIP hoặc lấy notebook riêng `09_ShieldVI_V3_Hybrid_Review_Colab.ipynb` và mở [Google Colab](https://colab.research.google.com/).
2. Nếu `transformers` chưa ở phiên bản **4.57.3**, chạy ô cài thư viện một lần, sau đó **Runtime → Restart session**. **Bỏ qua ô cài đặt** sau restart (tránh nâng lại 5.x). Cảnh báo `gradio`/`diffusers` không nhất thiết ngăn ShieldVI hoạt động.
3. Chạy ô import để tạo `Path`, `drive`, `files`, `time`, `subprocess`, `output` cùng lúc; sau đó upload **`ShieldVI_V3_Hybrid_Review.zip`** khi được hỏi. Không upload ZIP V2 cũ.
4. Build React bằng `npm install` và `npm run build` (Colab cần Internet).
5. Kết nối Drive đang chứa `MyDrive/visobert_toxic_final` và `threshold_config.json`.
6. Notebook dùng `REVIEW_DB_PATH=/content/drive/MyDrive/shieldvi_v3_reviews.sqlite3` để giữ nhãn giữa các phiên. Thực hiện sao lưu CSV thường xuyên; SQLite trên Google Drive mount có thể gặp lỗi I/O hoặc đồng bộ. Khi cần, hãy dùng DB cục bộ rồi xuất CSV/backup Drive.
7. Khởi động backend → mở `/dashboard/` qua Colab iframe hoặc proxy.
8. Nhập JSON tại `examples/DEMO_HYBRID_TEENCODE_EN_VI.json` (được đóng gói) → **Phân tích hội thoại** → chọn bộ lọc **Từ lóng / tục** → xác nhận nhãn → **Lưu vào SQLite** → **Tải nhãn đã lưu** → xem **Thống kê kiểm duyệt**.

> Notebook V3 có đầy đủ imports để tránh lỗi `NameError` thường gặp. Nếu cổng 8000 đang có bản ShieldVI V2, cần dừng server cũ hoặc restart session trước khi chạy V3.

## Chạy trên Windows

Cần Python 3.10+ và Node.js LTS. Giải nén và đứng trong thư mục gốc:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
npm --prefix frontend install
npm --prefix frontend run build
$env:MODEL_PATH="C:\\AI\\visobert_toxic_final"
$env:REVIEW_DB_PATH="C:\\AI\\shieldvi_v3_reviews.sqlite3"
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở **http://127.0.0.1:8000/dashboard/**. Cần `MODEL_PATH` hợp lệ chứa checkpoint V1 thật. Nếu mô hình chưa có, API phân tích trả HTTP 503 thay vì điểm số giả.

## API V3

### Từ điển nội bộ và tín hiệu từ vựng

Bộ dò đọc dữ liệu nội bộ tại `app/data/lexicon/`, không tải Internet trong mỗi lần
phân tích. Ba nguồn được ghim mã commit, lưu giấy phép MIT/CC0-1.0 và thống kê
trong [manifest.json](app/data/lexicon/manifest.json). Chỉ mục đã rà soát được bật;
mục chưa chắc chắn nằm trong hàng chờ, không tự động kích hoạt.

Dashboard hiển thị dạng tìm thấy, từ gốc, ngôn ngữ, nhóm và lý do. Nhóm `ambiguous`
và `other_sensitive` chỉ cung cấp ngữ cảnh; khớp từ không tự gán TOXIC hay thay đổi
điểm/ngưỡng ViSoBERT. Xem [quy trình nhập và rà soát](app/data/lexicon/README.md).

| HTTP | Đường dẫn | Mục đích |
|---|---|---|
| GET | `/health` | Trạng thái ViSoBERT |
| POST | `/api/analyze` | Điểm ViSoBERT + tín hiệu từ vựng + target + repeated |
| POST | `/api/reviews/batch` | Upsert nhãn của người kiểm duyệt |
| GET | `/api/reviews?thread_id=...&reviewer_id=A` | Đọc nhãn đã lưu |
| GET | `/api/reviews/stats` | TP/TN/FP/FN theo nhãn người dùng |
| GET | `/api/reviews/export` | Xuất tất cả nhãn SQLite sang CSV |
| GET | `/api/recent` | Metadata lượt phân tích (nếu bật tùy chọn) |
| GET | `/docs` | Swagger API |

**Ví dụ**: xem `examples/DEMO_HYBRID_TEENCODE_EN_VI.json`.

### Chính sách lưu trữ & giới hạn

- SQLite `human_reviews` chỉ lưu ID hội thoại, ID bình luận, mã người gán, nhãn, điểm và tín hiệu từ vựng — **không lưu toàn văn bình luận**. Cần sử dụng ID đã được ẩn danh.
- Review là nhãn của **một** người; không được gọi là gold độc lập hoặc tính Cohen's Kappa giữa hai người khi không có người thứ hai.
- `lexical_signals` là từ điển quy tắc chưa được đánh giá độc lập; nó bỏ sót biến thể lạ và có thể báo nhầm do viết tắt/ngữ cảnh. Kết quả từ vựng chỉ là tín hiệu kiểm tra, không được dùng để tự phạt người dùng. Ngưỡng `0.03` của profile nghiên cứu mô phỏng không dùng trong kiểm duyệt thực tế.
- API **chưa có đăng nhập, phân quyền, rate limiting**. Chỉ chạy trên `127.0.0.1`, phiên Colab riêng hoặc qua reverse proxy có xác thực. Không công bố link demo với dữ liệu thật.
- `risk_score_heuristic` không phải xác suất đã hiệu chuẩn. Dữ liệu V3/V4 mô phỏng không phải gold thật.

## Kiểm thử

Thử nghiệm huấn luyện lại ViSoBERT, so sánh V1/V1.1 và cách chọn checkpoint được
ghi trong [báo cáo mô hình](models/MODEL_REFINEMENT_REPORT.md). Bản V1 gốc được giữ
nguyên; việc đổi checkpoint cần khởi động lại FastAPI. Kết quả J97 vẫn cần rà soát
ngữ cảnh và chưa có nhãn người duyệt độc lập.

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

Bộ test kiểm tra từ lóng Việt/Anh/teencode, đối chiếu câu vô hại, ranh giới từ,
trích dẫn/xin lỗi, cảm thán không hướng vào ai, nhập dữ liệu offline, nguồn/giấy
phép, giữ nguyên điểm/ngưỡng mô hình và API lưu/đọc/xuất SQLite. Chạy lệnh bên trên
để xem số ca hiện tại. Build Dashboard bằng `npm.cmd --prefix frontend run build`
trên Windows hoặc `npm --prefix frontend run build` trên Linux/Colab.
