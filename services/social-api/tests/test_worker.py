from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import datetime, timezone
import importlib
import json
from pathlib import Path
import secrets
import sys

import httpx
import pytest
from pydantic import SecretStr
from sqlalchemy import event, func, select

from shieldvi_social.ai_client import AIClient, AIError, WorkerSettings
from shieldvi_social.models import Comment, ContentAudit, ModerationJob, ModerationResult, Post, User
from shieldvi_social.moderation_contract import ModerationRequest, ModerationResponse
from shieldvi_social.worker import POLICY_VERSION, Worker, queue_stats
from conftest import login, register
from conftest import migrate
from test_content import actor, comment, post, versions


class Clock:
    def __init__(self):
        import time
        self.value = int(time.time()) + 5
    def __call__(self):
        return self.value


def response(payload, score=.02, **changes):
    data = dict(schema_version="1.0", request_id=payload.request_id, content_id=payload.content_id,
        content_revision=payload.content_revision, model_name="SYNTHETIC STUB", model_version="stub-not-real-inference",
        lexicon_version="fixture", analyzed_at=datetime.now(timezone.utc), model_threshold=.41,
        toxicity_score=score, ai_label="TOXIC" if score >= .41 else "CLEAN",
        lexical_review_recommended=False, directed_insult_candidate=False, reported_or_apology_context=False,
        lexical_signals=[], target_evidence={"target_user_id":None,"method":"undetermined","confidence":"none"},
        suspected_repeated_harassment=False, evidence=[], suggested_action="needs_review" if score >= .41 else "approve",
        decision_authority="advisory", limitations=["Synthetic scores; not model inference"])
    return ModerationResponse.model_validate({**data, **changes})


@pytest.fixture
def setup(authenticated):
    client, headers = authenticated
    row = post(client, headers).json()
    clock = Clock()
    settings = WorkerSettings(service_token=SecretStr(secrets.token_urlsafe(32)))
    return client, headers, row, clock, settings


def make_worker(setup, handler=None):
    client, _, _, clock, settings = setup
    class FakeAI:
        def moderate(self, payload):
            return handler(payload) if handler else response(payload)
    return Worker(client.app.state.engine, settings, FakeAI(), clock, jitter=lambda:0)


def get_job(client, entity_id):
    with client.app.state.sessions() as db:
        return db.scalar(select(ModerationJob).where(ModerationJob.entity_id == entity_id).order_by(ModerationJob.content_revision.desc()))


@pytest.mark.parametrize("score,flags,state,risk", [
    (.02,{},"PUBLISHED","LOW"), (.9,{},"PUBLISHED_FLAGGED","REVIEW"),
    (.41,{},"PUBLISHED_FLAGGED","REVIEW"),
    (.02,{"lexical_review_recommended":True},"PUBLISHED_FLAGGED","REVIEW"),
    (.02,{"reported_or_apology_context":True,"lexical_review_recommended":True},"PUBLISHED_FLAGGED","REVIEW"),
])
def test_shadow_policy_result_and_system_audit(setup, score, flags, state, risk):
    client, headers, row, _, _ = setup
    worker = make_worker(setup, lambda payload: response(payload, score, **flags))
    assert worker.run_once()
    assert not worker.run_once()
    result = client.get(f"/api/v1/posts/{row['id']}", headers=headers).json()
    assert result["visibility_status"] == state and result["risk_tier"] == risk
    assert result["decision_version"] == 1
    with client.app.state.sessions() as db:
        record = db.scalar(select(ModerationResult))
        job = db.get(ModerationJob, record.job_id)
        assert record.score == score and record.policy_version == POLICY_VERSION
        assert job.status == "SUCCEEDED" and job.request_json is None and job.claim_token is None
        audit = db.scalar(select(ContentAudit).where(ContentAudit.event == "AI_APPLIED"))
        assert audit.actor_id is None and audit.actor_type == "system" and audit.actor_role == "worker"
        assert audit.before_visibility == "PENDING_MODERATION" and audit.after_visibility == state


