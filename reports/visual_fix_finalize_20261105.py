"""Validate actual launcher receipts before recording this UI fix as complete."""
from pathlib import Path
from collections import Counter
import hashlib,json,re,sqlite3,struct,urllib.request

ROOT=Path(__file__).resolve().parents[1]
def read(path):return json.loads((ROOT/path).read_text(encoding='utf-8'))
def log(path):
    raw=(ROOT/path).read_bytes()
    return raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')
pointer=read('reports/task_rollout_20261104/ACTIVE_DEMO.json')
run=Path(pointer['root']).resolve();assert run.parent==ROOT/'reports/task_rollout_20261104'
assert pointer['running']
result=json.loads((run/'visual_result.json').read_text(encoding='utf-8'))
assert result['status']=='PASS' and len(result['records'])==70 and len(result['checks'])==10
assert not result['page_errors']
for r in result['records']:
    assert not r['problems'],(r['route'],r['requested'],r['problems'])
    assert r['metrics']['innerWidth']==r['requested']['width']
    assert r['metrics']['innerHeight']==r['requested']['height']
    image=run/f"after_{r['route']}_{r['requested']['width']}.png"
    assert struct.unpack('>I',image.read_bytes()[16:20])[0]==r['requested']['width'],image
assert any('1075px' in c for c in result['checks'])
assert any('clipped_tablet_filters' in c for c in result['checks'])
workflow='reports/task_rollout_20261104/demo_c36e3823760cb65e'
old=read(workflow+'/T043_browser_result.json');assert old['status']=='PASS' and len(old['checks'])==8
assert '13 passed' in log('reports/visual_fix_20261105_startup.log')
for app in ('social','admin'):assert 'built in' in log(f'reports/visual_fix_20261105_{app}_build.log')
readiness=json.loads(log('reports/visual_fix_20261105_readiness.log'))
assert readiness['status']=='PASS' and readiness['files_checked']==1311
http=urllib.request.build_opener(urllib.request.ProxyHandler({}))
for url in pointer['urls'].values():
    with http.open(url,timeout=10) as response:assert response.status==200

