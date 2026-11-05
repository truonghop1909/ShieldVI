import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, func, select
from sqlalchemy.exc import IntegrityError

from shieldvi_social.main import create_app
from shieldvi_social.models import Comment, ContentAudit, ModerationJob, Post, User
from conftest import login, register


def key_headers(headers, key=None):
    return {**headers, "Idempotency-Key": key or str(uuid4())}


def post(client, headers, body="Fixture post", key=None):
    return client.post("/api/v1/posts", headers=key_headers(headers, key), json={"body": body})


def comment(client, headers, post_id, parent_id=None, body="Fixture comment", key=None):
    return client.post(f"/api/v1/posts/{post_id}/comments", headers=key_headers(headers, key),
                       json={"body": body, "parent_id": parent_id})


def versions(row):
    return {"expected_revision": row["content_revision"], "expected_decision_version": row["decision_version"]}


def remove(client, headers, kind, row, **extra):
    return client.request("DELETE", f"/api/v1/{kind}/{row['id']}", headers=headers,
                          json={**versions(row), **extra})


def actor(client, name, role="user"):
    assert register(client, username=name, email=f"{name}@example.com").status_code == 201
    if role != "user":
        with client.app.state.sessions.begin() as db:
            db.scalar(select(User).where(User.username == name)).role = role
    return {"Authorization": "Bearer " + login(client, name).json()["access_token"]}


def fixture_visibility(client, model, row_id, state="PUBLISHED"):
    """Test-only DB state setup, not evidence of a production publish workflow."""
    with client.app.state.sessions.begin() as db:
        row = db.get(model, row_id)
        row.visibility_status = state


@pytest.fixture
def actors(authenticated):
    client, owner = authenticated
    return client, owner, actor(client, "other_fixture")


def test_create_post_comment_reply_and_atomic_outbox(authenticated):
    client, headers = authenticated
    created = post(client, headers, body="  Nguyên bản tiếng Việt 🙂  ")
    assert created.status_code == 201, created.text
    p = created.json()
    assert p["body"] == "  Nguyên bản tiếng Việt 🙂  "
    assert p["visibility_status"] == "PENDING_MODERATION"
    assert p["risk_tier"] == "UNKNOWN" and p["review_status"] == "QUEUED"
    c = comment(client, headers, p["id"])
    assert c.status_code == 201, c.text
    reply = comment(client, headers, p["id"], c.json()["id"])
    assert reply.status_code == 201, reply.text
    assert reply.json()["parent_id"] == c.json()["id"]
    assert client.get(f"/api/v1/posts/{p['id']}", headers=headers).status_code == 200
    listed = client.get(f"/api/v1/posts/{p['id']}/comments", headers=headers).json()
    assert listed["total"] == 2
    assert client.get("/api/v1/feed", headers=headers).json()["total"] == 0
    with client.app.state.sessions() as db:
        jobs = db.scalars(select(ModerationJob)).all()
        assert len(jobs) == 3 and all(job.status == "QUEUED" for job in jobs)
        assert len({job.request_id for job in jobs}) == 3
        assert all(job.content_revision == 1 and job.expected_decision_version == 0 for job in jobs)
        assert all(job.policy_version is None for job in jobs)  # No active policy yet.
        assert db.scalar(select(func.count()).select_from(ContentAudit)) == 3


@pytest.mark.parametrize("kind", ["post", "comment"])
def test_outbox_failure_rolls_back_content_and_audit(authenticated, kind):
    client, headers = authenticated
    p = post(client, headers).json() if kind == "comment" else None

    def fail(*_):
        raise RuntimeError("injected outbox failure")

    event.listen(ModerationJob, "before_insert", fail)
    try:
        with pytest.raises(RuntimeError, match="outbox failure"):
            comment(client, headers, p["id"]) if p else post(client, headers)
    finally:
        event.remove(ModerationJob, "before_insert", fail)
    with client.app.state.sessions() as db:
        model = Comment if p else Post
        assert db.scalar(select(func.count()).select_from(model)) == 0
        assert db.scalar(select(func.count()).select_from(ModerationJob)) == (1 if p else 0)
        assert db.scalar(select(func.count()).select_from(ContentAudit)) == (1 if p else 0)


