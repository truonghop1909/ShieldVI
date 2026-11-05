# T009 — Post, comment, reply và feed

**Trạng thái:** DONE — CRUD/feed/outbox đã kiểm thử độc lập AI; publish/worker thuộc task sau.  
**Phụ thuộc:** T008

## Mục tiêu
Xây API nghiệp vụ mạng xã hội chạy độc lập với AI.

## Phạm vi và việc cần làm
- CRUD bài viết/bình luận có tác giả, reply theo parent_id cùng post.
- Feed phân trang, validation độ dài, trạng thái moderation.
- Permission tác giả/admin; moderation job lưu transaction cùng comment.
- Tests IDOR, phân trang, parent self-loop, xóa/chỉnh sửa không có quyền.

## Tiêu chí nghiệm thu
- Tạo/đọc/bình luận/trả lời qua HTTP hoạt động trên DB dev.
- Có test auth, permission, bad payload, query size.

## Kết quả kiểm thử / thay đổi
Ngày thực hiện: 30/10/2026 (Asia/Saigon). Áp dụng skill [shieldvi-social-backend](../../.agents/skills/shieldvi-social-backend/SKILL.md), đọc task/AGENTS/contract và state machine T016, kiểm tra service T008 thực tế. Git status ở design/service vẫn không có repository; dùng manifest/file list và evidence để review.

### Chức năng

- CRUD posts/comments, reply parent cùng post, immutable parent/post/author/id và depth tối đa 32. DB composite FK/check chống parent khác post và self-parent; API không cho rewiring nên không tạo cycle.
- GET feed/list phân trang, stable tie-break `(created_at,id)`, page 1–10000/page_size 1–50, total chỉ tính items được phép đọc. Mọi route yêu cầu Bearer; feed chỉ public, private author/staff qua direct GET/list có guard.
- Effective visibility kiểm tra post và mọi ancestor cả direct URL/list; parent ẩn không cập nhật state con, restore không tự restore child hidden. Author đọc được riêng nội dung của mình, không body ancestor người khác. Cờ/risk/review của người khác không lộ ra public response.
- Create luôn PENDING_MODERATION/QUEUED/UNKNOWN, content+job+audit cùng transaction; chưa có AI/worker/approve. Feed mới có thể trống vì nội dung còn pending. Public fixture chỉ ở DB test để kiểm chứng bộ lọc, không có endpoint bypass publish.
- POST bắt buộc Idempotency-Key UUID, dedupe theo author/type và payload hash; 201 create/200 replay resource hiện tại, mismatch 409. Replay sau delete chỉ tombstone; không sinh job/audit trùng.
- Edit chỉ author, expected revision/decision version, tăng revision/version và pending lại, vô hiệu job cũ, tạo job mới. Author delete terminal/soft-delete; admin DELETE nội dung người khác là HIDDEN/REJECTED với reason bắt buộc, không viết lại body. Moderator chỉ đọc private ở task này; workflow quyết định/appeal thuộc task sau.
- Body 1–8000 ký tự Unicode hợp lệ, không NUL/blank, giữ nguyên spelling. Cap content request 128KiB để hỗ trợ JSON escaped Unicode; auth vẫn 16KiB. Mutation rate theo user (mặc định 30/60s), DB content bucket riêng; CORS PATCH/DELETE/Idempotency-Key.
- Audit actor/role/time/reason/entity/revision/version/before-after; không sao chép body cũ. Policy version null vì chưa chọn active policy, không bật auto-hold. Jobs lưu bền/request_id/revision/expected decision, chưa có claim/lease/retry worker T012/T017.

### File thêm/sửa

Trong `V3 root/services/social-api/`:

