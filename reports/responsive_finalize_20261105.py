"""Save verified UI-only evidence after real checks, without altering old receipts."""
import hashlib,json,re,sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
def load(relative):return json.loads((ROOT/relative).read_text(encoding='utf-8'))
def logtext(relative):
    raw=(ROOT/relative).read_bytes()
    return raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')
base='reports/task_rollout_20261104/'
before=base+'demo_77a6b5d6c9fe3d7b'
after=base+'demo_087f9ab44bf232fa'
regression=base+'demo_9a8b1169d4c85243'
audit=load(before+'/responsive_result.json');result=load(after+'/responsive_result.json')
assert result['status']=='PASS' and len(result['measurements'])==144
assert len(result['checks'])==13 and not result['page_errors']
assert all(not m['overflow'] and not m['smallControls'] for m in result['measurements'])
assert sum(m['overflow'] for m in audit['measurements'])==5
receipts={}
for name,count in [('comment_ux_result.json',7),('reply_identity_result.json',4),('quick_json_browser_result.json',5),('T043_browser_result.json',8)]:
    file=ROOT/regression/name
    if not file.exists() and name=='comment_ux_result.json':
        file=ROOT/regression/'comment_ux_browser_result.json'
    r=json.loads(file.read_text(encoding='utf-8'))
    assert r['status']=='PASS' and len(r['checks'])==count,(name,r)
    receipts[file.relative_to(ROOT).as_posix()]=count
for log in ['social_final_build','admin_ready_build']:
    assert 'built in' in logtext(f'reports/responsive_20261105_{log}.log')
assert '13 passed' in logtext('reports/responsive_20261105_startup.log')
assert 'pass 4' in logtext('reports/responsive_20261105_transport.log')
lock=load('reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json')
readiness=json.loads(logtext('reports/responsive_20261105_readiness.log'))
assert readiness['status']=='PASS' and readiness['files_checked']==1311
pointer=load(base+'ACTIVE_DEMO.json')
assert Path(pointer['root']).name=='demo_85046f8406365373' and pointer['pid']==6456

report=ROOT/'docs/realtime_moderation/RESPONSIVE_UI_REPORT.md'
for target in re.findall(r'\]\(([^)]+)\)',report.read_text(encoding='utf-8')):
    assert (report.parent/target).exists(),target

note='''

## Responsive UI/UX — 05/11/2026 — DONE_VERIFIED (Live/Studio scope)

Final evidence supersedes the IN_PROGRESS checkpoint above. Optimized Social
login/feed/create/detail/account/comment/reply, Moderator queue/review/JSON,
Dataset/Annotation/Training/Evaluation Studio using shared tokens and native
controls. 44px touch targets, bounded reply indentation/expandable parent context,
mobile navigation/cards, desktop rails/panels, draft retention, hide/delete
confirmation and metrics-derived charts. No new dependency or framework rewrite.

Before:120layout checks,5overflow cases (evaluation320/360/375/390,moderator820).
Final:144/144layout +13responsive workflows PASS at12viewports,0overflow,
0undersized enabled measured controls,0page errors;60after screenshots saved.
Existing actual-backend browser regressions24PASS (composer7,identity4,JSON5,
hide/appeal/restore/audit8); startup13PASS; shared transport4PASS; both frontend
builds PASS; readiness1311PASS. No full backend-suite rerun claimed for CSS/UI.
T043 browser test explicitly accepts the newly required hide confirmation;
all original visibility/appeal/evidence assertions remain unchanged.

Training progress/charts/logs verified with browser-only named fixture: no
training/evaluation start or worker. Synthetic upload/annotation test artifacts
remain separate from datasets and human gold. Active demo_85046f8406365373/PID6456
and its DB/pointer retained. No API/business/model/default/0.41/lock changes or
deploy. Frozen legacy routes excluded from edits and responsive acceptance;
physical-device/virtual-keyboard testing remains unverified. Formal T028/T029
BLOCKED and T030–T033 PARTIAL preserved; historical T034–T043 states retained.

Report: docs/realtime_moderation/RESPONSIVE_UI_REPORT.md.
Source/evidence SHA inventory: reports/responsive_20261105_verified.json.
Before: reports/task_rollout_20261104/demo_77a6b5d6c9fe3d7b/.
Final: reports/task_rollout_20261104/demo_087f9ab44bf232fa/.
Regressions: reports/task_rollout_20261104/demo_9a8b1169d4c85243/.
Resume: refresh existing /live.html or /studio.html; use browser device emulation
or run --responsive-check. No restart/migration/training required for this UI.
'''
progress=ROOT/'tasks/AUTO_PROGRESS.md'
assert 'Final evidence supersedes the IN_PROGRESS checkpoint above.' not in progress.read_text(encoding='utf-8')
with progress.open('a',encoding='utf-8') as f:f.write(note)
tasks=list((ROOT/'tasks/moderation-ai').glob('T0*.md'))
changed_tasks=[]
for p in tasks:
    if p.name[:4] not in {f'T0{i}' for i in range(37,44)}:continue
    with p.open('a',encoding='utf-8') as f:
        f.write('\n\n## Responsive UI follow-up — 05/11/2026\n\n'
                'Live/Studio UI scope verified:144layout checks/12viewports and13responsive\n'
                'workflows PASS;24existing browser checks PASS;builds/startup/transport PASS.\n'
                'No training/API/model/reference change. Frozen legacy and real-device\n'
                'coverage excluded. See docs/realtime_moderation/RESPONSIVE_UI_REPORT.md\n'
                'and reports/responsive_20261105_verified.json. Historical status retained.\n')
    changed_tasks.append(p.relative_to(ROOT).as_posix())

