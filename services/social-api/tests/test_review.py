"""Review acceptance uses synthetic accounts/temporary SQLite, never real inference."""
from concurrent.futures import ThreadPoolExecutor
import json
import time

import pytest
from sqlalchemy import func, select

from shieldvi_social.models import Appeal, ContentAudit, ContentReport, ModerationJob, ModerationResult, Post, ReviewClaim
from conftest import migrate
from test_content import actor, comment, post, versions
from test_worker import make_worker, response, setup


def decision(client, staff, row, action="hide", **extra):
    return client.post("/api/v1/moderation/decisions",headers={**staff,"Content-Type":"application/json"},content=json.dumps({
        "entity_type":"comment" if "post_id" in row else "post","entity_id":row["id"],
        "action":action,"reason":"Synthetic review reason",**versions(row),**extra}))


def path(row):
    return f"/api/v1/content/{'comment' if 'post_id' in row else 'post'}/{row['id']}"


def detail_path(row):
    return f"/api/v1/moderation/content/{'comment' if 'post_id' in row else 'post'}/{row['id']}"


@pytest.fixture
def review(authenticated):
    client, author = authenticated
    staff = actor(client,"fixture_moderator","moderator")
    other = actor(client,"fixture_other")
    row = post(client,author,body="<img src=x onerror=alert(1)> Synthetic full text").json()
    return client,author,staff,other,row


@pytest.mark.parametrize("route",["/api/v1/moderation/queue","/api/v1/moderation/jobs"])
def test_queue_rbac(review,route):
    client,author,staff,_,_ = review
    assert client.get(route).status_code == 401
    assert client.get(route,headers=author).status_code == 403
    assert client.get(route,headers=staff).status_code == 200


def test_private_detail_audit_idor_and_no_export_endpoint(review):
    client,author,staff,other,row = review
    for suffix in ("","/audit"):
        assert client.get(detail_path(row)+suffix).status_code == 401
        assert client.get(detail_path(row)+suffix,headers=other).status_code == 403
        assert client.get(detail_path(row)+suffix,headers=author).status_code == 403
        assert client.get(detail_path(row)+suffix,headers=staff).status_code == 200
    assert client.get(path(row)+"/moderation",headers=other).status_code == 404
    assert client.get("/api/v1/me/moderation",headers=other).json()["total"] == 0
    assert client.get("/api/v1/moderation/export",headers=other).status_code == 404


def test_appeal_restore_audit_reload_and_worker_guard(review):
    client,author,staff,other,row = review
    hidden = decision(client,staff,row).json()
    assert hidden["visibility_status"] == "HIDDEN"
    assert client.get(f"/api/v1/posts/{row['id']}",headers=other).status_code == 404
    payload = {**versions(hidden),"reason":"A quotation, please reconsider"}
    assert client.post(path(row)+"/appeals",headers=other,json=payload).status_code == 404
    opened = client.post(path(row)+"/appeals",headers=author,json=payload)
    assert opened.status_code == 201,opened.text
    assert client.post(path(row)+"/appeals",headers=author,json=payload).status_code == 409
    status = client.get(path(row)+"/moderation",headers=author).json()
    assert status["content"]["visibility_status"] == "HIDDEN"
    assert status["appeals"][0]["status"] == "OPEN"
    assert "resolved_by" not in json.dumps(status)
    current = status["content"]
    assert decision(client,staff,current,"restore").status_code == 409
    resolved = client.post(f"/api/v1/moderation/appeals/{opened.json()['id']}/resolve",headers=staff,
        json={**versions(current),"reason":"Quotation confirmed","outcome":"RESTORED"})
    assert resolved.status_code == 200,resolved.text
    row = resolved.json()["content"]
    assert row["visibility_status"] == "PUBLISHED" and row["review_status"] == "RESOLVED"
    assert client.get(f"/api/v1/posts/{row['id']}",headers=other).status_code == 200
    assert client.post(f"/api/v1/moderation/appeals/{opened.json()['id']}/resolve",headers=staff,
        json={**versions(current),"reason":"Duplicate","outcome":"UPHELD"}).status_code == 409
    events = client.get(detail_path(row)+"/audit",headers=staff).json()["items"]
    resolved_event = next(item for item in events if item["event"] == "APPEAL_RESOLVED")
    assert resolved_event["actor_id"] and resolved_event["created_at"]
    assert resolved_event["details"]["outcome"] == "RESTORED"
    assert resolved_event["before_visibility"] == "HIDDEN" and resolved_event["after_visibility"] == "PUBLISHED"
    with client.app.state.sessions() as db:
        job = db.scalar(select(ModerationJob).where(ModerationJob.entity_id == row["id"]))
        assert job.outcome == "STALE_IGNORED" and job.request_json is None