def test_idempotent_create_and_conflicting_payload(actors):
    client, owner, other = actors
    key = str(uuid4())
    first, replay = post(client, owner, key=key), post(client, owner, key=key)
    assert first.status_code == 201 and replay.status_code == 200
    assert replay.headers["idempotency-replayed"] == "true"
    assert first.json() == replay.json()
    assert post(client, owner, body="different", key=key).status_code == 409
    assert post(client, other, key=key).status_code == 201  # Scoped to author.
    p = first.json()
    ckey = str(uuid4())
    first_c = comment(client, owner, p["id"], key=ckey)
    assert first_c.status_code == 201
    assert comment(client, owner, p["id"], key=ckey).status_code == 200
    assert comment(client, owner, p["id"], parent_id=first_c.json()["id"], key=ckey).status_code == 409
    with client.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(ModerationJob)) == 3


def test_concurrent_create_one_job_and_audit(authenticated):
    client, headers = authenticated
    key = str(uuid4())
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: post(client, headers, key=key), range(2)))
    assert sorted(r.status_code for r in results) == [200, 201]
    assert results[0].json()["id"] == results[1].json()["id"]
    with client.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(Post)) == 1
        assert db.scalar(select(func.count()).select_from(ModerationJob)) == 1
        assert db.scalar(select(func.count()).select_from(ContentAudit)) == 1


@pytest.mark.parametrize("kind", ["posts", "comments"])
def test_edit_revision_jobs_audit_and_soft_delete(authenticated, kind):
    client, headers = authenticated
    p = post(client, headers).json()
    row = p if kind == "posts" else comment(client, headers, p["id"]).json()
    model = Post if kind == "posts" else Comment
    fixture_visibility(client, model, row["id"])
    edited = client.patch(f"/api/v1/{kind}/{row['id']}", headers=headers,
                          json={"body": "Edited text", **versions(row)})
    assert edited.status_code == 200, edited.text
    new = edited.json()
    assert new["content_revision"] == 2 and new["decision_version"] == 1
    assert new["visibility_status"] == "PENDING_MODERATION"
    with client.app.state.sessions() as db:
        jobs = db.scalars(select(ModerationJob).where(ModerationJob.entity_id == row["id"]).order_by(ModerationJob.content_revision)).all()
        assert [(j.content_revision, j.status, j.outcome) for j in jobs] == [(1, "SUCCEEDED", "STALE_IGNORED"), (2, "QUEUED", None)]
        assert jobs[1].expected_decision_version == 1
    assert client.patch(f"/api/v1/{kind}/{row['id']}", headers=headers,
        json={"body": "Stale edit", **versions(row)}).status_code == 409
    deleted = remove(client, headers, kind, new)
    assert deleted.status_code == 200, deleted.text
    tombstone = deleted.json()
    assert tombstone["visibility_status"] == "DELETED_BY_AUTHOR" and tombstone["body"] is None
    assert client.get(f"/api/v1/{kind}/{row['id']}", headers=headers).json()["body"] is None
    assert client.patch(f"/api/v1/{kind}/{row['id']}", headers=headers,
        json={"body": "Resurrect", **versions(tombstone)}).status_code == 409
    assert remove(client, headers, kind, tombstone).json() == tombstone
    with client.app.state.sessions() as db:
        events = db.scalars(select(ContentAudit).where(ContentAudit.entity_id == row["id"]).order_by(ContentAudit.decision_version)).all()
        assert [a.event for a in events] == ["CREATE", "EDIT", "AUTHOR_DELETE"]
        assert all(a.actor_id == row["author_id"] and a.reason and a.created_at for a in events)


