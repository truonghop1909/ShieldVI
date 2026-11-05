import json
import pytest
from test_studio_datasets import studio,payload,sample,upload
from test_live_api import live
from ml_studio.annotations import StudioReviews

def setup(studio):
    rows=[sample(label=None),sample(comment_id='c2',parent_id='c1',user_id='ParticipantB',timestamp='2026-11-04T00:01:00Z',text='Mình có thể đem chậu cây và vài nhãn giấy để đánh dấu những giống rau mới.',label=None)]
    result=upload(studio,payload(rows,dataset_type='UNLABELED')).json();assert result['status']=='ACCEPTED'
    return result['id']
def annotation(studio,identity,cid='c1',round=1,revision=0,**changes):
    live,_=studio
    value={'thread_id':'STUDIO_DEMO_100','comment_id':cid,'review_round':round,'expected_revision':revision,'label':'CLEAN','category':'normal','annotation_status':'ROUND1_DONE' if round==1 else 'ROUND2_DONE'};value.update(changes)
    return live[0].post('/api/studio/annotations/'+identity,headers=live[3],json=value)
def state(studio,identity):return studio[0][0].get('/api/studio/annotations/'+identity,headers=studio[0][3])
def snapshot(studio,identity):return studio[0][0].post('/api/studio/annotations/'+identity+'/snapshot',headers=studio[0][3])

def test_blind_context_source_reference_hidden_and_server_reviewer(studio):
    identity=upload(studio).json()['id'];result=state(studio,identity).json()
    assert result['blind_mode'] and not result['human_gold'];assert 'label' not in result['threads'][0]['comments'][0]
    assert 'ai_suggestion' not in json.dumps(result)
    assert annotation(studio,identity,reviewer_id='forged').status_code==403
    assert studio[0][0].get('/api/studio/annotations/'+identity,headers=studio[0][1]).status_code==403

def test_solo_two_round_export_immutable_lineage_not_gold(studio):
    identity=setup(studio)
    assert snapshot(studio,identity).status_code==409
    assert annotation(studio,identity,round=2,round1_revision=1).status_code==422
    for cid in ('c1','c2'):
        first=annotation(studio,identity,cid).json();assert first['revision']==1
        assert annotation(studio,identity,cid,round=2,round1_revision=1).status_code==200
    value=snapshot(studio,identity);assert value.status_code==200;value=value.json()
    assert value['snapshot_state']=='LOCKED' and not value['human_gold'] and value['manifest']['parent_version']==identity
    assert all(r['label_source']=='synthetic_reference' for r in studio[1].rows(value['id']))
    assert all(r['label'] is None for r in studio[1].rows(identity))
    assert studio[1].rows(identity)[0]['user_id']==studio[1].rows(value['id'])[0]['user_id']

def test_changed_round1_invalidates_round2_and_cas_conflict(studio):
    identity=setup(studio);assert annotation(studio,identity).status_code==200
    assert annotation(studio,identity,round=2,round1_revision=1).status_code==200
    assert annotation(studio,identity,revision=0).status_code==409
    assert annotation(studio,identity,revision=1,label='UNCERTAIN',reviewer_notes='Nội dung cần thêm ngữ cảnh.',change_reason='Rà lại phần bối cảnh.').status_code==200
    rows=state(studio,identity).json()['reviews'];old=next(r for r in rows if r['review_round']==2)
    assert not old['round2_valid'] and old['review_state']=='DRAFT'
    assert annotation(studio,identity,round=2,revision=1,round1_revision=1).status_code==409
    assert snapshot(studio,identity).status_code==409

def test_uncertain_requires_notes_and_target_must_be_other_known_user(studio):
    identity=setup(studio)
    assert annotation(studio,identity,label='UNCERTAIN').status_code==422
    assert annotation(studio,identity,directed_at_user_id='unknown',is_directed_attack=True).status_code==422
    assert annotation(studio,identity,label='UNCERTAIN',reviewer_notes='Cần ngữ cảnh bổ sung.').status_code==200

def test_repeated_evidence_requires_same_actor_target_and_time(studio):
    identity=setup(studio);rows=studio[1].rows(identity)
    # Different authors cannot be combined into one repeated actor.
    assert annotation(studio,identity,is_directed_attack=True,directed_at_user_id=rows[1]['user_id']).status_code==200
    result=annotation(studio,identity,'c2',is_directed_attack=True,is_repeated_attack=True,directed_at_user_id=rows[0]['user_id'],evidence_comment_ids=['c1','c2'])
    assert result.status_code==422

def test_real_round2_requires_time_gap_and_no_other_reviewer_confirmation(studio):
    identity=setup(studio);value=StudioReviews(studio[1],identity)
    payload={'thread_id':'STUDIO_DEMO_100','comment_id':'c1','reviewer_id':'same_reviewer','review_round':1,'expected_revision':0,'label':'CLEAN','annotation_status':'ROUND1_DONE'}
    value.save(payload);value.origin='real'
    with pytest.raises(ValueError,match='300 seconds'):value.save({**payload,'review_round':2,'round1_revision':1,'annotation_status':'ROUND2_DONE'})
    with pytest.raises(ValueError,match='own Round 1'):value.save({**payload,'reviewer_id':'other_reviewer','review_round':2,'round1_revision':1,'annotation_status':'ROUND2_DONE'})
