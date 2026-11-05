# 06 — Runbook Colab (chỉ dùng nếu T029 được duyệt)

## Môi trường checkpoint baseline

- Checkpoint cũ: `/content/drive/MyDrive/visobert_toxic_final/` (V1, giữ nguyên file gốc).
- Yêu cầu kiểm tra có `config.json`, `model.safetensors`, tokenizer files và `threshold_config.json`, đối chiếu threshold 0.41.
- Môi trường đã chạy trong dự án: `transformers==4.57.3`, `huggingface-hub==0.36.2`, tokenizers `0.22.x`. Colab đôi khi cài Transformers 5.x; sau `%pip install` phải restart và kiểm tra `transformers.__version__`, không nhấn Run all qua ô cài khác.
- Gradio/Diffusers có thể cảnh báo xung đột hub; **không** coi warnings là bằng chứng train thành công. Cần thật sự import/load model và inference smoke.

## Protocol dữ liệu hiện hành

T028 dùng G2-S synthetic research; bộ hội thoại thật/real lock chỉ cần cho G2-R tùy chọn. Giữ G3 phê duyệt resource/config và GPU; script readiness hiện vẫn cần đồng bộ sang G2-S trước khi thực thi. Lần sửa docs không cho phép tự chạy train.

## Trình tự kỹ thuật

1. Mount Drive đúng tài khoản; **read-only logic** đối với folder baseline. Không gọi `save_pretrained` vào path gốc.
2. Kiểm tra GPU/VRAM, package versions, sha256 manifest và split dataset. Fail fast nếu version sai, thiếu train/val, thiếu nhãn/provenance theo protocol được chọn, hoặc có leakage. Với G2-S/T028, nhãn AI được người dùng chọn dùng là hợp lệ cho augmentation, không bắt buộc nhãn người.
3. Load baseline (tokenizer/classifier) và chạy small inference smoke real. Test smoke độc lập khỏi mock.
4. Fine-tune (nếu duyệt) với config/seed/hyperparameters đã lưu, early stopping theo **validation**, checkpoint lưu vào path mới như `/content/drive/MyDrive/shieldvi_candidates/<run_id>/`.
5. Search threshold nếu thực nghiệm có yêu cầu **chỉ trên validation**; giữ baseline 0.41 song song và không tự ghi vào config production. Không dùng test để chọn threshold/epochs/ratio augmentation.
6. Export report/config, confusion matrix, per-class precision/recall/F1, FP/FN examples đã ẩn danh và artifact checksum. Chỉ báo final evaluation sau khi chốt model selection.
7. Rollback plan: ứng viên chưa deploy, default vẫn trỏ V1. Tiết kiệm chi phí: không auto GPU training nếu thiếu approval.

## Khi gặp lỗi pip

Dừng, báo `sys.executable`, `transformers.__version__`, `importlib.metadata.version(...)` và `transformers.__file__`; không âm thầm đổi các thư viện khác hay cài lại toàn runtime vô cớ.
