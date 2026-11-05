"""Write Vietnamese text directly from UTF-8 source, avoiding shell pipe encoding."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
plan=json.loads((OUT/'APPLIED.json').read_text(encoding='utf-8'))
intro=r'''# Tổ chức tài liệu ShieldVI — 04/11/2026

Tài liệu được tập trung dưới `docs/`; bắt đầu tại [mục lục](README.md).

## Kết quả

- Di chuyển 38 tài liệu hướng dẫn, kiến trúc và module vào nhóm phù hợp.
- Gộp ghi chú compatibility frontend vào hướng dẫn legacy research dashboard.
- Bỏ trang demo chỉ trỏ sang guide hiện hành; cập nhật tham chiếu về guide đó.
- Sửa liên kết và đường dẫn trong 53 file thuộc đợt di chuyển chính.
- Không có tài liệu độc lập trùng byte trong phạm vi tài liệu chính. Hai file bỏ
  đi là trang chỉ dẫn dư và ghi chú đã gộp đầy đủ; không xóa các bản khác nội dung
  chỉ vì cùng tên. README V3 và prompt cũ được chuyển vào khu lưu trữ.

## Cấu trúc

| Nhóm | Nội dung |
|---|---|
| `docs/README.md` | Điểm bắt đầu chung |
| `architecture/` | Kiến trúc hiện thực, database, API, migration, policy |
| `design/` | Bộ thiết kế Social ban đầu |
| `guides/` | Runbook và giải thích demo |
| `modules/` | Hướng dẫn backend/frontend và legacy dashboard |
| `ai-update/` | Quy trình, thực nghiệm và báo cáo AI theo phiên bản |
| `realtime_moderation/`, `ml_studio/` | Chi tiết realtime và ML Studio |
| `archive/` | Báo cáo triển khai, hướng dẫn và prompt lịch sử |
| `governance/` | Phụ lục quy tắc tham khảo |

## Các vị trí cần giữ

`AGENTS.md` là chỉ dẫn công cụ; README ở root chỉ liên kết tới mục lục.
`tasks/`, `.agents/skills/` và `contracts/` giữ quy ước hoạt động. README/license
cạnh dataset, model, lexicon là metadata provenance, không phải bản hướng dẫn
sản phẩm bị duy trì trùng. Snapshot `docs/baseline/`,
`docs/repository-merge-evidence/`, các bằng chứng kiểm thử và gói nguồn bên ngoài
repository được giữ nguyên.

Không sửa code runtime, checkpoint V1/r06, threshold 0.41, dataset hoặc database.
Giữ nguyên cả 37 trạng thái task. Các manifest SHA cũ là snapshot lịch sử;
bản đồ di chuyển và hash mới được ghi riêng.

## Phục hồi và kiểm tra

Bản sao nguyên byte của 61 file bị di chuyển/sửa/gộp nằm trong
`reports/docs_cleanup_20261104/before.zip`; bản sao chỉ mục AI trước khi bổ sung
liên kết hướng dẫn mới nằm trong `before_index_update.zip` cùng thư mục.
Tổng cộng 62 bản gốc đã được kiểm tra SHA. Bản đồ và kết quả kiểm tra nằm ở
`PLAN.json`, `APPLIED.json`, `VALIDATION.json`, `readiness.log` và
`FILES_SHA256.json` cùng thư mục. Không giải nén đè toàn repository; dùng bản đồ
để phục hồi đúng file cần thiết.

Kiểm tra từ repository root:

```powershell
.\.venv\Scripts\python.exe reports/docs_cleanup_20261104/validate_docs.py
.\.venv\Scripts\python.exe scripts/verify_ai_readiness_lock.py --lock reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json
```

Kiểm tra bao gồm vị trí file, nội dung bản sao ZIP, các liên kết tương đối,
metadata skill, trạng thái task, trùng nội dung và readiness lock. Không cần
build frontend hoặc chạy training vì source runtime không thay đổi.

## Bản đồ file

| Vị trí cũ (tính từ root) | Vị trí hiện tại |
|---|---|
'''
lines=[intro.rstrip()]
for old,new in plan['moves'].items():lines.append(f'| `{old}` | `{new}` |')
for old,new in plan['merged'].items():lines.append(f'| `{old}` (gộp) | `{new}` |')
for old,new in plan['redundant_pointer_pages'].items():lines.append(f'| `{old}` (bỏ trang trỏ dư) | `{new}` |')
lines+=['',f"SHA256 bản sao ZIP: `{plan['backup_sha256']}`."]
(ROOT/'docs/ORGANIZATION.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

progress=ROOT/'tasks/AUTO_PROGRESS.md'
marker='## Documentation consolidation — 04/11/2026'
if marker not in progress.read_text(encoding='utf-8-sig'):
    with progress.open('a',encoding='utf-8') as output:
        output.write('''

## Documentation consolidation — 04/11/2026

Đã gom 38 tài liệu vào docs/, gộp ghi chú frontend compatibility và bỏ trang demo
chỉ trỏ tới guide hiện hành. Điểm vào: docs/README.md; bản đồ: docs/ORGANIZATION.md.
Root chỉ giữ README dẫn mục lục và AGENTS cho công cụ. Task/skill và metadata
license/dataset/model giữ đúng vị trí. Không đổi runtime, model, dataset hay DB.

Kiểm tra: toàn bộ liên kết và đường dẫn cũ trong tài liệu, metadata skill,
checksum 62 bản gốc trong hai ZIP, trùng nội dung và 37 trạng thái task; readiness
verifier PASS 1311 file, lock không sửa/reseal. Không chạy frontend build hoặc
training vì chỉ đổi tài liệu. Lệnh/evidence: reports/docs_cleanup_20261104/
validate_docs.py, VALIDATION.json, readiness.log và FILES_SHA256.json. Manifest
SHA cũ là lịch sử trước di chuyển; bản đồ/hash đợt này lưu riêng.
''')