@pytest.mark.parametrize("code,retryable", [("AI_TIMEOUT",True),("AI_HTTP_503",True),("AI_INVALID_SCHEMA",True),("AI_HTTP_401",False),("AI_HTTP_422",False)])
def test_failure_never_publishes_and_bounded_retry(setup, code, retryable):
    client, headers, row, clock, _ = setup
    def fail(_):
        raise AIError(code,retryable)
    worker = make_worker(setup, fail)
    assert worker.run_once()
    job = get_job(client,row["id"])
    assert job.status == ("RETRY_WAIT" if retryable else "FAILED_PERMANENTLY")
    assert job.last_error == code
    assert client.get(f"/api/v1/posts/{row['id']}",headers=headers).json()["visibility_status"] == "PENDING_MODERATION"
    if retryable:
        assert job.next_retry_at == clock.value+5 and job.request_json
        assert not worker.run_once()
        for delay in (5,30):
            clock.value += delay
            assert worker.run_once()
        assert get_job(client,row["id"]).status == "FAILED_PERMANENTLY"
    assert queue_stats(client.app.state.engine,clock.value)["model_availability"] == "down"


def test_ai_recovery_reuses_snapshot_request_and_publishes_once(setup):
    client, headers, row, clock, _ = setup
    seen = []
    def flaky(payload):
        seen.append(payload.model_dump_json())
        if len(seen)==1:
            raise AIError("AI_HTTP_503",True)
        return response(payload)
    worker = make_worker(setup,flaky)
    worker.run_once(); clock.value += 5
    # New process-equivalent Worker, same DB; retry metadata/request survives.
    restarted = Worker(client.app.state.engine,worker.settings,worker.ai,clock,jitter=lambda:0)
    assert restarted.run_once() and seen[0]==seen[1]
    assert get_job(client,row["id"]).total_attempts == 2
    stats=queue_stats(client.app.state.engine,clock.value)
    assert stats["queue_size"]==0 and stats["retry_attempts"]==1 and stats["expired_leases"]==0
    assert client.get("/api/v1/feed",headers=headers).json()["total"] == 1


def test_expired_lease_reclaim_and_old_worker_cannot_finalize(setup):
    client, _, row, clock, settings = setup
    first,second = make_worker(setup),make_worker(setup)
    old = first.claim()
    assert second.claim() is None
    clock.value += settings.lease_seconds+1
    new = second.claim()
    assert new.job_id==old.job_id and new.claim_token!=old.claim_token
    assert new.payload.model_dump_json()==old.payload.model_dump_json()
    assert not first.finish(old,response(old.payload))
    assert second.finish(new,response(new.payload))
    with client.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(ModerationResult))==1
        assert db.scalar(select(func.count()).select_from(ContentAudit).where(ContentAudit.event=="AI_APPLIED"))==1


def test_concurrent_claim_only_one_owner(setup):
    worker = make_worker(setup)
    with ThreadPoolExecutor(max_workers=2) as pool:
        claims=list(pool.map(lambda _:worker.claim(),range(2)))
    assert sum(claim is not None for claim in claims)==1


def test_expired_max_attempt_crash_moves_to_manual_queue(setup):
    client, _, row, clock, settings = setup
    worker=make_worker(setup)
    for _ in range(settings.max_attempts):
        assert worker.claim() is not None
        clock.value += settings.lease_seconds+1
    assert worker.claim() is None
    job=get_job(client,row["id"])
    assert job.status=="FAILED_PERMANENTLY" and job.last_error=="ATTEMPTS_EXHAUSTED"
    assert queue_stats(client.app.state.engine,clock.value)["failed_jobs"][0]["job_id"]==job.id


