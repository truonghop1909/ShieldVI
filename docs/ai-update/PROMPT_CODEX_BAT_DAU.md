> Chỉ là prompt mẫu cho lần được giao task sau; không thực hiện T020 trong lần gộp này. Đường dẫn trong prompt tính từ root tài liệu.

# Prompt ngắn dùng ngay trong Codex VS Code

```text
Đọc AGENTS.md, tasks/moderation-ai/TASK_ORDER_AI.md và skill $shieldvi-ai-upgrade.
Chỉ thực hiện T020 (kiểm kê và chốt baseline AI); xác định đúng service đang chạy, không sửa mô hình, không train, không đọc toàn repo.
Chạy test baseline nếu môi trường cho phép; ghi kết quả vào task và TASK_ORDER_AI.md. Báo cáo ≤120 từ: file, test, blocker, task kế tiếp. Không tự làm T021.
```

**Prompt các lần sau**:

```text
Làm T0XX theo AGENTS.md + skill $shieldvi-ai-upgrade. Chỉ đọc/sửa file liên quan; test, cập nhật task và TASK_ORDER_AI.md; không in code/log dài; báo cáo ≤120 từ. Dừng sau task này.
```

**Prompt đặc biệt trước training**:

```text
Đọc T029 và docs/ai-update/03_EXPERIMENT_PLAN.md. Chỉ chuẩn bị kế hoạch/Colab; chưa chạy train, chưa download dữ liệu, chưa thay checkpoint. Báo chi phí tài nguyên, dữ liệu sử dụng, đường dẫn output ứng viên; chờ tôi duyệt.
```
