"""Read scoped artifacts; write measured performance and final integrity inventories."""
import argparse,hashlib,json,math,os,platform,re,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent
def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def save(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def stats(values):
    values=sorted(v for v in values if v is not None)
    return {'n':len(values),'p50_ms':round(statistics.median(values),3),'p95_ms':round(values[math.ceil(.95*len(values))-1],3),'min_ms':round(values[0],3),'max_ms':round(values[-1],3)} if values else {'n':0,'p50_ms':None,'p95_ms':None}
def performance():
    browser=read(P/'T043_browser_result.json');actual=read(P/'T043_actual_results.json');events=actual['events'];results={r['content_id']:r for r in actual['results']};rows=[]
    for item in browser['latencies']:
        own=[e for e in events if e['content_id']==item['content_id']]
        def stamp(status):return min([e['created_ms'] for e in own if e['status']==status],default=None)
        queued,started,complete=stamp('QUEUED'),stamp('PROCESSING'),stamp('COMPLETED')
        created=min([e['created_ms'] for e in own if e['event_type']=='conversation.message.created'],default=None)
        sql=next((r['enqueue_sql_ms'] for r in actual.get('sql_enqueue_timings',[]) if r['content_id']==item['content_id']),None)
        rows.append({**item,'enqueue_sql_insert_ms':sql,'enqueue_commit_spacing_ms':abs(queued-created) if queued is not None and created is not None else None,
            'queue_wait_ms':started-queued if queued is not None and started is not None else None,'ai_analysis_ms':results[item['content_id']]['conversation_signals']['analysis_ms'],
            'fanout_snapshot_render_observation_ms':item['observed_ms']-complete if complete else None})
    keys=['ack_fetch_ms','enqueue_sql_insert_ms','enqueue_commit_spacing_ms','queue_wait_ms','ai_analysis_ms','fanout_snapshot_render_observation_ms','author_analysis_visible_ms']
    report={'scope':'single_local_synthetic_workflow_not_load_test','concurrent_browser_contexts':3,'messages':len(rows),'ai_model':actual['results'][0]['model_version'],'model_threshold':.41,'model_fingerprint':actual['results'][0]['conversation_signals']['model_fingerprint'],
        'cpu_threads_for_neural_server':2,'host_logical_cpus':os.cpu_count(),'cpu':platform.processor(),'os':platform.platform(),'percentiles':'p50 median; p95 nearest-rank; tiny n, no production SLO',
        'notes':['ACK uses browser Resource Timing fetch duration through same-origin Vite proxy.',
                 'Enqueue SQL duration is actual INSERT execution before commit, joined only to committed messages; commit/lock time is in ACK. Enqueue spacing is millisecond notification spacing in one atomic content/job commit, not isolated queue insertion CPU time.',
                 'AI analysis includes neural/cache and context/target/repeated processing.',
                 'Fanout includes SSE polling window, snapshot fetch, render and Playwright observation; not isolated network time.'],
        'measurements':rows,'summary':{key:stats([r[key] for r in rows]) for key in keys}}
    save(P/'T043_performance.json',report)
    lines=['# Local measured performance','','Three authenticated browser contexts, four synthetic messages, actual approved-default V1.1 / default-v5. No new training or production load test.','','| Measurement | n | P50 ms | P95 ms |','|---|---:|---:|---:|']
    lines += [f"| {key} | {value['n']} | {value['p50_ms']} | {value['p95_ms']} |" for key,value in report['summary'].items()]
    lines+=['']+['- '+n for n in report['notes']]+['','Hardware: '+report['cpu']+f"; logical CPUs {os.cpu_count()}, neural process capped2threads. Percentiles have tiny samples and are not release SLOs."]
    (P/'PERFORMANCE.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');return report
def integrity(final=False):
    merge=read(P/'MERGE_MANIFEST.json');state=read(R/'tasks/moderation-ai/AUTO_EXECUTION_STATE.json');source=Path(merge['files'][0]['source']).parents[2];original=read(source/'MANIFEST_SHA256.json')
    for name,expected in original.items():assert sha(source/name)==expected,('Source pack changed',name)
    for file,expected in merge['historical_states'].items():
        matches=re.findall(r'^(?:-\s+)?\*\*(?:Status|Trạng thái):\*\*\s*(.+)$',(R/file).read_text(encoding='utf-8-sig'),re.M)
        assert matches and matches[0]==expected,('Historical status changed',file)
    assert len(state['tasks'])==10
    documents=list((R/'docs/realtime_moderation').glob('*.md'))+list((R/'docs/ml_studio').glob('*.md'))+list((R/'docs/demo').glob('*.md'))
    documents+=list((R/'docs/ai-update/final-report').glob('*GUIDE.md'))+[R/'docs/ai-update/final-report/T034_T043_FINAL_REPORT.md']
    for key,item in state['tasks'].items():
        task=R/item['file'];assert task.is_file();documents.append(task)
        specification=task.read_text(encoding='utf-8')
        assert specification.startswith('# '+key+' ')
        assert '**Mục tiêu:**' in specification
        # Source title+goal and18explicit implementation fields cover the20required items.
        assert len(re.findall(r'^- \*\*[^*\n]+:\*\*',specification,re.M))>=18
        assert len(list((R/'tasks/moderation-ai').glob(key+'-*.md')))==1
        for reference in item['evidence']:assert (R/reference).exists(),(key,'missing evidence',reference)
        if final:assert item['status']=='DONE_VERIFIED',(key,item['status'])
    checked_links=0
    for path in documents:
        if not path.exists():continue
        for value in re.findall(r'\[[^\]]+\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' in value or value.startswith('#'):continue
            target=value.split('#')[0].strip('<>')
            assert (path.parent/target).exists(),('Broken local link',str(path),target);checked_links+=1
    result={'status':'PASS','source_pack_files_verified':len(original),'historical_statuses_unchanged':len(merge['historical_states']),'new_tasks':10,'states':{k:v['status'] for k,v in state['tasks'].items()},'local_links_checked':checked_links,
        'task_required_items_verified':20,'readiness_lock_sha256':sha(R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json'),'source_pack_retained':True,'git_metadata_available':(R/'.git').exists(),'production_changed':False}
    save(P/'T043_integrity.json',result)
    return result
def inventory():
    files=set()
    for prefix in ['scripts/ml_studio','apps/shared','docs/realtime_moderation','docs/ml_studio','docs/demo']:
        files.update(p for p in (R/prefix).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    for prefix,patterns in [
        ('services/social-api/src/shieldvi_social',['live*.py','studio_routes.py']),('services/social-api/tests',['test_live*.py','test_studio*.py']),
        ('services/moderation-ai/app',['live*.py']),('tests',['test_incremental_analysis.py']),
        ('apps/social-web',['live.html','vite.live.config.js','src/live.*']),('apps/moderation-web',['live.html','studio.html','vite.live.config.js','src/live.*','src/studio*','src/*Studio.jsx']),
        ('scripts',['demo_realtime*.ps1','demo_open_browsers.mjs']),('contracts',['realtime_event.schema.json','live_moderation_response.schema.json']),
        ('docs/ai-update/final-report',['REALTIME_DEMO_GUIDE.md','TRAINING_STUDIO_GUIDE.md','DATASET_ANNOTATION_GUIDE.md','WINDOWS_SETUP_GUIDE.md','T034_T043_FINAL_REPORT.md']),
        ('tasks/moderation-ai',['T03[4-9]-*.md','T04[0-3]-*.md','AUTO_EXECUTION_STATE.json','TASK_ACCEPTANCE_MATRIX.md','TASK_DEPENDENCIES_T034_T043.md','TASK_MERGE_REPORT.md','RULES_REALTIME_STUDIO.md','TASK_ORDER_AI.md']),
        ('tasks',['AUTO_PROGRESS.md','AUTO_RESUME_T034_T043.md','TASK_ORDER.md'])]:
        for pattern in patterns:files.update(p for p in (R/prefix).glob(pattern) if p.is_file())
    files.update(p for p in P.iterdir() if p.is_file() and p.name not in ('ARTIFACTS.json','ARTIFACTS_ATTESTATION.json','ACTIVE_DEMO.json'))
    trained=read(P/'T041_retained.json');root=Path(trained['studio_root']);manifest=read(P/'T041_run_manifest.json');run=root/'training_runs'/manifest['run_id']
    files.update(p for p in run.rglob('*') if p.is_file())
    files.update(p for p in (root/'registry').glob('*.json'))
    files.update(p for p in (root/'evaluations').rglob('*.json'))
    sources=manifest['dataset_sources']
    for ref in sources.values():
        path=Path(ref['path']);files.update(p for p in path.parent.iterdir() if p.is_file())
    output={'scope':'T034–T043 added/updated sources and retained verification evidence','files':{p.relative_to(R).as_posix():sha(p) for p in sorted(files)},'excluded':'Temporary test DBs, mutable ACTIVE_DEMO pointer, private HMAC keys, runtime Studio DB and future interactive-demo sessions; protected baseline has its own original unchanged readiness lock.'}
    save(P/'ARTIFACTS.json',output);return len(output['files'])
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--final',action='store_true');args=parser.parse_args();performance();result=integrity(args.final)
    if args.final:
        result['artifact_files']=inventory();manifest=read(P/'ARTIFACTS.json')
        mismatches=[name for name,expected in manifest['files'].items() if sha(R/name)!=expected]
        assert not mismatches,mismatches
        save(P/'ARTIFACTS_ATTESTATION.json',{'status':'PASS','inventory_sha256':sha(P/'ARTIFACTS.json'),'files_verified':len(manifest['files']),'sha_mismatches':mismatches,'production_changed':False})
    print(json.dumps(result,ensure_ascii=False))
