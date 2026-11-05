import json
import secrets
from pathlib import Path

import pytest

from app import moderation_adapter as adapter
from app.main import get_predictor, app
from app.moderation_contract import ModerationRequest, ModerationResponse


@pytest.fixture
def internal(client, monkeypatch):
    token = secrets.token_urlsafe(32)
    monkeypatch.setenv("AI_SERVICE_TOKEN", token)
    monkeypatch.setattr(adapter, "guard", adapter.ServiceGuard())
    return client, {"Authorization": "Bearer " + token}


def payload(text="Xin chào"):
    return {"schema_version":"1.0", "request_id":"req-fixture", "content_id":"c1", "content_type":"comment",
        "content_revision":1, "user_id":"actor", "text":text, "timestamp":"2026-10-30T01:00:00Z",
        "context":{"post_id":"post-fixture", "source":"social-api", "complete":False, "recent_comments":[]}}


def send(internal, data):
    client, headers = internal
    return client.post("/api/v1/moderate/comment", headers=headers, json=data)


def test_advisory_contract_metadata_and_raw_probability(internal):
    response = send(internal, payload())
    assert response.status_code == 200, response.text
    result = ModerationResponse.model_validate(response.json())
    assert result.toxicity_score == 0.02 and result.ai_label == "CLEAN"
    assert result.model_threshold == 0.41 and result.model_version == "TEST STUB — NO AI"
    assert len(result.lexicon_version) == 64 and result.decision_authority == "advisory"
    assert result.content_id == "c1" and result.content_revision == 1
    assert not result.suspected_repeated_harassment and result.evidence == []
    assert "visibility_status" not in response.json()


@pytest.mark.parametrize("text", ["Đm máy hết pin", 'Tôi trích dẫn "fuck you" để báo cáo.', "f.u.c.k you", "đ.m mày"])
def test_lexical_signal_never_changes_model_label_or_creates_repeated(internal, text):
    response = send(internal, payload(text))
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["ai_label"] == "CLEAN" and result["toxicity_score"] == 0.02
    assert result["suggested_action"] == "needs_review"
    assert result["suspected_repeated_harassment"] is False


def test_actual_parent_and_times_required_for_repeated(internal):
    data = payload("[TEST_TOXIC] second")
    data.update(content_id="c2", parent_id="root", timestamp="2026-10-30T01:02:00Z")
    data["context"]["recent_comments"] = [
        {"comment_id":"root","user_id":"target","text":"Root","timestamp":"2026-10-30T01:00:00Z"},
        {"comment_id":"c1","user_id":"actor","text":"[TEST_TOXIC] first","parent_id":"root","timestamp":"2026-10-30T01:01:00Z"},
    ]
    result = send(internal, data).json()
    assert result["suspected_repeated_harassment"]
    assert result["evidence"][0]["evidence_comment_ids"] == ["c1", "c2"]
    data["user_id"] = "different-actor"
    assert not send(internal, data).json()["suspected_repeated_harassment"]


@pytest.mark.parametrize("change", [
    {"schema_version":"2.0"}, {"content_revision":0}, {"content_revision":True},
    {"parent_id":"missing"}, {"timestamp":"2026-10-30T01:00:00"},
    {"email":"private@example.com"}, {"text":"s"*8001},
])
def test_bad_contract_rejected_without_echoing_input(internal, change):
    response = send(internal, {**payload(), **change})
    assert response.status_code == 422
    assert "private@example.com" not in response.text and "s"*100 not in response.text
    assert all("input" not in item for item in response.json()["detail"])


def test_auth_missing_disabled_and_rate_limit(internal, monkeypatch):
    client, headers = internal
    assert client.post("/api/v1/moderate/comment", json=payload()).status_code == 401
    monkeypatch.delenv("AI_SERVICE_TOKEN")
    assert client.post("/api/v1/moderate/comment", headers=headers, json=payload()).status_code == 503
    monkeypatch.setenv("AI_SERVICE_TOKEN", headers["Authorization"][7:])
    monkeypatch.setenv("AI_SERVICE_RATE_LIMIT", "1")
    assert send(internal, payload()).status_code == 200
    assert send(internal, payload()).status_code == 429


def test_missing_model_and_body_limit_are_explicit(internal):
    client, headers = internal
    app.dependency_overrides.pop(get_predictor, None)
    assert send(internal, payload()).status_code == 503
    assert client.post("/api/v1/moderate/comment", headers=headers, content="x"*1048577).status_code == 413


def test_threshold_mismatch_does_not_change_checkpoint(internal):
    class DifferentThreshold:
        threshold = 0.5
    app.dependency_overrides[get_predictor] = lambda: DifferentThreshold()
    assert send(internal, payload()).status_code == 503


def test_no_rounding_flips_threshold_label(internal):
    class NearBoundary:
        threshold, name = 0.41, "BOUNDARY STUB"
        def predict_scores(self, texts):
            return [0.4099999] * len(texts)
    app.dependency_overrides[get_predictor] = lambda: NearBoundary()
    data = send(internal, payload()).json()
    assert data["toxicity_score"] == 0.4099999 and data["ai_label"] == "CLEAN"


def test_busy_inference_returns_retryable_status(internal):
    assert adapter.guard.inference.acquire(blocking=False)
    try:
        assert send(internal,payload()).status_code==429
    finally:
        adapter.guard.inference.release()


def test_future_context_is_rejected(internal):
    data=payload()
    data["context"]["recent_comments"]=[{"comment_id":"future","user_id":"other","text":"future","timestamp":"2026-10-31T00:00:00Z"}]
    assert send(internal,data).status_code==422
