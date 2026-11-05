def make_payload(profile="conservative"):
    return {
        "thread_id": "DEMO01",
        "profile": profile,
        "comments": [
            {"comment_id": "c1", "user_id": "u1", "text": "Xin chào", "timestamp": "2026-01-01T10:00:00Z"},
            {"comment_id": "c2", "user_id": "u2", "text": "[TEST_TOXIC] câu 1", "parent_id": "c1", "timestamp": "2026-01-01T10:01:00Z"},
            {"comment_id": "c3", "user_id": "u1", "text": "Mời góp ý lịch sự", "parent_id": "c2", "timestamp": "2026-01-01T10:02:00Z"},
            {"comment_id": "c4", "user_id": "u2", "text": "[TEST_TOXIC] câu 2", "parent_id": "c3", "timestamp": "2026-01-01T10:03:00Z"},
        ]
    }


def test_analyze_detects_repeated_with_parent_and_two_times(client):
    resp = client.post("/api/analyze", json=make_payload())
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["suspected_repeated_harassment"] is True
    assert data["evidence"][0]["evidence_comment_ids"] == ["c2", "c4"]
    assert data["risk_level"] == "suspected_repeated"
    assert data["research_only"] is False


def test_single_insult_not_repeated(client):
    payload = make_payload()
    payload["comments"] = payload["comments"][:-1]
    resp = client.post("/api/analyze", json=payload)
    assert resp.status_code == 200
    assert resp.json()["suspected_repeated_harassment"] is False
    assert resp.json()["risk_level"] == "needs_review"


def test_parent_self_reference_rejected(client):
    payload = make_payload()
    payload["comments"][0]["parent_id"] = "c1"
    assert client.post("/api/analyze", json=payload).status_code == 422


def test_parent_missing_rejected(client):
    payload = make_payload()
    payload["comments"][1]["parent_id"] = "invalid"
    assert client.post("/api/analyze", json=payload).status_code == 422


def test_duplicate_comment_id_rejected(client):
    payload = make_payload()
    payload["comments"][1]["comment_id"] = "c1"
    assert client.post("/api/analyze", json=payload).status_code == 422


def test_no_raw_text_in_response(client):
    resp = client.post("/api/analyze", json=make_payload())
    assert resp.status_code == 200
    assert "[TEST_TOXIC]" not in resp.text


def test_research_profile_explicit(client):
    result = client.post("/api/analyze", json=make_payload("research_synthetic")).json()
    assert result["research_only"] is True
    assert result["repeated_rule_threshold"] == 0.03
    assert result["model_threshold"] == 0.41


def test_no_model_returns_503_without_override(monkeypatch, tmp_path):
    """Độc lập với MODEL_PATH/Drive thật: kiểm tra API khi checkpoint vắng mặt."""
    from fastapi.testclient import TestClient
    from app.main import app, get_predictor

    nonexistent_model_dir = tmp_path / "missing_visobert_checkpoint"
    assert not nonexistent_model_dir.exists()
    monkeypatch.setattr(
        "app.main.default_model_path", lambda: str(nonexistent_model_dir)
    )
    app.dependency_overrides.pop(get_predictor, None)
    with TestClient(app) as c:
        resp = c.post("/api/analyze", json=make_payload())
        assert resp.status_code == 503, resp.text
        health = c.get("/health")
        assert health.status_code == 200
        assert health.json()["model_loaded"] is False
