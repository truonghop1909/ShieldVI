---
name: shieldvi-ai-upgrade
description: Cải thiện phân tích toxic, context, lexicon, target, repeated harassment và thực nghiệm ViSoBERT cho ShieldVI, bảo toàn baseline.
---
# ShieldVI AI Update

Dùng cho task AI T020–T033 khi được người dùng giao. Việc cài/gộp tài liệu không phải lệnh chạy T020.

## Định vị và đọc chọn lọc
- Root chứa skill cũng là root code/tài liệu `ShieldVI_V3_Hybrid_Review`; xem [bản đồ đường dẫn](../../../docs/ai-update/INTEGRATION_NOTES.md).
- Đọc [AGENTS](../../../AGENTS.md), đúng file task trong [nhóm AI](../../../tasks/moderation-ai), [TASK_ORDER_AI](../../../tasks/moderation-ai/TASK_ORDER_AI.md) và tài liệu trực tiếp liên quan. Không đọc toàn bộ code/dataset hoặc làm nhiều task trong một lượt.
- Trước khi sửa, xác định service/test thật; legacy `app/` là compatibility entrypoint. Không tạo một bản AI implementation khác.

## Phạm vi T028 và phiên autonomous
- Yêu cầu GAME_RANK_30 mới nhất chuyển T028 sang synthetic-only: sinh và kiểm dataset AI, không phụ thuộc REAL/contact hoặc human gold. Nhãn người dùng là reference riêng, không tự thành independent gold. Giữ dữ liệu cũ bất biến; khi sửa context phải kiểm cả công kích mới sau xin lỗi/nhận lỗi và báo suy giảm ở thread khác.
- Khi được giao autonomous T028–T033, tiếp tục các phần độc lập dù REAL bị chặn; bảo toàn dependency còn thiếu và resource/cost/production approval. Xem task nguồn và [tiến độ](../../../tasks/AUTO_PROGRESS.md). Các hướng dẫn một-task mặc định không hủy quyền tiếp tục đã được người dùng cấp trong phiên.

## Current all-task CPU alternative
- Khi người dùng giao chạy hết task và cho phép sửa blocker, T029 hiện là thí nghiệm head-only CPU có giới hạn4threads/900s/cost0, receipt ràng buộc request/config/data; giữ encoder/base/0.41 và không biến quyền này thành paidGPU/fullfine-tune/production. T031 là review candidate bằng local shadow/fallback/rollback; có thể DONE bằng quyết định reject có bằng chứng. Xem task nguồn/AUTO_PROGRESS; không sửa tiêu chí theo kết quả.

## Bất biến và kiểm chứng
- Bảo toàn V1/visobert_toxic_final và threshold 0.41, test split gốc, SQLite và dữ liệu người dùng. Không tự train, sửa threshold hoặc đổi default checkpoint. Baseline thí nghiệm V1 so với default V1.1 còn chờ quyết định trong ghi chú tích hợp.
- Giữ prediction raw độc lập với context/lexicon/target/repeated; Social API sở hữu visibility/audit. Không bật HIGH auto-hold hoặc auto-ban. Xem [contract additive](../../../docs/ai-update/04_API_VERSIONING.md).
- Không hardcode nhãn theo ID hoặc sửa text fixture để pass. [Fixtures](../../../datasets/fixtures/genz_regression/README.md) là synthetic development regression, không phải gold/blind evaluation. Nhãn solo không chứng minh agreement giữa hai người.
- Khi task chạm dữ liệu/đánh giá, đọc [annotation guide](../../../docs/ai-update/02_ANNOTATION_GUIDE.md), [experiment plan](../../../docs/ai-update/03_EXPERIMENT_PLAN.md) và [privacy](../../../docs/ai-update/07_DATA_AND_SECURITY.md); không tune trên test, báo cả wins/losses và giới hạn.
- T029 train, T031 deploy, download/network/API tốn phí hoặc thao tác dữ liệu rủi ro cần ủy quyền phù hợp theo [release gates](../../../docs/ai-update/05_RELEASE_GATES.md). Chỉ đọc [Colab runbook](../../../docs/ai-update/06_COLAB_RUNBOOK.md) khi thực hiện task được giao liên quan.
- Chạy test trong service đúng phạm vi (`python -m pytest -q`); `npm run build` khi thay frontend. Phân biệt mock với inference thật; không log PII. Ghi lệnh, exit code và kết quả thực tế.
- Chỉ cập nhật task/TASK_ORDER_AI theo bằng chứng; không tự sửa task Social. Dừng sau task được giao, báo tối đa 120 từ theo AGENTS.

Skill này được tái lập từ metadata đặt nhầm trong skill tích hợp và các quy tắc nguồn còn nguyên; không phải khôi phục byte của SKILL.md bị thiếu. Xem [báo cáo gộp](../../../docs/ai-update/MERGE_REPORT.md).
