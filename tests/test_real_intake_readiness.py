"""All fabricated source material and manual labels stay in isolated pytest roots."""
import copy,json,sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'scripts'))
from real_dataset.core import Pseudonymizer,atomic_json
from real_dataset.intake import stage_manual_thread
from real_dataset.collector import collect
from real_dataset.review_app import create_app
from real_dataset.store import ReviewStore
from real_dataset.validation import validate_dataset
from real_dataset.leakage import development_index
from test_real_dataset_pipeline import corpus,payload

def draft():
    return {'source_url':'https://unit.invalid/post/1','license_declaration':'unit-only claim, not verified',
      'license_evidence_url':'https://unit.invalid/license','topic':'Unit local intake',
      'comments':[{'source_comment_id':'a','source_user_id':'PrivateAuthor','text':'PrivateAuthor liên hệ test@example.org','timestamp':None},
      {'source_comment_id':'b','parent_source_comment_id':'a','source_user_id':'SecondAuthor','text':'Mình trả lời nguyên văn','timestamp':'2020-01-01T00:01:00Z'}]}

def test_user_pause_blocks_network_even_with_stale_contact(tmp_path):
    atomic_json(tmp_path/'manifests/collection_policy.json',{'collection_enabled':False,'reason':'explicit user pause'})
    def forbidden(*args,**kwargs):pytest.fail('Paused collector must not construct a network client')
    r=collect(tmp_path,contact='unit@university.edu',client_factory=forbidden)
    assert r['status']=='BLOCKED' and r['network_requests']==0 and not (tmp_path/'raw/cache').exists()

def test_intake_preserves_graph_and_missing_time_without_becoming_real_or_gold(tmp_path):
    r=stage_manual_thread(tmp_path,draft());paths=list((tmp_path/'anonymized/manual_inbox').glob('*.json'))
    value=json.loads(paths[0].read_text(encoding='utf-8'));a,b=value['comments']
    assert r['counted_as_real'] is False and not value['evaluation_eligible'] and not value['training_eligible'] and not value['human_gold']
    assert value['source_permission_status']=='UNVERIFIED' and value['labels'] is None
    assert a['timestamp'] is None and b['timestamp']=='2020-01-01T00:01:00+00:00' and b['parent_id']==a['comment_id']
    assert 'PrivateAuthor' not in a['text'] and 'example.org' not in a['text']
    assert value['source_url']==draft()['source_url'] and value['license_evidence_url']==draft()['license_evidence_url']
    assert validate_dataset(tmp_path)['actual_threads']==0 and not ReviewStore(tmp_path).list_reviews()
    assert stage_manual_thread(tmp_path,draft())['already_present'] and len(paths)==1

@pytest.mark.parametrize('kind',['parent','cycle','time','url','annotations'])
def test_intake_rejects_invalid_structure_or_preloaded_labels(tmp_path,kind):
    d=draft()
    if kind=='parent':d['comments'][1]['parent_source_comment_id']='missing'
    elif kind=='cycle':d['comments'][0]['parent_source_comment_id']='b'
    elif kind=='time':d['comments'][0]['timestamp']='2020-01-01T00:00:00'
    elif kind=='url':d['source_url']='file:///private.txt'
    else:d['comments'][0]['annotation']={'label':'CLEAN'}
    with pytest.raises(ValueError):stage_manual_thread(tmp_path,d)
    assert not list((tmp_path/'anonymized/manual_inbox').glob('*.json'))

def test_missing_intake_pseudonym_key_is_not_silently_regenerated(tmp_path):
    stage_manual_thread(tmp_path,draft())
    # Move aside the unit-test key, never any actual dataset's private key.
    path=tmp_path/'raw/private_pseudonym_key.txt';path.rename(path.with_suffix('.saved'))
    with pytest.raises(ValueError,match='key missing'):Pseudonymizer(tmp_path)

def test_stale_round2_returns_to_same_human_review_queue(tmp_path):
    t=corpus(tmp_path);s=ReviewStore(tmp_path)
    first=s.save(payload(t,label='CLEAN',annotation_status='ROUND1_DONE'))
    s.save(payload(t,review_round=2,round1_revision=first['revision'],label='CLEAN',annotation_status='ROUND2_DONE'))
    assert not s.round2_queue('solo')
    s.save(payload(t,expected_revision=first['revision'],label='TOXIC',annotation_status='ROUND1_DONE',change_reason='unit revised first review'))
    assert len(s.round2_queue('solo'))==1
    assert not s.round2_queue('another_reviewer')

def test_ui_intake_is_csrf_protected_blind_and_not_counted_as_ready(tmp_path):
    with TestClient(create_app(tmp_path,test_mode=True)) as client:
        session=client.get('/session').json();assert session['blind_review'] and not session['model_predictions_enabled']
        assert client.post('/api/manual-intake',json=draft()).status_code==403
        r=client.post('/api/manual-intake',json=draft(),headers={'X-Review-Token':session['token']})
        assert r.status_code==200 and not r.json()['counted_as_real']
        ready=client.get('/api/readiness').json()
        assert ready['manual_intake_pending']==1 and ready['candidate_threads']==0 and ready['target_threads']==200
        assert not client.get('/api/threads').json()['items'] and not client.get('/api/round2-queue?reviewer_id=solo').json()['items']

def test_nested_synthetic_threads_are_excluded_without_losing_comment_text(tmp_path):
    from real_dataset.core import sha_file,sha_bytes,comparison
    source=tmp_path/'synthetic.jsonl';text='Đây là câu tổng hợp dài dùng để kiểm tra chống rò rỉ. '*3
    source.write_text(json.dumps({'thread_id':'synthetic_old','comments':[{'text':text}]},ensure_ascii=False)+'\n',encoding='utf-8')
    root=tmp_path/'real'
    atomic_json(root/'manifests/development_exclusions.json',{'audit_completed':True,'source_records':[
        {'path':'synthetic.jsonl','format':'threads_jsonl','sha256':sha_file(source)}]})
    ids,hashes,groups=development_index(root,project_root=tmp_path)
    assert 'synthetic_old' in ids and groups['synthetic_old']==[text] and sha_bytes(comparison(text).encode()) in hashes
    source.write_text('{}\n',encoding='utf-8')
    with pytest.raises(ValueError,match='missing/changed'):development_index(root,project_root=tmp_path)