- Thêm `migrations/versions/0002_content.py`, `src/shieldvi_social/content_schemas.py`, `content_store.py`, `content_routes.py`, `tests/test_content.py`.
- Sửa `src/shieldvi_social/models.py`, `dependencies.py`, `db.py`, `config.py`, `main.py`, `middleware.py`, `tests/test_migrations.py`, `.env.example`, `README.md`.
- Giữ nguyên migration T008; 0002 bổ sung content/outbox/audit/limiter, nâng/downgrade content có test giữ nguyên users/sessions. SQLite content mutation dùng BEGIN IMMEDIATE, PostgreSQL row lock theo post→comment; chưa test PostgreSQL server.

Design root: sửa task T009, `docs/architecture/API_CONTRACT.md`, `docs/architecture/DATABASE.md`, `docs/CHANGELOG.md`; thêm `contracts/social-content.openapi.json` và `docs/baseline/T009/` (test/smoke/hash/source manifest). Không sửa app/frontend/tests/DB/model legacy, không cài dependency mới, không tạo user thật.

### Lệnh kiểm chứng

Từ service root, venv riêng:

```powershell
& ./.venv/Scripts/python.exe -m pytest -v -p no:cacheprovider
```

Từ V3 root, `STORE_SUMMARIES=0`:

```powershell
& ./.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider
```

CLI/live smoke chạy trên loopback port tạm, `SOCIAL_DATABASE_URL` trỏ file tạm, đăng ký chỉ bật cho tài khoản synthetic trong DB này. `alembic upgrade head`, uvicorn factory và HTTP register/login/create post/comment/reply/read/edit/delete/dedupe/feed pending đã được chạy; [live-smoke.txt](../../docs/baseline/T009/live-smoke.txt). Không log token/password, process/DB tạm kết thúc sau smoke.

Các test mới kiểm tra atomic rollback khi insert job lỗi, idempotent/concurrent create, stale/concurrent edit, IDOR/role escalation, soft-delete/admin reason/audit, parent/cycle/depth, ancestor hide/restore, count/pagination, Unicode/HTML-as-text, query/body limits, CORS, limiter restart, nâng schema T008 giữ identities/sessions và rollback DB tạm có reply graph. Schema drift compare và PostgreSQL SQL offline nằm trong suite migration.

| Kiểm chứng | Kết quả thật | Evidence |
|---|---|---|
| Social API suite (gồm auth T008) | **87 passed, 1 warning**, 19.29s, exit 0 | [social-pytest.txt](../../docs/baseline/T009/social-pytest.txt) |
| V3 regression | **111 passed, 1 warning**, 1.40s, exit 0 | [legacy-pytest.txt](../../docs/baseline/T009/legacy-pytest.txt) |
| CLI migration + live HTTP smoke | PASS trên DB/tài khoản synthetic tạm; pending không vào feed | [live-smoke.txt](../../docs/baseline/T009/live-smoke.txt) |
| Hash legacy T007 | **68/68 file giữ nguyên** | [legacy-integrity.json](../../docs/baseline/T009/legacy-integrity.json) |
| Source service mới | Manifest toàn bộ source và thay đổi so với T008 | [social-source-manifest.json](../../docs/baseline/T009/social-source-manifest.json) |
| PostgreSQL | SQL offline pass; server thật CHƯA CHẠY | Migration tests |
| Frontend build | CHƯA CHẠY lại, frontend không đổi | Baseline T007 |

Warning cả hai suite là Starlette/httpx TestClient deprecation hiện có. Không dùng những kết quả này để tuyên bố inference/policy quality/E2E UI pass.

### Giới hạn/bàn giao

Frontend build không chạy lại vì không sửa frontend; chưa có Social Web trong T009. HTML-as-text backend không thay test XSS/render UI ở T010. PostgreSQL server/concurrency thật, worker/AI inference/policy evaluation, publish/restore/appeal API và tải thực chưa kiểm chứng. Chưa chạy migration/downgrade DB thật. Không lưu body revision cũ trong T009, chỉ audit metadata; retention/results/evidence cần task integration. Offset pagination không phải snapshot cursor. Task tiếp theo theo kế hoạch là T010 khi được yêu cầu; chưa tự bắt đầu.
