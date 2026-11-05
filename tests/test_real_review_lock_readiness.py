"""Protocol tests only: fabricated receipts/labels never enter the real corpus."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from fastapi.testclient import TestClient
from real_dataset.core import atomic_json
from real_dataset.review_app import create_app
from real_dataset.validation import validate_dataset
from test_real_dataset_pipeline import corpus,payload
from test_real_intake_readiness import draft

def test_stale_round2_cannot_be_locked_via_api_and_same_human_can_reconfirm(tmp_path):
    t=corpus(tmp_path,2)
    atomic_json(tmp_path/'manifests/development_exclusions.json',{'audit_completed':True,'thread_ids':[],'long_text_sha256':[],'source_records':[]})
    app=create_app(tmp_path,test_mode=True);store=app.state.store
    with TestClient(app) as client:
        headers={'X-Review-Token':client.get('/session').json()['token']};second=[]
        for i in range(2):
            first=store.save(payload(t,i,label='CLEAN',annotation_status='ROUND1_DONE'))
            second.append(store.save(payload(t,i,review_round=2,round1_revision=first['revision'],label='CLEAN',annotation_status='ROUND2_DONE')))
        store.check_thread(t['thread_id'],'solo',True,True,True)
        revised=store.save(payload(t,expected_revision=1,label='TOXIC',annotation_status='ROUND1_DONE',change_reason='Unit first-round revision'))
        assert len(client.get('/api/round2-queue',params={'reviewer_id':'solo'}).json()['items'])==1
        rejected=client.post('/api/lock',headers=headers,json={'reviewer_id':'solo'})
        assert rejected.status_code==422
        assert not (tmp_path/'manifests/evaluation_lock.json').exists()
        renewed=client.post('/api/reviews',headers=headers,json=payload(t,review_round=2,round1_revision=revised['revision'],
            expected_revision=second[0]['revision'],label='TOXIC',annotation_status='ROUND2_DONE',change_reason='Unit same-human reconfirmation'))
        assert renewed.status_code==200
        assert not client.get('/api/round2-queue',params={'reviewer_id':'solo'}).json()['items']
        assert client.post('/api/lock',headers=headers,json={'reviewer_id':'solo'}).status_code==200
        # A two-comment protocol fixture never satisfies the real200 criterion.
        assert validate_dataset(tmp_path)['t028_real_acceptance_ready'] is False

def test_round2_identity_and_empty_cohort_guards_are_enforced_by_api(tmp_path):
    app=create_app(tmp_path,test_mode=True)
    with TestClient(app) as client:
        headers={'X-Review-Token':client.get('/session').json()['token']}
        assert client.post('/api/lock',json={'reviewer_id':'solo'}).status_code==403
        assert client.post('/api/lock',headers=headers,json={'reviewer_id':'solo'}).status_code==422
        t=corpus(tmp_path,2);first=app.state.store.save(payload(t,label='CLEAN',annotation_status='ROUND1_DONE'))
        response=client.post('/api/reviews',headers=headers,json=payload(t,reviewer_id='other_identity',review_round=2,
            round1_revision=first['revision'],label='CLEAN',annotation_status='ROUND2_DONE'))
        assert response.status_code==422
        assert not app.state.store.list_reviews(reviewer_id='other_identity')

def test_empty_provenance_url_is_rejected_before_any_quarantine_or_private_key_write(tmp_path):
    with TestClient(create_app(tmp_path,test_mode=True),raise_server_exceptions=False) as client:
        headers={'X-Review-Token':client.get('/session').json()['token']}
        invalid=draft();invalid['source_url']=''
        result=client.post('/api/manual-intake',headers=headers,json=invalid)
        assert result.status_code==422
        assert not list((tmp_path/'anonymized/manual_inbox').glob('*.json'))
        assert not (tmp_path/'raw/private_pseudonym_key.txt').exists()
