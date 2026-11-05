# AI tasks T020–T033

**Tích hợp cùng** kế hoạch social trong `tasks/README_SOCIAL.md`, không thay thế. Dùng `TASK_ORDER_AI.md` làm nguồn trạng thái trong phân nhánh AI.

- T020: kiểm kê/checkpoint/test baseline.
- T021: regression 5 threads + annotations provisional.
- T022: context signals.
- T023: lexicon Việt–Anh/teencode.
- T024: target detection v3.
- T025: repeated harassment evidence v3.
- T026: API/schema + UI + policy boundary.
- T027: data ingestion/provenance.
- T028: blind evaluation & solo human review.
- T029: **optional, cần duyệt** fine-tune ViSoBERT candidate.
- T030: paired evaluation/ablation.
- T031: **optional, cần duyệt** model registry/shadow/rollback.
- T032: Social AI integration & offline safety.
- T033: technical report/thesis handoff.

Nếu chỉ cần sửa nhanh các lỗi AI trong Dashboard, làm **T020–T026** trước, không cần T029. Không cập nhật checkpoint V1 hoặc ngưỡng 0.41 chỉ để “pass” bộ 5 thread.
