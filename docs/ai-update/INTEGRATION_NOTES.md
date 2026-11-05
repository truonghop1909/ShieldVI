# Ghi chú tích hợp AI Update

## Root thống nhất sau khi gộp thư mục tài liệu

- Root đang dùng là thư mục chứa [AGENTS](../../AGENTS.md), tasks, docs, contracts, templates, skills, services, apps và datasets này: **ShieldVI_V3_Hybrid_Review/**.
- Mọi đường dẫn repo trong task tính từ root này. Fixture ở `datasets/fixtures/`; dữ liệu train cũ vẫn ở `datasets/raw/`, `datasets/prepared/` và các thư mục vốn có. Không tạo thêm bản fixture đang hoạt động ở nơi khác trong root.
- [Thư mục tài liệu cũ](../../../ShieldVI_SocialAI_Design_Docs_v1/) và [gói AI Update gốc](../../../ShieldVI_AI_Update_Codex_Tasks_v1/) được giữ nguyên làm bản dự phòng; chỉnh sửa tiếp theo chỉ thực hiện trong root thống nhất.
- Xem [báo cáo gộp root](../archive/merges/REPOSITORY_MERGE_REPORT.md). Báo cáo gộp AI Update và manifest trước đó là bằng chứng lịch sử của lần gộp ở root tài liệu cũ.

## Bản đồ tham chiếu runtime (chỉ kiểm tra tồn tại)

| Tham chiếu legacy trong gói | Vị trí implementation hiện tại |
|---|---|
| app/engine.py | [engine.py](../../services/moderation-ai/app/engine.py) |
| app/lexical.py | [lexical.py](../../services/moderation-ai/app/lexical.py) |
| app/predictor.py | [predictor.py](../../services/moderation-ai/app/predictor.py) |
| app/schemas.py | [schemas.py](../../services/moderation-ai/app/schemas.py) |
| app/main.py | [main.py](../../services/moderation-ai/app/main.py) |
| services/moderation-ai/ | [Moderation AI](../../services/moderation-ai) |
| apps/moderation-web/ | [Social moderation UI](../../apps/moderation-web); research UI ở [legacy-v3](../../apps/moderation-web/legacy-v3) |
| tests/test_engine.py, tests/test_lexical.py | [engine tests](../../tests/test_engine.py), [lexical tests](../../tests/test_lexical.py) |

`reports/ai_update/baseline/` và `tests/fixtures/ai_update/` được nêu như output dự kiến của T020/T021, chưa tạo. Các đường `/api/...` là endpoint; `/content/drive/...` là ví dụ Colab; placeholder/glob không phải liên kết file phải tồn tại. `SOURCE_FILE_MANIFEST.json` mô tả đường dẫn tại root gói nguồn, không tại docs/ai-update. Đầu vào AGENTS_AI_ADDENDUM.md được gộp vào AGENTS và skill, không cài thêm bản hướng dẫn trùng; bản gốc vẫn trong source backup. PACK_README giữ nội dung nhập gói gốc để tra cứu lịch sử, không dùng thay chỉ dẫn root thống nhất ở đây.

## Cần người dùng quyết định, chưa tự chọn

1. **Skill nguồn thiếu nội dung:** manifest đòi 2.015 byte nhưng SKILL.md chỉ có 5 byte (`---` và dòng trống). Metadata tên/mô tả AI Update nằm nhầm cuối skill `shieldvi-ai-integration`. Đã chuyển metadata sang skill AI Update hợp lệ, giữ workflow integration. Body mới tổng hợp từ addendum/task/docs còn nguyên; không khẳng định phục hồi nội dung/hàm băm gốc. Người dùng chọn chấp nhận skill tái lập hoặc cung cấp bản gốc để đối chiếu. Nguồn lỗi vẫn nguyên.
2. **Baseline đánh giá và default runtime:** gói mới dùng B0/V1; [báo cáo T015](../archive/implementation_reports/T015_MIGRATION_REPORT.md) ghi default refined V1.1. Giữ cả hai tài liệu; chưa quyết định B0 cho AI Update, chưa đổi default/model/threshold. Người dùng cần xác nhận V1, V1.1 hoặc so sánh cả hai trước task thực nghiệm.
3. **Scope liên service của T026/T032:** yêu cầu có UI/worker/E2E nhưng scope mẫu nói chủ yếu moderation-ai. Chưa sửa task nguồn; khi giao triển khai cần xác nhận rõ module được sửa. Lần gộp không cấp phép sửa Social API/Web/Moderation Web.

Giữ nguyên việc tune threshold chỉ là tùy chọn có duyệt trong kế hoạch thực nghiệm; không cho phép đổi threshold baseline 0.41. Approval train trước đây không được diễn giải là đã thực hiện T029 hoặc được phép chạy task mới trong lần này.
