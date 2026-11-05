# T016 — Chốt chính sách kiểm duyệt bán tự động
**Status:** DONE (thiết kế và kiểm chứng phạm vi T016; chưa duyệt active config/HIGH auto-hold) | **Phụ thuộc:** T007 | **Skill:** `$shieldvi-moderation-policy`

## Mục tiêu
Thiết kế policy 3 mức LOW/REVIEW/HIGH + UNKNOWN; minh bạch trạng thái user, admin offline, rollbacks; không lấy ViSoBERT 0.41 làm luật auto-hide.

## Việc cần làm
1. Đọc `docs/design/03_CHINH_SACH_KIEM_DUYET.md`, `docs/design/04_VONG_DOI_NOI_DUNG.md`, rà code hiện tại.
2. Định nghĩa transitions, quyền actor, các flags trong policy; xây policy config versioned **chỉ khi được duyệt**.
3. Liệt kê data / metric cần xác nhận trước khi bật HIGH auto-hold; chế độ đầu tiên chỉ shadow.
4. Viết test policy cho profanity không mục tiêu, trích dẫn, teencode và model false positive.

## DONE khi
Có decision table, config version, test cases, cấm auto-hide vì 0.41/lexicon; báo các điều chưa thể quyết định do thiếu validation. Không đổi checkpoint.

## Kết quả — 30/10/2026 (Asia/Saigon)

- Đặc tả: [T016_POLICY_SPEC.md](../../docs/architecture/T016_POLICY_SPEC.md), version thiết kế `social-policy-draft-0.2`. Có decision table LOW/REVIEW/HIGH/UNKNOWN, shadow/kill switch, actor transitions, review/job lifecycle, revision/concurrency/idempotency guards, edit/delete/appeal/ancestor visibility và rollback.
- HIGH shadow → PUBLISHED_FLAGGED + queue ưu tiên, không hold; repeated heuristic V3 chỉ REVIEW. UNKNOWN → pending/retry/manual. Không dùng threshold `0.41`/lexicon để tự ẩn hoặc khóa tài khoản.
- Chốt demo local/private, tài khoản thử, nội dung mới pending; edit tăng revision và ngừng public bản cũ; parent chặn descendants bằng effective visibility; không tự restore qua appeal/report/kill switch.
- Đã đọc skill và các docs 03/04/09; rà engine/lexicon/schema V3 qua source và test trực tiếp với predictor giả. Git status tại design root vẫn báo không phải Git repository; không có Git diff/commit, dùng file list và hash baseline để review.
- **Không tạo/sửa active policy config:** task yêu cầu duyệt riêng. Version/flags ở đặc tả là thiết kế, approval/activation null; giữ `moderation_policy.example.json` là draft-0.1 không dùng runtime. Test vectors mới không phải config vận hành.
- Còn mở có chủ đích: HIGH threshold/rule, FP/FN budget/support/CI, dữ liệu gold/quyền dùng, số ngày retention, SLA/public launch. Cần validation và duyệt trước triển khai/kích hoạt; xem mục 8 đặc tả.

### File thêm/sửa

- Thêm `docs/architecture/T016_POLICY_SPEC.md`, `contracts/policy_acceptance_cases.json`, `tests/test_policy_design.py` và `docs/baseline/T016/{policy-tests.txt,legacy-pytest.txt,legacy-integrity.json}`.
- Sửa docs `03_CHINH_SACH_KIEM_DUYET.md`, `04_VONG_DOI_NOI_DUNG.md`, `09_TEST_DANH_GIA.md`, `11_QUYET_DINH_VA_CAU_HOI_MO.md`, `ARCHITECTURE.md`, `DATABASE.md` để thống nhất enum/shadow và ghi quyết định; sửa task T016 này và `docs/CHANGELOG.md`.
- Không sửa runtime/service/frontend/DB/checkpoint V3; không train, không bật auto-hold, không bắt đầu T008.

### Kiểm chứng thực chạy

Python dùng `.venv/Scripts/python.exe` sẵn có của V3. Lệnh từ design root:

```powershell
& ../ShieldVI_V3_Hybrid_Review/.venv/Scripts/python.exe -m pytest tests/test_policy_design.py -v -p no:cacheprovider
```

Lệnh regression từ V3 root, `STORE_SUMMARIES=0`:

```powershell
& ./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
```

| Kiểm chứng | Kết quả thật | Evidence |
|---|---|---|
| Policy design/legacy signals | 17 passed, 0.17s, exit 0 | [policy-tests.txt](../../docs/baseline/T016/policy-tests.txt) |
| V3 regression | 111 passed, 1 warning, 1.35s, exit 0 | [legacy-pytest.txt](../../docs/baseline/T016/legacy-pytest.txt) |
| Hash legacy theo mốc T007 | 68/68 giữ nguyên | [legacy-integrity.json](../../docs/baseline/T016/legacy-integrity.json) |
| Frontend build | CHƯA CHẠY lại; không sửa frontend, baseline T007 có build pass với override | T007 baseline |

Giới hạn: tests dùng score giả, kiểm tra engine/lexicon thật và invariants bảng acceptance, **không phải policy service đã triển khai**. Các ca future integration trong JSON chưa được chạy như DB/API/E2E tests. Real inference, HIGH calibration, DB concurrency/worker recovery/UI chưa kiểm chứng; thuộc task sau. DONE chỉ áp dụng đầu ra thiết kế T016.