@pytest.mark.parametrize("outcome",["UPHELD","RESTORED"])
def test_appeal_resolve_roles_and_concurrent_review(review,outcome):
    client,author,staff,other,row = review
    hidden = decision(client,staff,row).json()
    appeal = client.post(path(row)+"/appeals",headers=author,json={**versions(hidden),"reason":"Please review"}).json()
    current = client.get(path(row)+"/moderation",headers=author).json()["content"]
    route = f"/api/v1/moderation/appeals/{appeal['id']}/resolve"
    payload = {**versions(current),"reason":"Reviewed","outcome":outcome}
    assert client.post(route,headers=author,json=payload).status_code == 403
    second = actor(client,"fixture_second","admin")
    with ThreadPoolExecutor(2) as pool:
        results = list(pool.map(lambda headers:client.post(route,headers=headers,json=payload).status_code,[staff,second]))
    assert sorted(results) == [200,409]
    with client.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(ContentAudit).where(ContentAudit.event == "APPEAL_RESOLVED")) == 1


def test_reports_dedupe_privacy_no_hide_and_queue(review):
    client,author,staff,other,row = review
    published = decision(client,staff,row,"approve").json()
    payload = {**versions(published),"reason":"Report private reason"}
    for _ in range(2):
        assert client.post(path(row)+"/reports",headers=other,json=payload).json() == {"status":"RECEIVED"}
    assert client.post(path(row)+"/reports",headers=author,json=payload).status_code == 403
    queue = client.get("/api/v1/moderation/queue?tab=reports",headers=staff).json()
    assert queue["total"] == 1 and queue["items"][0]["report_count"] == 1
    detail = client.get(detail_path(row),headers=staff).json()
    assert "reporter_id" not in json.dumps(detail)
    safe = client.get(path(row)+"/moderation",headers=author).json()
    assert "Report private reason" not in json.dumps(safe)
    assert safe["content"]["visibility_status"] == "PUBLISHED"
    decision(client,staff,detail["content"],"hide")
    assert client.get("/api/v1/moderation/queue?tab=reports",headers=staff).json()["total"] == 0
    with client.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(ContentReport)) == 1


def test_hidden_ancestor_report_context_and_restore(review):
    client,author,staff,other,row = review
    published = decision(client,staff,row,"approve").json()
    parent = comment(client,author,row["id"],body="Parent full context").json()
    parent = decision(client,staff,parent,"approve").json()
    child = comment(client,other,row["id"],body="Descendant",parent_id=parent["id"]).json()
    child = decision(client,staff,child,"approve").json()
    parent = decision(client,staff,parent,"hide").json()
    # Third party cannot read or report a public child under a hidden ancestor.
    viewer = actor(client,"fixture_viewer")
    assert client.get(f"/api/v1/comments/{child['id']}",headers=viewer).status_code == 404
    assert client.post(path(child)+"/reports",headers=viewer,json={**versions(child),"reason":"test"}).status_code == 404
    child_detail = client.get(detail_path(child),headers=staff).json()
    assert [item["body"] for item in child_detail["parent_context"]] == [row["body"],"Parent full context"]
    # Own status does not leak the hidden parent's body.
    assert "Parent full context" not in client.get(path(child)+"/moderation",headers=other).text
    assert decision(client,staff,parent,"restore").status_code == 200
    assert client.get(f"/api/v1/comments/{child['id']}",headers=viewer).status_code == 200
    child = decision(client,staff,child,"hide").json()
    parent = client.get(detail_path(parent),headers=staff).json()["content"]
    parent = decision(client,staff,parent,"hide").json()
    decision(client,staff,parent,"restore")
    assert client.get(f"/api/v1/comments/{child['id']}",headers=viewer).status_code == 404