@pytest.mark.parametrize("kind", ["posts", "comments"])
def test_owner_idor_and_admin_permissions(actors, kind):
    client, owner, other = actors
    p = post(client, owner).json()
    row = p if kind == "posts" else comment(client, owner, p["id"]).json()
    assert client.get(f"/api/v1/{kind}/{row['id']}", headers=other).status_code == 404
    assert remove(client, other, kind, row).status_code == 404
    fixture_visibility(client, Post, p["id"])
    if kind == "comments":
        fixture_visibility(client, Comment, row["id"])
    assert client.get(f"/api/v1/{kind}/{row['id']}", headers=other).status_code == 200
    assert client.patch(f"/api/v1/{kind}/{row['id']}", headers=other,
        json={"body": "Hijacked", **versions(row)}).status_code == 403
    assert remove(client, other, kind, row).status_code == 403
    admin = actor(client, "admin_fixture", "admin")
    assert client.patch(f"/api/v1/{kind}/{row['id']}", headers=admin,
        json={"body": "Admin rewriting user text", **versions(row)}).status_code == 403
    assert remove(client, admin, kind, row).status_code == 422
    hidden = remove(client, admin, kind, row, reason="Fixture community rule violation")
    assert hidden.status_code == 200, hidden.text
    assert hidden.json()["visibility_status"] == "HIDDEN"
    assert client.get(f"/api/v1/{kind}/{row['id']}", headers=other).status_code == 404
    with client.app.state.sessions() as db:
        action = db.scalar(select(ContentAudit).where(ContentAudit.entity_id == row["id"], ContentAudit.event == "ADMIN_HIDE"))
        assert action.actor_role == "admin" and action.reason == "Fixture community rule violation"


def test_pending_hidden_deleted_and_flagged_feed_pagination(actors):
    client, owner, other = actors
    rows = [post(client, owner, body=f"post-{i}").json() for i in range(7)]
    states = ["PUBLISHED", "PUBLISHED_FLAGGED", "PUBLISHED", "PENDING_MODERATION", "HELD_FOR_REVIEW", "HIDDEN", "DELETED_BY_AUTHOR"]
    with client.app.state.sessions.begin() as db:
        for i, row in enumerate(rows):
            obj = db.get(Post, row["id"])
            obj.visibility_status = states[i]
            obj.created_at = 1000  # Tie-breaker must be deterministic.
    first = client.get("/api/v1/feed?page_size=2", headers=other).json()
    second = client.get("/api/v1/feed?page_size=2&page=2", headers=other).json()
    assert first["total"] == second["total"] == 3
    got = first["items"] + second["items"]
    assert [r["id"] for r in got] == sorted([r["id"] for r in rows[:3]], reverse=True)
    assert all(r["visibility_status"] == "PUBLISHED" and r["risk_tier"] is None and r["review_status"] is None for r in got)
    assert client.get("/api/v1/feed?page=3&page_size=2", headers=other).json()["items"] == []
    assert client.get("/api/v1/feed", headers=owner).json()["total"] == 3  # Feed never includes own pending.


def test_ancestor_mask_restore_and_private_child_read(actors):
    client, owner, other = actors
    p = post(client, owner).json()
    parent = comment(client, owner, p["id"]).json()
    child = comment(client, owner, p["id"], parent["id"]).json()
    grandchild = comment(client, owner, p["id"], child["id"]).json()
    for model, row in [(Post,p), (Comment,parent), (Comment,child), (Comment,grandchild)]:
        fixture_visibility(client, model, row["id"])
    url = f"/api/v1/posts/{p['id']}/comments"
    assert client.get(url, headers=other).json()["total"] == 3
    fixture_visibility(client, Comment, parent["id"], "HIDDEN")
    assert client.get(url, headers=other).json()["total"] == 0
    assert client.get(f"/api/v1/comments/{grandchild['id']}", headers=other).status_code == 404
    assert client.get(f"/api/v1/comments/{child['id']}", headers=owner).status_code == 200
    fixture_visibility(client, Comment, child["id"], "HIDDEN")
    fixture_visibility(client, Comment, parent["id"], "PUBLISHED")
    assert client.get(url, headers=other).json()["total"] == 1
    fixture_visibility(client, Comment, child["id"], "PUBLISHED")
    assert client.get(url, headers=other).json()["total"] == 3
    fixture_visibility(client, Post, p["id"], "HIDDEN")
    assert client.get(url, headers=other).status_code == 404
    assert client.get(f"/api/v1/comments/{grandchild['id']}", headers=other).status_code == 404
    with client.app.state.sessions() as db:
        assert db.get(Comment, grandchild["id"]).visibility_status == "PUBLISHED"


