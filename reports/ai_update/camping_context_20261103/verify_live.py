"""Actual V1.1/r05 demo smoke, invariant raw scores, new context and exact evidence."""
import hashlib,json,re,sys,time,urllib.request,urllib.error
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
ref=json.loads((R/'tests/fixtures/ai_update/camping_reference.json').read_text(encoding='utf-8'))
payload=json.loads((R/ref['input_file']).read_text(encoding='utf-8'))
before=json.loads((P/'before_live.json').read_text(encoding='utf-8'))
state=json.loads((P/'demo_after_server_state.json').read_text(encoding='utf-8-sig'))
def get(port,path):
    with urllib.request.urlopen(f'http://127.0.0.1:{port}{path}',timeout=8) as response:return response.read()
def post(port,path):
    req=urllib.request.Request(f'http://127.0.0.1:{port}{path}',data=json.dumps(payload,ensure_ascii=False).encode('utf-8'),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(req,timeout=30) as response:return json.load(response)
results={};checks={}
for server in state:
    port=server['port'];until=time.monotonic()+90
    while True:
        try:
            health=json.loads(get(port,'/health'))
            if health['model_loaded']:break
        except (OSError,urllib.error.URLError):pass
        if time.monotonic()>until:raise TimeoutError('Demo not ready: '+str(port))
        time.sleep(2)
    assert Path(health['model_path']).resolve()==Path(server['model_path']).resolve()
    assert file_sha(Path(server['model_path'])/'model.safetensors')==server['model_sha256']
    html=get(port,'/dashboard/')
    assert hashlib.sha256(html).hexdigest()==file_sha(P/'dashboard_build/index.html')
    script=re.search(rb'src="([^"]+\.js)"',html).group(1).decode()
    assert b'APOLOGY_ACCEPTANCE' in get(port,script)
    out=post(port,'/api/v2/analyze');legacy=post(port,'/api/analyze')
    old={c['comment_id']:c for c in before[str(port)]['comments']};old_api={c['comment_id']:c for c in legacy['comments']}
    rows={c['comment_id']:c for c in out['comments']}
    for cid,c in rows.items():
        for key in ('toxicity_score','toxic_for_moderation','toxic_for_repeated_rule','target_user_id','target_method','target_confidence'):
            assert c[key]==old[cid][key]==old_api[cid][key],(port,cid,key)
        assert c['moderation_assessment']['label']==ref['labels'][cid]
        assert not c['policy_risk']['executed']
    assert out['source_model_threshold']==.41 and out['model_threshold']==.41 and out['repeated_rule_threshold']==.41
    assert rows['c09']['toxicity_score']<.41 and not rows['c09']['toxic_for_moderation']
    chain=next(e for e in out['evidence'] if e['actor_user_id']=='U04' and e['target_user_id']=='U03')
    assert chain['evidence_comment_ids']==ref['attack_evidence_ids'] and len(out['evidence'])==1
    for cid in ref['attack_evidence_ids']:
        assert rows[cid]['directed_at_user_id']=='U03' and rows[cid]['analysis_signals']['attack_instance_candidate']
    assert 'DEFENSE' not in rows['c18']['analysis_signals']['context_tags']
    assert 'APOLOGY_ACCEPTANCE' in rows['c25']['analysis_signals']['context_tags'] and 'ACKNOWLEDGEMENT' not in rows['c25']['analysis_signals']['context_tags']
    results[str(port)]=out
    checks[str(port)]={'health':'ready','model_loaded':True,'model_path':health['model_path'],'dashboard_status':200,
      'updated_bundle_served':True,'legacy_api':200,'v2_api':200,'all30_AI_reference_labels_match':True,
      'raw_scores_and_legacy_fields_unchanged':True,'evidence':chain,'c09_raw_score':rows['c09']['toxicity_score'],
      'c09_advisory':rows['c09']['moderation_assessment']['label'],'policy_executed':False}
    server['status']='READY'
    match=re.search(r'Started server process \[(\d+)\]',Path(server['stderr']).read_text(encoding='utf-8',errors='replace'))
    if match:server['server_process_id']=int(match[1])
atomic_json(P/'demo_after_server_state.json',state)
atomic_json(P/'after_live.json',results);atomic_json(P/'live_smoke.json',checks)
print(json.dumps({'status':'LIVE_BOTH_MODELS_PASS','ports':list(checks),'all30_reference_labels':True,'exact4attack_chain':True,'raw_invariant':True,'new_UI_served':True}))