@pytest.mark.parametrize("mutation",["edit","delete","manual_approve","manual_hide"])
def test_late_success_or_error_never_overwrites_newer_decision(setup, mutation):
    client, headers, row, _, _ = setup
    worker=make_worker(setup); claim=worker.claim()
    if mutation=="edit":
        updated=client.patch(f"/api/v1/posts/{row['id']}",headers=headers,json={"body":"new revision",**versions(row)}).json()
    elif mutation=="delete":
        updated=client.request("DELETE",f"/api/v1/posts/{row['id']}",headers=headers,json=versions(row)).json()
    else:
        staff=actor(client,"worker_staff","moderator")
        result=client.post("/api/v1/moderation/decisions",headers=staff,json={
            "entity_type":"post","entity_id":row["id"],"action":"approve" if mutation=="manual_approve" else "hide",
            "reason":"Synthetic manual decision while AI is unavailable",**versions(row)})
        assert result.status_code==200,result.text
        updated=result.json()
    assert not worker.finish(claim,response(claim.payload))
    assert not worker.finish(claim,error=AIError("AI_TIMEOUT",True))
    final=client.get(f"/api/v1/posts/{row['id']}",headers=headers).json()
    assert final["visibility_status"]==updated["visibility_status"] and final["decision_version"]==updated["decision_version"]
    assert get_job(client,row["id"]).request_json is None


def test_retry_failed_requires_staff_reason_and_preserves_attempt_history(setup):
    client,headers,row,clock,_=setup
    def fail(_):
        raise AIError("AI_HTTP_401",False)
    worker=make_worker(setup,fail); worker.run_once()
    job=get_job(client,row["id"]); original_request=job.request_id
    data={"reason":"Credentials fixed; retry synthetic job",**versions(row)}
    assert client.post(f"/api/v1/moderation/jobs/{job.id}/retry",headers=headers,json=data).status_code==403
    staff=actor(client,"retry_staff","admin")
    assert client.post(f"/api/v1/moderation/jobs/{job.id}/retry",headers=staff,json={**data,"reason":" "}).status_code==422
    assert client.post(f"/api/v1/moderation/jobs/{job.id}/retry",headers=staff,json=data).status_code==200
    refreshed=get_job(client,row["id"])
    assert refreshed.attempts==0 and refreshed.total_attempts==1 and refreshed.retry_count==1 and refreshed.request_id!=original_request
    assert make_worker(setup).run_once()
    assert get_job(client,row["id"]).status=="SUCCEEDED"


def test_metrics_are_staff_only_and_never_return_snapshot_or_token(setup):
    client,headers,row,_,_=setup
    worker=make_worker(setup); worker.claim()
    assert client.get("/api/v1/moderation/jobs",headers=headers).status_code==403
    staff=actor(client,"stats_staff","admin")
    result=client.get("/api/v1/moderation/jobs",headers=staff)
    assert result.status_code==200 and result.json()["counts"]["PROCESSING"]==1
    assert "request_json" not in result.text and "Bearer" not in result.text and row["body"] not in result.text


def test_manual_approval_without_ai_has_audit_and_concurrency_guard(setup):
    client,headers,row,_,_=setup
    staff=actor(client,"offline_staff","admin")
    body={"entity_type":"post","entity_id":row["id"],"action":"approve","reason":"Reviewed manually without GPU",**versions(row)}
    assert client.post("/api/v1/moderation/decisions",headers=headers,json=body).status_code==403
    assert client.post("/api/v1/moderation/decisions",headers=staff,json=body).status_code==200
    assert client.post("/api/v1/moderation/decisions",headers=staff,json=body).status_code==409
    assert client.get("/api/v1/feed",headers=headers).json()["total"]==1
    with client.app.state.sessions() as db:
        assert db.scalar(select(ContentAudit).where(ContentAudit.event=="MANUAL_APPROVE")).reason==body["reason"]


