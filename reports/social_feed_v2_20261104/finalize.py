"""Verify current outcomes before completion; keep old reports and locks intact."""
import hashlib,importlib.util,json,math,os,platform,re,statistics,sys,zipfile
from pathlib import Path
from import_tasks import ROOT,OUT,SOURCE,STATE,IDS,checkpoint,digest,save
OLD=ROOT/'reports/task_rollout_20261104'
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def log(path):
    raw=path.read_bytes();return raw.decode('utf-16' if raw.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8-sig')
def passed(name,count):assert re.search(rf'\b{count} passed\b',log(OUT/name)),name
def stats(values):
    values=sorted(values);return {'n':len(values),'p50_ms':statistics.median(values),'p95_ms':values[math.ceil(.95*len(values))-1]}
def main():
    passed('root_regression_utf8.log',744);passed('social_regression_sse_final.log',247)
    passed('T043_sse_green.log',18);assert '1 failed' in log(OUT/'T043_sse_red.log')
    for name in ('T037_build.log','T038_build.log'):assert 'built in' in log(OUT/name)
    assert re.search(r'(?:fail\s+0|failures\s+0)',log(OUT/'transport.log'))
    readiness=[json.loads(line) for line in log(OUT/'readiness.log').splitlines() if line.startswith('{')][-1]
    assert readiness['status']=='PASS' and readiness['files_checked']==1311
    demo=OLD/'demo_ab4d39e9057bf41f';browser=read(demo/'social_feed_result.json');assert browser['status']=='PASS' and len(browser['checks'])==10
    assert read(demo/'interactive_check.json')['contexts']==7
    assert read(demo/'ai_resumed.json')['actual_health']['model_path']==read(demo/'T043_actual_health.json')['model_path']
    assert read(demo/'T043_cleanup.json')['owned_processes_stopped']
    headless=OLD/'demo_d6c905446c193cbd';assert read(headless/'T043_browser_result.json')['status']=='PASS'
    assert len(read(headless/'T043_browser_result.json')['checks'])==8 and read(headless/'T043_cleanup.json')['owned_processes_stopped']
    studio=OLD/'demo_6a5b68a80812e8d6'
    for task in ('T039','T040'):assert read(studio/(task+'_browser_result.json'))['status']=='PASS'
    assert read(studio/'T043_cleanup.json')['owned_processes_stopped']
    for name in ('T041_receipt_reverified.json','T042_report_reverified.json'):assert read(OUT/name)['status']=='PASS'
    manifest=read(OUT/'MERGE_MANIFEST.json')
    for name,entry in read(SOURCE/'MANIFEST_SHA256.json').items():assert digest(SOURCE/name)==entry['sha256']
    with zipfile.ZipFile(OUT/'before_merge.zip') as backup:
        assert backup.testzip() is None
        before=json.loads(backup.read('tasks/moderation-ai/AUTO_EXECUTION_STATE.json'))
        for name,expected in manifest['before_sha256'].items():assert hashlib.sha256(backup.read(name)).hexdigest()==expected
        for item in manifest['tasks'].values():assert (ROOT/item['destination']).read_bytes().startswith(backup.read(item['destination']))
    state=read(STATE);assert state['tasks']==before['tasks'] and state['final_summary']==before['final_summary']
    for task in IDS:assert len(list((ROOT/'tasks/moderation-ai').glob(task+'[\u002d_]*.md')))==1,task
    spec=importlib.util.spec_from_file_location('historical_performance_reader',OLD/'finalize_rollout.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);module.P=headless;module.performance()
    summary={'scope':'local_synthetic_not_independent_real_or_load_test','social_browser_contexts':5,'total_browser_contexts':7,
        'ui_action_to_ack_ms':stats([r['comment_ack_ms'] for r in browser['latencies']]),
        'ui_action_to_result_visible_ms':stats([r['author_result_visible_ms'] for r in browser['latencies']]),
        'notes':['UI-action timers include fill/reply/click and browser observation; not pure HTTP latency.','Separate current 3-context/4-comment neural E2E has Resource Timing ACK, SQL enqueue, queue wait, AI analysis and fanout metrics. No production SLO.'],
        'component_metrics':str((headless/'T043_performance.json').relative_to(ROOT)),
        'cpu':platform.processor(),'logical_cpus':os.cpu_count(),'os':platform.platform(),'training_performed':False}
    save(OUT/'PERFORMANCE.json',summary)
    report=ROOT/'docs/realtime_moderation/SOCIAL_FEED_V2_ACCEPTANCE.md'
    report.write_text('''# Social Feed v2 — verified local acceptance, 04/11/2026

T034–T043 additional local scope is verified. Earlier task evidence/statuses
are preserved; new acceptance is separately tracked in TASK_ORDER_AI.md and
AUTO_EXECUTION_STATE.json/social_feed_v2. This is synthetic/local evidence,
not independent human-gold AI acceptance or a production release.

## Import and implementation

13source entries verified;10task ID collisions merged into the canonical
10files without creating duplicate task filenames. Original task bodies and
17control/task files are backed up byte-for-byte. New common safeguards stored
once; external source pack untouched. Source map and checksums:
`reports/social_feed_v2_20261104/MERGE_MANIFEST.json`.

| Task | Verified work |
|---|---|
| T034 | Actual repository audit, transport ADR, state/RBAC/test mapping;13contract tests |
| T035 | Existing durable API reused; five-account post/comment/reply test, idempotency/privacy/recovery;14tests |
| T036 | Explicit original-post/parent/current-reply context test;5worker+15incremental tests; approved processor/rules unchanged |
| T037 | Social Feed/post cards/composer, automatic public-feed refresh, reply context/time metadata and idempotent post retry;build+actual Chrome |
| T038 | Reauthenticated post/comment deep links; live evidence/manual hide/author appeal/restore and audit;Moderator build+actual Chrome |
| T039 | Existing Dataset Center reused;14backend+6actual upload/mapping/export/invalid-label UI checks |
| T040 | Existing annotation reused;6backend+6actual synthetic UI checks, same reviewer R1/R2, history and stale-R2 invalidation |
| T041 | 7guard/lifecycle tests; retained actual CPU-head run/checkpoint and concurrent47ms Social ACK receipt rehashed, no new training |
| T042 | 4guard tests; retained actual V1/r06/T041 paired4-comment report/models/cohort SHA verified and confusion/Macro-F1 recomputed; no new paired inference |
| T043 | 744root/startup+247Social Python tests,4transport tests,2frontend builds;7-context/10check Social Feed E2E and original3-context/8check neural E2E |

## Defects found and retained failures

- The new SSE scheduling probe failed before the fix. Synchronous SQL/pool
  waits inside the async SSE loop could prevent other request cleanup from
  running. `live_routes.py` now awaits `run_in_threadpool(read_page, ...)`.
  The unchanged probe and17related tests pass; full247Social regression and
  actual browser recovery pass. This does not alter model rules or policy.
- Windows Proactor accept WinError64 was observed on a failed browser run;
  demo Social uvicorn uses the opt-in Selector loop. This alone did not solve
  every freeze; subsequent SSE blocking was diagnosed and fixed above.
- Earlier send/login/restore timeouts are retained in T037/T043 failure logs;
  not every historical timeout can be attributed conclusively to one cause.
- An initial default-locale regression had3UnicodeDecodeError failures and
 741passes. With the documented Windows `-X utf8` invocation,744tests pass;
  no sealed research source, reference or dataset was modified.
- Failed browser setup now closes owned Chrome. Every new check retains a
  unique evidence directory instead of overwriting historical handoff reports.

## Current actual browser evidence

`reports/task_rollout_20261104/demo_ab4d39e9057bf41f/` contains the7-context run:
five distinct authenticated actors discover a UI-created post, comment/reply
without F5 or duplicates, real approved-default AI yields grounded repeated
evidence, moderator manually hides, author appeals and moderator restores.
Deep-link reauthentication, network reconnect, literal XSS rendering and a
thread over30comments pass. Owned AI is stopped, a new comment ACK persists
while analysis is pending/retrying, AI is restarted and processing completes
without duplicate comments. Stop script/owned-process cleanup pass.

`demo_d6c905446c193cbd/` contains the original3-context neural workflow8checks
and current component timing report. `demo_6a5b68a80812e8d6/` contains fresh
Dataset/Annotation browser evidence. Automated labels are synthetic tests,
never human gold. Original training/evaluation receipts are explicitly reused,
not presented as freshly executed training or inference.

## Demo and remaining limits

From project root, run `powershell -NoProfile -ExecutionPolicy Bypass -File
.\\scripts\\demo_realtime_studio.ps1`. Wait for DEMO_READY; seven Chrome contexts
open. Alice creates a post; other users select its feed card and comment/reply;
moderator reads evidence and makes manual decisions. Ctrl+C or
`scripts/demo_realtime_stop.ps1` stops the owned session. Detailed commands:
[demo guide](../ai-update/final-report/REALTIME_DEMO_GUIDE.md),
[Windows setup](../ai-update/final-report/WINDOWS_SETUP_GUIDE.md).

Feed discovery uses1.5second serialized polling with error backoff; opened
post/moderator updates use authenticated SSE. Public bodies remain subject to
existing policy publication; a reply alone never proves an attack. Filters in
Moderator are page-scoped. Other authors are displayed with pseudonymous IDs.
Each launcher invocation creates a separate isolated session; it does not resume
or merge existing demo sessions. Training remains an explicit operator action.
Tiny synthetic timing/metric samples are not capacity or quality guarantees.

V1/r06/default model,0.41,reference/test datasets and original readiness lock
remain unchanged (1311files verified). No production DB reset, deploy, push,
model promotion, r07 or new training. Formal T028/T029 remain BLOCKED and
T030–T033 PARTIAL. Next: operator demo/review, then permitted real-source intake
and genuine solo review rounds before independent evaluation/sign-off.

Full logs, performance definitions and SHA inventory:
`reports/social_feed_v2_20261104/` (PERFORMANCE.json, INTEGRITY.json,
ARTIFACTS.json and ARTIFACTS_ATTESTATION.json). Historical reports remain intact.
''',encoding='utf-8')
    sys.path.insert(0,str(ROOT/'reports/docs_cleanup_20261104'))
    from organize_docs import markdown_scope,broken_links
    links=broken_links(markdown_scope());assert not links,links
    checkpoint('T043','DONE_VERIFIED','Final744root/startup+247Social Python tests PASS,4transport tests PASS, both UI builds PASS. SSE scheduling RED→GREEN and full10-check7-context Social Feed/AI offline-recovery E2E PASS; original8-check3-context actual neural E2E PASS. All owned processes stopped;1311readiness files unchanged. Retained actual training/evaluation receipts reverified, not rerun. No production/default/training changes.',['docs/realtime_moderation/SOCIAL_FEED_V2_ACCEPTANCE.md','reports/social_feed_v2_20261104/root_regression_utf8.log','reports/social_feed_v2_20261104/social_regression_sse_final.log','reports/social_feed_v2_20261104/T043_sse_red.log','reports/social_feed_v2_20261104/T043_sse_green.log','reports/social_feed_v2_20261104/T043_feed_e2e_sse_fix.log','reports/social_feed_v2_20261104/T043_original_e2e.log'])
    save(OUT/'INTEGRITY.json',{'status':'PASS','canonical_task_ids':10,'source_entries_unchanged':13,'backed_up_originals_verified':17,'historical_tasks_and_evidence_state_unchanged':True,'new_local_done_verified':10,'broken_local_links':links,'readiness':readiness,'training_performed':False,'production_changed':False,'git_metadata_available':False})
    files=set(p for p in OUT.iterdir() if p.is_file() and p.name not in ('ARTIFACTS.json','ARTIFACTS_ATTESTATION.json'))
    names=['apps/social-web/src/live.jsx','apps/social-web/src/live.css','apps/moderation-web/src/live.jsx','services/social-api/src/shieldvi_social/live_routes.py','services/social-api/tests/test_live_api.py','services/social-api/tests/test_live_analysis_worker.py','services/social-api/tests/test_live_stream_scheduling.py','scripts/demo_loop.py','scripts/demo_open_browsers.mjs','scripts/demo_realtime_studio.ps1','reports/task_rollout_20261104/run_browser_actual.py','reports/task_rollout_20261104/browser_t043.mjs','docs/README.md','docs/realtime_moderation/ARCHITECTURE.md','docs/realtime_moderation/REPO_AUDIT.md','docs/realtime_moderation/SOCIAL_FEED_V2_ACCEPTANCE.md','docs/ai-update/final-report/REALTIME_DEMO_GUIDE.md','docs/ai-update/final-report/WINDOWS_SETUP_GUIDE.md']
    names+=list(manifest['before_sha256'])
    files.update(ROOT/name for name in names)
    for directory in (demo,headless,studio):
        files.update(p for p in directory.iterdir() if p.is_file() and p.suffix in ('.json','.png','.log','.jsonl','.csv') and p.name not in ('private_key','studio.sqlite3'))
    inventory={p.relative_to(ROOT).as_posix():digest(p) for p in sorted(files)}
    save(OUT/'ARTIFACTS.json',{'scope':'Social Feed v2 source and actual verification; excludes mutable DBs/private keys and historical evidence untouched','files':inventory})
    assert all(digest(ROOT/name)==expected for name,expected in inventory.items())
    save(OUT/'ARTIFACTS_ATTESTATION.json',{'status':'PASS','inventory_sha256':digest(OUT/'ARTIFACTS.json'),'files_verified':len(inventory),'mismatches':[]})
    print(json.dumps({'status':'PASS','new_tasks_done':10,'python_tests':991,'transport_tests':4,'readiness_files':1311,'hashed_files':len(inventory)}))
if __name__=='__main__':main()
