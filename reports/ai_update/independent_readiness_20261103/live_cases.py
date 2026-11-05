import argparse,json,sys,time,urllib.request
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json
parser=argparse.ArgumentParser();parser.add_argument('phase',choices=('before','after'));args=parser.parse_args()
paths=[R/'datasets/synthetic_conversations/genz_v2/dashboard_threads'/(tid+'.json') for tid in ('SGZ500_0205','SGZ500_0218','SGZ500_0339')]
paths += [R/'datasets/fixtures/genz_regression'/name for name in ('SHIELDVI_01_GAME_RANK_LAG_30.json','SHIELDVI_04_DI_CAMPING_CHIA_TIEN_30.json')]
results={}
for port in (8020,8021):
    deadline=time.monotonic()+90
    while True:
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=3) as response:
                if json.load(response)['model_loaded']:break
        except OSError:pass
        if time.monotonic()>deadline:raise TimeoutError('Demo model not ready')
        time.sleep(2)
    results[str(port)]={}
    for path in paths:
        payload=json.loads(path.read_text(encoding='utf-8'))
        req=urllib.request.Request(f'http://127.0.0.1:{port}/api/v2/analyze',data=json.dumps(payload,ensure_ascii=False).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=60) as response:out=json.load(response)
        results[str(port)][payload['thread_id']]=out
if args.phase=='after':
    old=json.loads((P/'before_live.json').read_text(encoding='utf-8'))
    for port,threads in results.items():
        for tid,out in threads.items():
            prior={c['comment_id']:c for c in old[port][tid]['comments']}
            for c in out['comments']:
                for k in ('toxicity_score','toxic_for_moderation','toxic_for_repeated_rule','target_user_id','target_method','target_confidence','lexical_signals'):assert c[k]==prior[c['comment_id']][k]
            assert out['source_model_threshold']==.41 and out['rule_versions']['context']=='context-v4' and out['rule_versions']['target']=='target-v4'
        for tid,cid in [('SGZ500_0205','SGZ500_0205_C07'),('SGZ500_0218','SGZ500_0218_C06'),('SGZ500_0339','SGZ500_0339_C02')]:
            row=next(c for c in threads[tid]['comments'] if c['comment_id']==cid)
            assert row['moderation_assessment']['label']=='TOXIC' and row['directed_at_user_id']==tid+'_U01'
        shipping=threads['SGZ500_0205']['evidence']
        assert any(e['actor_user_id']=='SGZ500_0205_U02' and e['target_user_id']=='SGZ500_0205_U01' and e['evidence_comment_ids']==['SGZ500_0205_C03','SGZ500_0205_C07'] for e in shipping)
        for path,actor,ids in [(paths[3],'U02',['c08','c11','c15','c18']),(paths[4],'U04',['c09','c12','c15','c18'])]:
            tid=json.loads(path.read_text(encoding='utf-8'))['thread_id']
            assert any(e['actor_user_id']==actor and e['target_user_id']=='U03' and e['evidence_comment_ids']==ids for e in threads[tid]['evidence'])
    atomic_json(P/'live_verification.json',{'status':'PASS','ports':[8020,8021],'threads_each':5,'comments_each':90,'raw_invariant':True,
      'indirect_targets_checked':3,'shipping_game_camping_chains_exact':True,'human_gold':False,'independent_test_scored':False})
atomic_json(P/(args.phase+'_live.json'),results)
print(json.dumps({'phase':args.phase,'models':2,'threads_each':len(paths),'status':'PASS'}))