sources=['apps/shared/responsive.css','apps/social-web/src/live.jsx','apps/social-web/src/live-responsive.css',
 'apps/moderation-web/src/live.jsx','apps/moderation-web/src/workspace-responsive.css',
 'apps/moderation-web/src/QuickAiTest.jsx','apps/moderation-web/src/studio.jsx',
 'apps/moderation-web/src/AnnotationStudio.jsx','apps/moderation-web/src/TrainingStudio.jsx',
 'apps/moderation-web/src/EvaluationStudio.jsx','apps/moderation-web/src/ChoiceList.jsx',
 'apps/moderation-web/src/TrainingProgress.jsx','apps/moderation-web/src/LabelDistribution.jsx',
 'reports/task_rollout_20261104/run_browser_actual.py','reports/task_rollout_20261104/browser_t043.mjs',
 'reports/task_rollout_20261104/browser_responsive_20261105.mjs',
 'reports/task_rollout_20261104/browser_responsive_regression_20261105.mjs',
 'docs/realtime_moderation/RESPONSIVE_UI_REPORT.md','docs/README.md','tasks/AUTO_PROGRESS.md',*changed_tasks]
assert not set(sources).intersection(lock['files']), 'Cannot alter sealed source'
artifacts=[ROOT/p for p in sources]
for folder in [before,after,regression]:
    artifacts.extend((ROOT/folder).glob('*.png'));artifacts.extend((ROOT/folder).glob('*result*.json'))
artifacts.extend(ROOT.glob('reports/responsive_20261105_*.log'))
inventory={p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in artifacts}
receipt={'status':'PASS','scope':'responsive_opt_in_live_studio_not_frozen_legacy','date':'2026-11-05',
 'before':{'path':before,'layout_checks':120,'overflow_cases':5},
 'after':{'path':after,'layout_checks':144,'workflow_checks':13,'overflow_cases':0,'page_errors':0,'viewports':result['viewports']},
 'browser_regression':receipts,'startup_tests':13,'transport_tests':4,'builds':['social-live','moderator-live','studio'],
 'readiness':readiness,'active_demo_pointer_unchanged':True,'training_executed':False,'evaluation_started':False,
 'training_progress_scope':'browser_only_fixture_not_real_training_evidence','production_changed':False,
 'limitations':['Frozen legacy routes unchanged','Physical mobile devices and virtual keyboard untested'],
 'changed_files':sources,'sha256':inventory}
(ROOT/'reports/responsive_20261105_verified.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'PASS','layout_checks':144,'responsive_workflows':13,'browser_regressions':24,'startup':13,'transport':4,'task_notes':len(changed_tasks),'sha_entries':len(inventory)}))