def test_cross_post_missing_deleted_and_inaccessible_parent(actors):
    client, owner, other = actors
    a, b = post(client, owner).json(), post(client, owner).json()
    parent = comment(client, owner, a["id"]).json()
    assert comment(client, owner, b["id"], parent["id"]).status_code == 404
    assert comment(client, owner, a["id"], str(uuid4())).status_code == 404
    fixture_visibility(client, Post, a["id"])
    assert comment(client, other, a["id"], parent["id"]).status_code == 404
    assert remove(client, owner, "comments", parent).status_code == 200
    assert comment(client, owner, a["id"], parent["id"]).status_code == 404
    assert remove(client, owner, "posts", a).status_code == 200
    assert comment(client, owner, a["id"]).status_code == 409


@pytest.mark.parametrize("body", ["", "   \n\t", "a" * 8001, "nul\x00fixture"])
def test_body_validation(authenticated, body):
    client, headers = authenticated
    assert post(client, headers, body=body).status_code == 422


def test_malformed_unicode_body_rejected(authenticated):
    client, headers = authenticated
    response = client.post("/api/v1/posts", headers={**key_headers(headers), "Content-Type":"application/json"},
        content=json.dumps({"body":"invalid-surrogate-\ud800"}))
    assert response.status_code == 422
    assert "invalid-surrogate" not in response.text


@pytest.mark.parametrize("fields", [{"author_id":str(uuid4())}, {"visibility_status":"PUBLISHED"}, {"id":str(uuid4())}, {"risk_tier":"LOW"}])
def test_no_client_author_state_or_id_injection(authenticated, fields):
    client, headers = authenticated
    response = client.post("/api/v1/posts", headers=key_headers(headers), json={"body":"fixture", **fields})
    assert response.status_code == 422


def test_html_and_unicode_stored_as_text_with_bounded_request(authenticated):
    client, headers = authenticated
    body = '<script>alert("fixture")</script>'
    assert post(client, headers, body=body).json()["body"] == body
    response = post(client, headers, body="🙂" * 8000)
    assert response.status_code == 201, response.text
    assert client.post("/api/v1/posts", headers=key_headers(headers), content="x" * 131073).status_code == 413


@pytest.mark.parametrize("query", ["page=0", "page=-1", "page=10001", "page_size=0", "page_size=51", "page_size=abc"])
def test_query_size_boundaries(authenticated, query):
    client, headers = authenticated
    p = post(client, headers).json()
    assert client.get("/api/v1/feed?" + query, headers=headers).status_code == 422
    assert client.get(f"/api/v1/posts/{p['id']}/comments?" + query, headers=headers).status_code == 422


def test_anonymous_content_requests_are_rejected(client):
    target = str(uuid4())
    for method, url, data in [
        ("GET","/api/v1/feed",None), ("GET",f"/api/v1/posts/{target}",None),
        ("GET",f"/api/v1/comments/{target}",None),
        ("POST","/api/v1/posts",{"body":"unauthenticated"}),
        ("PATCH",f"/api/v1/posts/{target}",{"body":"x","expected_revision":1,"expected_decision_version":0}),
        ("DELETE",f"/api/v1/comments/{target}",{"expected_revision":1,"expected_decision_version":0}),
    ]:
        assert client.request(method, url, json=data, headers={"Idempotency-Key":str(uuid4())}).status_code == 401


def test_parent_cannot_be_changed_to_create_cycle(authenticated):
    client, headers = authenticated
    p = post(client, headers).json()
    parent = comment(client, headers, p["id"]).json()
    child = comment(client, headers, p["id"], parent["id"]).json()
    result = client.patch(f"/api/v1/comments/{parent['id']}", headers=headers,
        json={"body":"cycle attempt", "parent_id":child["id"], **versions(parent)})
    assert result.status_code == 422
    with pytest.raises(IntegrityError), client.app.state.sessions.begin() as db:
        db.get(Comment, parent["id"]).parent_id = parent["id"]


def test_db_rejects_cross_post_parent(authenticated):
    client, headers = authenticated
    a,b = post(client, headers).json(),post(client, headers).json()
    parent = comment(client, headers, a["id"]).json()
    child = comment(client, headers, b["id"]).json()
    with pytest.raises(IntegrityError), client.app.state.sessions.begin() as db:
        db.get(Comment, child["id"]).parent_id = parent["id"]


