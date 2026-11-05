"""Identity is server-derived and reply context is never an attack verdict."""
import json
from pathlib import Path
from sqlalchemy import select
from test_live_api import live,send
from test_content import post,actor,key_headers
from shieldvi_social.live_identity import LiveIdentity
from shieldvi_social.models import Comment

def user(client,headers):return client.get('/api/v1/me',headers=headers).json()

def test_authenticated_live_feed_shows_usernames_without_private_account_fields(live):
    c,owner,other,_,thread,_=live;name=user(c,owner)['username']
    assert c.get('/api/live/feed').status_code==401
    response=c.get('/api/live/feed',headers=other);assert response.status_code==200
    row=response.json()['items'][0];assert row['id']==thread['id'] and row['author_username']==name
    assert not {'email','password_hash','token','role','session'}&row.keys()

def test_pending_private_post_cannot_leak_author_metadata_through_feed_or_snapshot(live):
    c,owner,other,_,_,_=live;private=post(c,owner,'Only author can see this pending post').json()
    assert private['id'] not in {r['id'] for r in c.get('/api/live/feed',headers=other).json()['items']}
    assert c.get(f"/api/live/threads/{private['id']}/snapshot",headers=other).status_code==404

def test_reply_name_and_id_are_derived_from_authorized_parent_not_client_claim(live):
    c,owner,other,_,thread,worker=live;parent=send(live).json();assert worker.run_once()
    a=user(c,owner);b=user(c,other)
    reply=send(live,headers=other,body='Thanks for the feedback',parent=parent['id'])
    assert reply.status_code==201;row=reply.json()
    assert (row['author_id'],row['author_username'])==(b['id'],b['username'])
    assert (row['reply_to_user_id'],row['reply_to_username'])==(a['id'],a['username'])
    assert row['body']=='Thanks for the feedback' and row['parent_id']==parent['id']
    assert worker.run_once()
    snapshot=c.get(f"/api/live/threads/{thread['id']}/snapshot",headers=owner).json()
    saved=next(r for r in snapshot['comments']['items'] if r['id']==row['id'])
    assert saved['reply_to_username']==a['username'] and snapshot['post']['author_username']==a['username']
    forged=c.post(f"/api/live/threads/{thread['id']}/messages",headers=key_headers(other),
        json={'body':'Forged target','parent_id':parent['id'],'reply_to_user_id':b['id'],'author_username':'forged'})
    assert forged.status_code==422

def test_hidden_parent_identity_is_not_exposed_to_non_author_reply_viewer(live):
    c,owner,other,_,thread,worker=live;parent=send(live).json();assert worker.run_once()
    child=send(live,headers=other,parent=parent['id']).json();assert worker.run_once()
    with c.app.state.sessions.begin() as db:db.get(Comment,parent['id']).visibility_status='HIDDEN'
    snapshot=c.get(f"/api/live/threads/{thread['id']}/snapshot",headers=other).json()
    row=next(r for r in snapshot['comments']['items'] if r['id']==child['id'])
    assert row['reply_to_user_id'] is None and row['reply_to_username'] is None

def test_metadata_schema_matches_export():
    path=Path(__file__).resolve().parents[3]/'contracts/live_content_identity.schema.json'
    assert json.loads(path.read_text(encoding='utf-8'))==LiveIdentity.model_json_schema()