def test_result_storage_failure_rolls_back_visibility_then_recovers(setup):
    client,headers,row,clock,settings=setup
    worker=make_worker(setup); claim=worker.claim()
    def fail(*_):
        raise RuntimeError("injected result storage failure")
    event.listen(ModerationResult,"before_insert",fail)
    try:
        with pytest.raises(RuntimeError,match="storage failure"):
            worker.finish(claim,response(claim.payload))
    finally:
        event.remove(ModerationResult,"before_insert",fail)
    assert client.get(f"/api/v1/posts/{row['id']}",headers=headers).json()["visibility_status"]=="PENDING_MODERATION"
    clock.value += settings.lease_seconds+1
    assert worker.run_once()


def test_context_parent_closure_and_no_current_duplicate(setup):
    client,headers,row,_,_=setup
    root=comment(client,headers,row["id"],body="root").json()
    reply=comment(client,headers,row["id"],parent_id=root["id"],body="reply").json()
    worker=make_worker(setup)
    for _ in range(3):
        assert worker.run_once()
    assert get_job(client,reply["id"]).status=="SUCCEEDED"
    assert client.get(f"/api/v1/comments/{reply['id']}",headers=headers).json()["visibility_status"]=="PUBLISHED"


@pytest.mark.parametrize("status,retryable",[(401,False),(403,False),(422,False),(429,True),(500,True),(503,True),(302,False)])
def test_http_error_classification_and_no_response_text_leak(setup,status,retryable):
    _,_,_,_,settings=setup
    payload=make_worker(setup).claim().payload
    transport=httpx.MockTransport(lambda request:httpx.Response(status,headers={"Retry-After":"9"},text="secret body must never be logged"))
    ai=AIClient(settings,transport)
    try:
        with pytest.raises(AIError) as caught:
            ai.moderate(payload)
        assert caught.value.retryable is retryable and "secret body" not in str(caught.value)
        assert caught.value.retry_after==9
    finally:
        ai.close()


@pytest.mark.parametrize("kind",["timeout","network","schema","correlation","oversize","score-string","nan"])
def test_client_rejects_incomplete_or_wrong_response(setup,kind):
    _,_,_,_,settings=setup
    payload=make_worker(setup).claim().payload
    def handler(request):
        assert request.headers["Authorization"]=="Bearer "+settings.service_token.get_secret_value()
        if kind=="timeout": raise httpx.ReadTimeout("private data",request=request)
        if kind=="network": raise httpx.ConnectError("private data",request=request)
        if kind=="schema": return httpx.Response(200,json={"score":"invalid"})
        if kind=="oversize": return httpx.Response(200,content=b"x"*1048577)
        if kind=="score-string": return httpx.Response(200,json={**response(payload).model_dump(mode="json"),"toxicity_score":"0.02"})
        if kind=="nan": return httpx.Response(200,content=json.dumps({**response(payload).model_dump(mode="json"),"toxicity_score":float("nan")}).encode())
        return httpx.Response(200,json=response(payload,request_id="wrong-id").model_dump(mode="json"))
    ai=AIClient(settings,httpx.MockTransport(handler))
    try:
        with pytest.raises(AIError) as caught: ai.moderate(payload)
        assert caught.value.retryable and "private data" not in str(caught.value)
    finally: ai.close()


def test_vendored_contract_and_generated_schema_match():
    root=Path(__file__).resolve().parents[3]
    assert (root/"services/moderation-ai/app/moderation_contract.py").read_bytes()==(root/"services/social-api/src/shieldvi_social/moderation_contract.py").read_bytes()
    design=root.parent/"ShieldVI_SocialAI_Design_Docs_v1"
    for name,model in [("request",ModerationRequest),("response",ModerationResponse)]:
        assert json.loads((design/f"contracts/moderation_{name}.schema.json").read_text(encoding="utf-8"))==model.model_json_schema()