@pytest.mark.parametrize("deleting",[False,True])
def test_edit_delete_close_appeal_and_terminal_guard(review,deleting):
    client,author,staff,_,row = review
    hidden = decision(client,staff,row).json()
    appeal = client.post(path(row)+"/appeals",headers=author,json={**versions(hidden),"reason":"Review"}).json()
    current = client.get(path(row)+"/moderation",headers=author).json()["content"]
    route = f"/api/v1/posts/{row['id']}"
    if deleting:
        result = client.request("DELETE",route,headers=author,json=versions(current))
    else:
        result = client.patch(route,headers=author,json={**versions(current),"body":"New revision"})
    assert result.status_code == 200,result.text
    data = client.get(path(row)+"/moderation",headers=author).json()
    assert data["appeals"][0]["outcome"] == ("AUTHOR_DELETED" if deleting else "SUPERSEDED")
    assert client.post(f"/api/v1/moderation/appeals/{appeal['id']}/resolve",headers=staff,
        json={**versions(result.json()),"reason":"Stale","outcome":"RESTORED"}).status_code == 409
    if deleting:
        assert client.get(detail_path(row),headers=staff).json()["content"]["body"] is None
        assert decision(client,staff,result.json(),"restore").status_code == 409


def test_claim_lease_and_reviewer_concurrency(review,monkeypatch):
    client,author,staff,other,row = review
    second = actor(client,"fixture_second","moderator")
    route = detail_path(row)+"/claim"
    payload = {**versions(row),"reason":"Taking review"}
    assert client.post(route,headers=author,json=payload).status_code == 403
    claimed = client.post(route,headers=staff,json=payload).json()
    assert claimed["content"]["review_status"] == "UNDER_REVIEW"
    current = claimed["content"]
    assert decision(client,second,current,"approve").status_code == 409
    with client.app.state.sessions.begin() as db:
        db.get(ReviewClaim,("post",row["id"])).lease_until = int(time.time())-1
    assert client.get(detail_path(row),headers=second).json()["content"]["review_status"] == "QUEUED"
    assert decision(client,second,current,"approve").status_code == 200


@pytest.mark.parametrize("reason",["","  ","x"*501,"bad\x00reason","bad\ud800reason"])
def test_reason_required_and_version_conflict(review,reason):
    client,author,staff,_,row = review
    assert decision(client,staff,row,reason=reason).status_code == 422
    assert decision(client,staff,row,expected_decision_version=99).status_code == 409


def test_queue_pagination_types_priority_and_missing_ai(review):
    client,author,staff,_,row = review
    parent = decision(client,staff,row,"approve").json()
    child = comment(client,author,row["id"],body="Pending comment").json()
    another = post(client,author,body="Another pending").json()
    queue = client.get("/api/v1/moderation/queue?entity_type=comment&page_size=1",headers=staff).json()
    assert queue["total"] == 1 and queue["items"][0]["content"]["id"] == child["id"]
    assert client.get("/api/v1/moderation/queue?page_size=0",headers=staff).status_code == 422
    detail = client.get(detail_path(child),headers=staff).json()
    assert detail["ai"] is None and detail["job"]["status"] == "QUEUED"
    assert client.get("/api/v1/me/moderation?page_size=1",headers=author).json()["total"] == 3


def test_ai_provenance_false_positive_and_stale_finish(setup):
    client,headers,row,_,_ = setup
    staff = actor(client,"fixture_mod","moderator")
    worker = make_worker(setup,lambda payload:response(payload,.8))
    claim = worker.claim()
    assert worker.finish(claim,response=response(claim.payload,.8))
    detail = client.get(detail_path(row),headers=staff).json()
    assert detail["ai"]["model_threshold"] == .41 and detail["ai"]["ai_label"] == "TOXIC"
    approved = decision(client,staff,detail["content"],"approve",false_positive=True)
    assert approved.status_code == 200
    assert not worker.finish(claim,response=response(claim.payload,.9))
    history = client.get(detail_path(row)+"/audit",headers=staff).json()["items"]
    manual = next(item for item in history if item["event"] == "MANUAL_APPROVE")
    assert manual["details"]["false_positive"] is True
    assert manual["details"]["model_version"] == "stub-not-real-inference"


