"""Actual loopback HTTP/inference checks for the process-local demo."""
import json,re,sys,time
from pathlib import Path
from urllib.request import Request,urlopen
from urllib.error import URLError,HTTPError
R=Path(__file__).resolve().parents[3];D=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
from verify_ai_readiness_lock import verify_lock
BASE='http://127.0.0.1:8023'

def get(path):
    with urlopen(BASE+path,timeout=60) as response:return response.read(),response.headers

if __name__=='__main__':
    for attempt in range(20):
        try:
            health=json.loads(get('/health')[0])
            if health['model_loaded']:break
        except URLError:pass
        time.sleep(1)
    else:raise RuntimeError('Demo model did not become ready')
    config=json.loads(get('/api/demo/config')[0]);assert config['model']=='r06' and config['threshold']==.41
    page,headers=get('/dashboard/');assert 'v6.1'.encode() in page and headers['X-ShieldVI-Demo']=='r06-v6.1-research'
    for asset in re.findall(r'(?:src|href)="(/dashboard/assets/[^\"]+)"',page.decode()):assert get(asset)[0]
    try:get('/api/v1/moderate/comment')
    except HTTPError as exc:assert exc.code==404
    else:raise AssertionError('Research demo must not expose internal moderation')
    cases=[]
    for number in (9,10,7):
        payload=get('/demo/threads/'+str(number))[0]
        request=Request(BASE+'/api/v2/analyze',data=payload,headers={'Content-Type':'application/json'},method='POST')
        with urlopen(request,timeout=60) as response:
            assert response.status==200;out=json.loads(response.read())
        assert 'r06' in out['checkpoint_id'] and out['source_model_threshold']==.41
        assert out['rule_versions']['context']=='context-v6.1-research'
        atomic_json(D/('Test'+str(number).zfill(2)+'_actual_demo_analysis.json'),out)
        if number==9:
            row=next(c for c in out['comments'] if c['comment_id']=='c17')
            assert row['moderation_assessment']['label']=='TOXIC' and row['directed_at_user_id']=='U03'
        elif number==10:
            row=next(c for c in out['comments'] if c['comment_id']=='c14')
            assert row['moderation_assessment']['label']=='CLEAN' and not row['analysis_signals']['attack_instance_candidate']
        else:
            assert {(e['actor_user_id'],e['target_user_id']):e['evidence_comment_ids'] for e in out['evidence']}=={
                ('U02','U03'):['c06','c11'],('U03','U02'):['c07','c12']}
        cases.append({'test':number,'status':'PASS','comments':len(out['comments'])})
    ready=verify_lock(R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json');assert ready['status']=='PASS'
    atomic_json(D/'smoke_result.json',{'status':'PASS','url':BASE+'/dashboard/','health':health,'demo':config,'cases':cases,
        'actual_model_inference':True,'training_performed':False,'readiness':ready,'launcher_sha256':file_sha(D/'launch.py')})
    print(json.dumps({'status':'PASS','cases':cases,'readiness_files':ready['files_checked']}))
