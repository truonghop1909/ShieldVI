# T008 — Xác thực và dữ liệu người dùng

**Trạng thái:** DONE — auth/users/roles và SQLite migration đã kiểm thử; PostgreSQL server chưa kiểm chứng.  
**Phụ thuộc:** T007

## Mục tiêu
Tạo dịch vụ FastAPI social-api độc lập, migration DB và bảo mật xác thực.

## Phạm vi và việc cần làm
- Khởi tạo backend mới `services/social-api/` có app factory, env config.
- Users/roles, register/login/me, password hashing; token/session an toàn.
- Test quyền auth và không lộ thông tin cá nhân; dùng DB test riêng.
- SQLite dev và thiết kế migration lên PostgreSQL.

## Tiêu chí nghiệm thu
- `pytest` auth pass; không lưu mật khẩu plaintext.
- User thường không gọi được admin route; không hardcode secret.

## Kết quả kiểm thử / thay đổi
Ngày thực hiện: 30/10/2026 (Asia/Saigon). Đã áp dụng skill [shieldvi-social-backend](../../.agents/skills/shieldvi-social-backend/SKILL.md), đọc AGENTS/task/architecture/database/contract/security và quyết định T016.

### Kết quả và quyết định

- Tạo `services/social-api/` trong **V3 root**, theo blueprint T007; package riêng `shieldvi_social`, app factory/env config, không import module AI. Hai cây V3/design docs vẫn ngang hàng.
- Alembic `0001_users`: users/roles/status có constraints/unique; sessions có token hash/FK/expiry; auth_rate_buckets bền qua restart. SQLite test riêng; PostgreSQL optional driver + kế hoạch chuyển DB và SQL migration offline, chưa kết nối PostgreSQL thật.
- Register/login/me/logout; Argon2id salt riêng/rehash; Bearer opaque 256-bit, SHA-256 token lưu DB, TTL mặc định 1h, revoke/logout, role/status server-side mỗi request. Không cần JWT secret, không cookie credential. User response không email/hash, 422 không echo input/password; cap body 16KiB.
- Register mặc định tắt theo T016; test bật riêng trong app fixture và dùng tài khoản giả. Không tạo user thật hoặc bootstrap admin thật. Read-only `/api/v1/admin/access` kiểm chứng user/moderator bị 403, admin 200; không cấp quyền qua API/client.
- CORS allowlist, limiter auth DB-atomic theo peer IP/account, TTL cleanup, Retry-After; dev uvicorn tắt proxy headers. Snapshot dependency riêng, không đổi venv/dependency V3.
- Chưa tạo Social Web/post/comment/feed, worker/moderation state runtime; T009 chưa bắt đầu.

### File thêm/sửa

Trong `V3 root/services/social-api/`:

- `pyproject.toml`, `requirements-dev.lock`, `.env.example`, `.gitignore`, `README.md`, `alembic.ini`.
- `src/shieldvi_social/{__init__,config,db,models,security,schemas,dependencies,rate_limit,routes,middleware,main}.py`.
- `migrations/env.py`, `migrations/script.py.mako`, `migrations/versions/0001_users.py`.
- `tests/conftest.py`, `test_auth.py`, `test_permissions.py`, `test_migrations.py`, `test_limits_config.py`.
- `.venv/` mới chỉ cho service; dependency phát triển đã cài theo snapshot, không chứa Torch/Transformers.

Trong design root: cập nhật task T008 này, `docs/architecture/API_CONTRACT.md`, `docs/architecture/DATABASE.md`, `docs/CHANGELOG.md`; thêm `contracts/social-auth.openapi.json` sinh từ server thật và `docs/baseline/T008/` (test/dependency/smoke/integrity/source manifest). Không sửa source/static/DB/checkpoint V3 hiện có. `git status` ở cả hai cây vẫn báo không có Git repository, nên chưa có Git diff/commit; review qua file list/manifest.

### Lệnh và bằng chứng thật

Từ service root:

```powershell
& ./.venv/Scripts/python.exe -m pytest -v -p no:cacheprovider
& ./.venv/Scripts/python.exe -m pip check
```

Từ V3 root, `STORE_SUMMARIES=0`:

```powershell
& ./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
```

| Kiểm chứng | Kết quả | Evidence |
|---|---|---|
| Auth/users/RBAC/privacy/rate limits/migration | **47 passed, 1 warning**, 6.67s, exit 0 | [social-pytest.txt](../../docs/baseline/T008/social-pytest.txt) |
| V3 regression | **111 passed, 1 warning**, 1.40s, exit 0 | [legacy-pytest.txt](../../docs/baseline/T008/legacy-pytest.txt) |
| Dependency check | No broken requirements, exit 0 | [dependency-check.txt](../../docs/baseline/T008/dependency-check.txt) |
| CLI migration + uvicorn factory thật trên loopback/port tạm | Upgrade head exit 0; health/OpenAPI 200; không tạo user | [live-smoke.txt](../../docs/baseline/T008/live-smoke.txt) |
| Hash baseline V3 | 68/68 file T007 không đổi | [legacy-integrity.json](../../docs/baseline/T008/legacy-integrity.json) |
| PostgreSQL | Offline SQL compile pass trong tests; server/data migration CHƯA CHẠY | Test migration |
| Frontend build | CHƯA CHẠY lại: không đổi frontend, chưa có app frontend mới trong T008 | Baseline T007 |

Tests bao gồm duplicate case-insensitive/concurrent register, Argon2 hash/salt/rehash, session expiry/revoke/restart/suspend, role escalation và hạ quyền, không chọn user khác qua me, config/CORS, oversized/malformed input redaction, rate limit persisted qua restart/IP/account/window reset, FK/check constraints, upgrade/no-op/downgrade/re-upgrade/schema drift và reject unmigrated DB. Các test chỉ tạo dữ liệu giả trên DB tạm, không chạy migration/downgrade DB V3.

Warning hiện có: Starlette TestClient/httpx deprecation. Những lần kiểm tra trước khi hoàn thiện có lỗi dữ liệu test độ dài mật khẩu (chuỗi 12 ký tự không dưới min; chuỗi `short` trùng tên error `too_short`); đã sửa fixture và chạy lại bộ cuối ở trên, không hạ yêu cầu validation.

### Giới hạn/bàn giao

Service chỉ cho local/private demo: chưa public hardening/email verification/password reset/refresh hoặc admin provisioning workflow; không claim production-ready. Role thay đổi trong tests bằng fixture DB, chưa có API quản trị user. Rate limit fixed-window có burst ở biên, không thay edge DDoS limit; request sai schema chưa vào limiter. PostgreSQL thật, browser auth UX và tải thực chưa kiểm chứng. Retention và mở Internet cần chốt trước production theo T016. T009 sẽ thêm post/comment/reply/feed trên DB này, không sửa AI V3.