def test_populated_review_migration_preserves_history_on_downgrade(review):
    client,author,staff,_,row = review
    decision(client,staff,row)
    with pytest.raises(RuntimeError,match="Review history exists"):
        migrate(client.app.state.engine,"downgrade","0003_worker")
    assert client.get(detail_path(row)+"/audit",headers=staff).status_code == 200


def test_claim_on_appeal_expiry_returns_appealed_and_legacy_hide_cannot_bypass(review):
    client,author,staff,_,row = review
    admin = actor(client,"fixture_admin","admin")
    hidden = decision(client,staff,row).json()
    appeal = client.post(path(row)+"/appeals",headers=author,json={**versions(hidden),"reason":"Appeal"}).json()
    current = client.get(detail_path(row),headers=staff).json()["content"]
    claimed = client.post(detail_path(row)+"/claim",headers=staff,json={**versions(current),"reason":"Review appeal"}).json()
    with client.app.state.sessions.begin() as db:
        db.get(ReviewClaim,("post",row["id"])).lease_until = 0
    assert client.get(detail_path(row),headers=staff).json()["content"]["review_status"] == "APPEALED"
    assert client.request("DELETE",f"/api/v1/posts/{row['id']}",headers=admin,
        json={**versions(claimed["content"]),"reason":"Bypass attempt"}).status_code == 409
    assert client.post(f"/api/v1/moderation/appeals/{appeal['id']}/resolve",headers=admin,
        json={**versions(claimed['content']),"reason":"Appeal checked","outcome":"UPHELD"}).status_code == 200


def test_priority_failed_pending_repeated_and_reports(setup):
    client,headers,row,_,_ = setup
    staff = actor(client,"fixture_mod","moderator")
    worker = make_worker(setup)
    claim = worker.claim()
    worker.finish(claim,response=response(claim.payload,.8))
    with client.app.state.sessions.begin() as db:
        record = db.scalar(select(ModerationResult))
        signals = json.loads(record.signals_json)
        # Synthetic repeated fixture for ordering only, not precision evidence.
        signals["suspected_repeated_harassment"] = True
        record.signals_json = json.dumps(signals)
    pending = post(client,headers,body="Pending priority").json()
    failed = post(client,headers,body="Failed priority").json()
    with client.app.state.sessions.begin() as db:
        job = db.scalar(select(ModerationJob).where(ModerationJob.entity_id == failed["id"]))
        job.status = "FAILED_PERMANENTLY"
    queued = client.get("/api/v1/moderation/queue",headers=staff).json()["items"]
    assert [item["content"]["id"] for item in queued] == [failed["id"],pending["id"],row["id"]]
    assert [item["priority"] for item in queued] == [1,2,4]


def test_manual_claim_prevents_inflight_ai_publish(setup):
    client,headers,row,_,_ = setup
    staff = actor(client,"fixture_mod","moderator")
    worker = make_worker(setup)
    claim = worker.claim()
    claimed = client.post(detail_path(row)+"/claim",headers=staff,json={**versions(row),"reason":"Manual review"})
    assert claimed.status_code == 200
    assert not worker.finish(claim,response=response(claim.payload))
    current = client.get(f"/api/v1/posts/{row['id']}",headers=headers).json()
    assert current["visibility_status"] == "PENDING_MODERATION" and current["review_status"] == "UNDER_REVIEW"


def test_held_descendant_not_leaked_through_feed_counts_or_mine(review):
    client,author,staff,other,row = review
    with client.app.state.sessions.begin() as db:
        db.get(Post,row["id"]).visibility_status = "HELD_FOR_REVIEW"
    assert client.get("/api/v1/feed",headers=other).json()["total"] == 0
    assert client.get(path(row)+"/moderation",headers=other).status_code == 404
    assert client.get("/api/v1/me/moderation",headers=other).json()["total"] == 0
    assert client.post(path(row)+"/reports",headers=other,json={**versions(row),"reason":"Guess"}).status_code == 404
    assert client.post(path(row)+"/appeals",headers=author,json={**versions(row),"reason":"Held review"}).status_code == 201