counts={}
for dbfile in (run/'studio').rglob('*.sqlite3'):
    with sqlite3.connect(f'file:{dbfile.as_posix()}?mode=ro',uri=True) as db:
        names={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for name in ('training_runs','evaluations','evaluation_runs'):
            if name in names:counts[name]=db.execute(f'SELECT COUNT(*) FROM {name}').fetchone()[0]
assert counts.get('training_runs')==0,counts
assert all(n==0 for name,n in counts.items()),counts

report=ROOT/'docs/realtime_moderation/RESPONSIVE_VISUAL_FIX_REPORT.md'
text=report.read_text(encoding='utf-8').replace('demo_f53e637975139804',run.name)
text=text.replace('Trạng thái: IN_PROGRESS — DOM/nghiệp vụ đã kiểm chứng; đang nghiệm thu ảnh cuối.','Trạng thái: DONE_VERIFIED trong phạm vi Live/Studio và các kích thước được đo.')
text=text.replace('http://127.0.0.1:54601/live.html?thread=7b36e75a-3104-49a0-b9e2-0db69dad4dc7',pointer['urls']['social']).replace('http://127.0.0.1:54602/live.html',pointer['urls']['moderator']).replace('http://127.0.0.1:54602/studio.html',pointer['urls']['studio'])
text+='''

### Kiểm tra chất lượng ảnh và khởi động lại

Ảnh cuối chụp qua CDP ở đúng innerWidth; xác minh PNG IHDR khớp từng width yêu
cầu. Trong capture, giữ nguyên gutter scrollbar đang có và assert DOM width
không đổi trước/trong/sau chụp, rồi gỡ style tạm. Không thêm overflow-x:hidden
hoặc thay CSS app để hợp thức hóa ảnh. Lượt demo_4f894a4ffc8a55d2 đã phát hiện
capture làm biến đổi gutter; bị loại, giữ bằng chứng, không tính PASS.
Lượt demo_f53e637975139804 đạt DOM tests nhưng ảnh Playwright bị crop15px; giữ
nguyên như lịch sử. Ảnh final liên kết phía trên thuộc session nghiệm thu mới.

Cửa sổ cũ được tạo với viewport1250px phải khởi tạo lại bằng launcher; refresh
không gỡ override của Playwright. Dùng các cửa sổ/URL session mới ở trên. Không
tự dừng session người dùng ban đầu hoặc reset dữ liệu cũ.

Readiness1311/1311 PASS. DB Studio session cuối có0 training run và0 evaluation
run; không thực hiện train/evaluate mô hình trong đợt sửa layout. Có inference
thật phục vụ các comment/JSON test. Manifest SHA và URL snapshot:
`reports/visual_fix_20261105_verified.json`.
'''
for target in re.findall(r'\]\(([^)]+)\)',text):
    if not target.startswith('http'):assert (report.parent/target).exists(),target
report.write_text(text,encoding='utf-8')

note=f'''

## Native Chrome visual fix — 05/11/2026 — DONE_VERIFIED

Supersedes viewport-only responsive acceptance for the user-reported issue.
Measured genuine launcher BEFORE: native window1650/850 still CSS1250, fixed
1250x950 Playwright viewport; tablet filters3columns. Headed context now
viewport:null. Fluid Live/Studio shells, responsive filter tracks, bounded
queue/sidebar widths, desktop context/review panels, reading-text-only caps.
Frozen legacy/API/backend/model/0.41/readiness/reference states unchanged.

Final actual launcher session: {run.relative_to(ROOT).as_posix()}.
70/70layout measurements across7populated Live/Studio states and10viewports,
10/10workflows PASS;0page errors/overflow/clipped fields. Native desktop width
verified;28native cases,14native-width/height-only emulation due Windows cap,
28mobile emulation. At1650 client/root/shell1635; at850 shell835 and Thread394.5.
Negative controls correctly reject1075px left root and clipped tablet filters.
70final screenshots assert PNG width and unchanged DOM width during capture.
Prior interrupted/harness/cropped-screenshot attempts retained and documented.

Both builds PASS; startup13PASS; actual launcher hide/appeal/restore/repeated/
audit E2E8PASS; readiness1311PASS. Studio training/evaluation run counts0;
only synthetic UI draft annotation, never human gold. User's original session
retained; final4-context VisualCheck demo remains running. Normal launcher
still opens5social accounts+Moderator+Studio, now with native resize.
Old fixed-viewport windows need a fresh launcher session, not only refresh.
Report: docs/realtime_moderation/RESPONSIVE_VISUAL_FIX_REPORT.md.
Evidence/SHA: reports/visual_fix_20261105_verified.json.
URLs: Social {pointer['urls']['social']}
Moderator {pointer['urls']['moderator']}; Studio {pointer['urls']['studio']}.
Remaining limits: real phones/keyboard, other browsers/DPI/zoom unverified;
legacy unchanged; formal T028/T029 BLOCKED, T030-T033 PARTIAL preserved.
'''
progress=ROOT/'tasks/AUTO_PROGRESS.md'
assert '## Native Chrome visual fix — 05/11/2026 — DONE_VERIFIED' not in progress.read_text(encoding='utf-8')
with progress.open('a',encoding='utf-8') as f:f.write(note)
task=ROOT/'tasks/moderation-ai/T043-realtime-studio-e2e-handoff.md'
with task.open('a',encoding='utf-8') as f:f.write('\n\n## Native Chrome visual follow-up — 05/11/2026\n\nFixed headed demo viewport override and fluid Live/Studio shells.70native-width/\nmobile layout cases,10workflows,8existing actual-AI E2E cases PASS; builds/startup/\nreadiness PASS. Prior viewport-only acceptance did not cover native resizing.\nSee docs/realtime_moderation/RESPONSIVE_VISUAL_FIX_REPORT.md and\nreports/visual_fix_20261105_verified.json. Historical task status preserved.\n')

sources=['apps/shared/responsive.css','apps/social-web/src/live-responsive.css','apps/moderation-web/src/workspace-responsive.css',
 'scripts/demo_open_browsers.mjs','scripts/demo_realtime_studio.ps1','reports/task_rollout_20261104/run_browser_actual.py',
 'reports/task_rollout_20261104/browser_visual_fix_20261105.mjs','docs/README.md',report.relative_to(ROOT).as_posix(),
 progress.relative_to(ROOT).as_posix(),task.relative_to(ROOT).as_posix()]
lock=read('reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json');assert not set(sources).intersection(lock['files'])
artifacts=[ROOT/p for p in sources]+[run/'visual_result.json']+list(run.glob('after*.png'))
artifacts+=[ROOT/'reports/task_rollout_20261104/demo_a53a25230d622b48/visual_result.json',ROOT/workflow/'T043_browser_result.json']
artifacts+=[ROOT/f'reports/visual_fix_20261105_{name}.log' for name in ('social_build','admin_build','startup','readiness','workflows')]
receipt={'status':'PASS','date':'2026-11-05','run':run.relative_to(ROOT).as_posix(),'urls':pointer['urls'],
 'root_cause':'Fixed Playwright headed viewport1250x950 + capped CSS shells',
 'layout_cases':70,'workflows':10,'page_errors':0,'mode_counts':dict(Counter(r['mode'] for r in result['records'])),
 'actual_moderation_e2e':8,'startup_tests':13,'builds':['Social','Moderator+Studio'],'readiness':readiness,
 'studio_job_counts':counts,'training_started':False,'evaluation_started':False,'demo_running':True,
 'source_changes':sources,'sha256':{p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts},
 'limitations':['physical mobile keyboard untested','height-only emulation for OS height limit','frozen legacy unchanged']}
(ROOT/'reports/visual_fix_20261105_verified.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','run':run.name,'layout_cases':70,'workflows':10,'screenshot_widths_verified':70,'studio_jobs':counts,'sha_entries':len(receipt['sha256']),'urls':pointer['urls']}))
