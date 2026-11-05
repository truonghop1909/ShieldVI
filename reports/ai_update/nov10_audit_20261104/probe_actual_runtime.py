"""Instrument an isolated canonical ASGI app with real r06; no live-server edit."""
import json,os,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent;D=R/'datasets/fixtures/nov10_regression_v1'
sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(R/'services/moderation-ai'))
from synthetic_data.pipeline import atomic_json,file_sha

if __name__=='__main__':
    os.environ.update(MODEL_PATH=str(R/'models/candidates/T029_synthetic_only_head_cpu_20261103_r06'),STORE_SUMMARIES='0',
        REVIEW_DB_PATH=str(P/'probe_reviews.sqlite3'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',CUDA_VISIBLE_DEVICES='-1')
    import torch
    torch.set_num_threads(4)
    from fastapi.testclient import TestClient
    import app.main as main
    import app.experiments.fresh10_v6 as exp
    original_context=exp.context_v6;calls=[]
    def context_spy(text,participants=()):
        ctx,trace=original_context(text,participants)
        calls.append({'text_sha256':__import__('hashlib').sha256(text.encode()).hexdigest(),'context_version':ctx.version,
                      'attack_candidate':ctx.attack_candidate,'predicate_matches':len(trace['matches'])})
        return ctx,trace
    exp.context_v6=context_spy;main.analyze_thread_v2=exp.analyze_thread_v6
    observed=[]
    with TestClient(main.app) as client:
        assert client.get('/health').json()['model_loaded']
        assert main.app.state.predictor.threshold==.41
        for number in (12,15,20):
            thread=json.loads(next((D/'inputs').glob('TEST'+str(number)+'_*.json')).read_text())
            imported=json.loads(next((D/'analysis').glob('*_'+str(number)+'_*analysis.json')).read_text())
            count=len(calls);response=client.post('/api/v2/analyze',json=thread);assert response.status_code==200
            out=response.json();assert len(calls)-count==20
            diff=max(abs(a['toxicity_score']-b['toxicity_score']) for a,b in zip(out['comments'],imported['comments']))
            assert diff<=.000002,(number,diff)
            assert out['rule_versions']==imported['rule_versions']
            assert all(not c['analysis_signals']['directed_attack_candidate'] for c in out['comments'])
            observed.append({'test':number,'http_status':200,'context_v61_calls':20,'raw_score_max_abs_difference':diff,
                             'attack_instances':sum(c['analysis_signals']['attack_instance_candidate'] for c in out['comments'])})
            atomic_json(P/('actual_Test'+str(number)+'_analysis.json'),out)
        control={'thread_id':'actual_runtime_control','comments':[
            {'comment_id':'a','user_id':'A','timestamp':'2026-11-04T12:00:00Z','text':'Mình gửi bản đồ vị trí các kệ sách.'},
            {'comment_id':'b','parent_id':'a','user_id':'B','timestamp':'2026-11-04T12:02:00Z','text':'Bạn đúng là đồ ngu.'},
            {'comment_id':'c','parent_id':'a','user_id':'B','timestamp':'2026-11-04T12:04:00Z','text':'Mày là đồ vô dụng.'}]}
        result=client.post('/api/v2/analyze',json=control);assert result.status_code==200
        out=result.json();assert out['evidence'][0]['evidence_comment_ids']==['b','c']
        assert out['evidence'][0]['actor_user_id']=='B' and out['evidence'][0]['target_user_id']=='A'
        atomic_json(P/'actual_positive_control.json',out)
    atomic_json(P/'runtime_probe.json',{'status':'PASS','actual_r06_inference':True,'asgi_http':True,
        'processor_sha256':file_sha(R/'services/moderation-ai/app/experiments/fresh10_v6.py'),
        'weights_sha256':file_sha(R/'models/candidates/T029_synthetic_only_head_cpu_20261103_r06/model.safetensors'),
        'observed':observed,'calls':calls,'positive_repeated_control':'PASS','training_performed':False,
        'original_export_process_identity_proven':False,'note':'New instrumented ASGI run confirms current source behavior; export versions/replay alone do not attest original process identity.'})
    print(json.dumps({'status':'PASS','actual_r06_comments':len(calls),'observed':observed,'positive_repeated_control':'PASS'}))
