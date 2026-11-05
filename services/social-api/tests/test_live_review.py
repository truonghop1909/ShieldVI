from test_live_api import live,send
from test_content import versions

def test_staff_poll_requires_role_and_excludes_body(live):
    c,owner,_,staff,_,_=live
    send(live,body='PRIVATE_BODY_NOT_IN_EVENTS')
    assert c.get('/api/live/moderator/events/poll',headers=owner).status_code==403
    result=c.get('/api/live/moderator/events/poll',headers=staff)
    assert result.status_code==200 and result.json()['items']
    assert 'PRIVATE_BODY_NOT_IN_EVENTS' not in result.text

def test_clarification_audited_without_visibility_change_and_stale_rejected(live):
    c,owner,_,staff,_,worker=live;row=send(live).json();worker.run_once()
    row=c.get('/api/v1/moderation/content/comment/'+row['id'],headers=staff).json()['content']
    path='/api/live/moderator/content/comment/'+row['id']+'/clarification'
    body={**versions(row),'reason':'Please clarify the context; no removal requested.'}
    assert c.post(path,headers=owner,json=body).status_code==403
    result=c.post(path,headers=staff,json=body)
    assert result.status_code==200 and result.json()['visibility_status']==row['visibility_status']
    assert result.json()['decision_version']==row['decision_version']+1
    assert c.post(path,headers=staff,json=body).status_code==409
    audit=c.get('/api/v1/moderation/content/comment/'+row['id']+'/audit',headers=staff).json()
    assert any(r['event']=='REQUEST_CLARIFICATION' and r['actor_role']=='admin' and r['reason']==body['reason'] for r in audit['items'])

def test_clarification_reason_required(live):
    c,_,_,staff,_,_=live;row=send(live).json()
    assert c.post('/api/live/moderator/content/comment/'+row['id']+'/clarification',headers=staff,json={**versions(row),'reason':' '}).status_code==422