def test_cross_service_real_adapter_with_stub_predictor(setup,monkeypatch,tmp_path):
    client,headers,row,_,settings=setup
    root=Path(__file__).resolve().parents[3]
    sys.path.insert(0,str(root))
    from fastapi.testclient import TestClient
    main=importlib.import_module("app.main")
    adapter=importlib.import_module("app.moderation_adapter")
    monkeypatch.setenv("AI_SERVICE_TOKEN",settings.service_token.get_secret_value())
    monkeypatch.setattr(main,"default_model_path",lambda:str(tmp_path/"missing-real-model"))
    monkeypatch.setattr(adapter,"guard",adapter.ServiceGuard())
    class Stub:
        threshold,name=.41,"SYNTHETIC CROSS-SERVICE STUB"
        def predict_scores(self,texts): return [.02]*len(texts)
    main.app.dependency_overrides[main.get_predictor]=lambda:Stub()
    try:
        with TestClient(main.app) as ai_server:
            def transport(request):
                result=ai_server.post(request.url.path,headers=dict(request.headers),content=request.content)
                return httpx.Response(result.status_code,headers=dict(result.headers),content=result.content)
            ai=AIClient(settings,httpx.MockTransport(transport))
            try:
                assert Worker(client.app.state.engine,settings,ai,setup[3]).run_once()
            finally: ai.close()
    finally:
        main.app.dependency_overrides.pop(main.get_predictor,None)
    assert client.get(f"/api/v1/posts/{row['id']}",headers=headers).json()["visibility_status"]=="PUBLISHED"


def test_downgrade_refuses_to_erase_system_audit(setup):
    client,_,_,_,_=setup
    make_worker(setup).run_once()
    with pytest.raises(RuntimeError,match="System audit exists"):
        migrate(client.app.state.engine,"downgrade","0002_content")
    with client.app.state.sessions() as db:
        assert db.scalar(select(func.count()).select_from(ModerationResult))==1
        assert db.scalar(select(func.count()).select_from(ContentAudit).where(ContentAudit.actor_type=="system"))==1


def test_worker_rejects_forged_repeated_evidence(setup):
    _,_,_,_,settings=setup
    payload=make_worker(setup).claim().payload
    fabricated=response(payload,suspected_repeated_harassment=True,evidence=[{
        "actor_user_id":payload.user_id,"target_user_id":"someone","evidence_comment_ids":[payload.content_id,"invented"],
        "n_distinct_timestamps":2,"target_confidence":"high"}])
    ai=AIClient(settings,httpx.MockTransport(lambda _:httpx.Response(200,json=fabricated.model_dump(mode="json"))))
    try:
        with pytest.raises(AIError,match="AI_INVALID_EVIDENCE"):
            ai.moderate(payload)
    finally: ai.close()


def test_claim_policy_and_request_guards(setup):
    client,_,row,_,_=setup
    worker=make_worker(setup); claim=worker.claim()
    with client.app.state.sessions.begin() as db:
        db.get(ModerationJob,claim.job_id).request_id="changed-request-id"
    assert not worker.finish(claim,response(claim.payload))
    with client.app.state.sessions() as db:
        assert db.get(Post,row["id"]).visibility_status=="PENDING_MODERATION"


def test_policy_mismatch_stays_pending_and_visible_to_operator(setup):
    client,_,row,_,_=setup
    worker=make_worker(setup); claim=worker.claim()
    with client.app.state.sessions.begin() as db:
        db.get(ModerationJob,claim.job_id).policy_version="unapproved-other-policy"
    assert not worker.finish(claim,response(claim.payload))
    job=get_job(client,row["id"])
    assert job.status=="FAILED_PERMANENTLY" and job.last_error=="POLICY_STALE"


@pytest.mark.parametrize("changes",[{"service_token":SecretStr("too-short")},{"base_url":"http://user:pass@localhost"},{"lease_seconds":10},{"read_timeout":0},{"max_attempts":0}])
def test_worker_configuration_fails_closed(setup,changes):
    with pytest.raises(ValueError):
        replace(setup[4],**changes)