def test_content_limit_and_idempotent_retry(authenticated, settings):
    client, headers = authenticated
    limited = create_app(replace(settings, content_rate_limit=1))
    with TestClient(limited) as capped:
        key = str(uuid4())
        first = post(capped, headers, key=key)
        assert first.status_code == 201
        assert post(capped, headers, key=key).status_code == 200
        assert post(capped, headers).status_code == 429
    with TestClient(create_app(replace(settings, content_rate_limit=1))) as restarted:
        assert post(restarted, headers).status_code == 429


def test_reply_depth_bound(authenticated, settings):
    client, headers = authenticated
    with TestClient(create_app(replace(settings, content_rate_limit=100))) as deep:
        p = post(deep, headers).json()
        row = comment(deep, headers, p["id"]).json()
        for _ in range(32):
            response = comment(deep, headers, p["id"], row["id"])
            assert response.status_code == 201, response.text
            row = response.json()
        assert comment(deep, headers, p["id"], row["id"]).status_code == 422


def test_concurrent_edit_rejects_stale_versions(authenticated):
    client, headers = authenticated
    row = post(client, headers).json()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda i: client.patch(f"/api/v1/posts/{row['id']}", headers=headers,
            json={"body":f"edit-{i}", **versions(row)}), range(2)))
    assert sorted(response.status_code for response in results) == [200, 409]
    with client.app.state.sessions() as db:
        assert db.get(Post, row["id"]).content_revision == 2
        assert db.scalar(select(func.count()).select_from(ModerationJob)) == 2


def test_replay_after_delete_returns_tombstone_without_new_job(authenticated):
    client, headers = authenticated
    key = str(uuid4())
    row = post(client, headers, key=key).json()
    assert remove(client, headers, "posts", row).status_code == 200
    replay = post(client, headers, key=key)
    assert replay.status_code == 200 and replay.json()["body"] is None
    assert replay.json()["visibility_status"] == "DELETED_BY_AUTHOR"
    with client.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(ModerationJob)) == 1
        assert db.scalar(select(func.count()).select_from(ContentAudit)) == 2


def test_comment_pagination_counts_only_visible_items(actors):
    client, owner, other = actors
    p = post(client, owner).json()
    rows = [comment(client, owner, p["id"], body=f"comment-{i}").json() for i in range(5)]
    fixture_visibility(client, Post, p["id"])
    with client.app.state.sessions.begin() as db:
        for i, row in enumerate(rows):
            obj = db.get(Comment, row["id"])
            obj.visibility_status = "PUBLISHED" if i < 3 else "HIDDEN"
            obj.created_at = 1000
    url = f"/api/v1/posts/{p['id']}/comments"
    first = client.get(url+"?page_size=2", headers=other).json()
    second = client.get(url+"?page_size=2&page=2", headers=other).json()
    assert first["total"] == second["total"] == 3
    assert [r["id"] for r in first["items"]+second["items"]] == sorted(r["id"] for r in rows[:3])


def test_decision_version_guard_without_revision_change(authenticated):
    client, headers = authenticated
    row = post(client, headers).json()
    with client.app.state.sessions.begin() as db:
        obj = db.get(Post, row["id"])
        obj.decision_version += 1  # Test-only simulation of a newer human decision.
        obj.visibility_status = "HIDDEN"
    response = client.patch(f"/api/v1/posts/{row['id']}", headers=headers,
        json={"body":"stale overwrite", **versions(row)})
    assert response.status_code == 409
    with client.app.state.sessions() as db:
        assert db.get(Post, row["id"]).body == row["body"]


def test_content_preflight_supports_mutations_and_idempotency(client):
    for method in ("POST", "PATCH", "DELETE"):
        result = client.options("/api/v1/posts", headers={"Origin":"http://localhost:5173",
            "Access-Control-Request-Method":method,
            "Access-Control-Request-Headers":"authorization,content-type,idempotency-key"})
        assert result.status_code == 200
        assert result.headers["access-control-allow-origin"] == "http://localhost:5173"


def test_staff_can_read_pending_but_moderator_cannot_remove_others(actors):
    client, owner, other = actors
    row = post(client, owner).json()
    staff = actor(client, "moderator_fixture", "moderator")
    assert client.get(f"/api/v1/posts/{row['id']}", headers=staff).status_code == 200
    assert remove(client, staff, "posts", row, reason="No delete permission in T009").status_code == 403
    assert client.get(f"/api/v1/posts/{row['id']}", headers=other).status_code == 404
