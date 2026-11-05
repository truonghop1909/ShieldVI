from fastapi import HTTPException
from app.main import app,get_predictor
from test_moderation_adapter import internal,payload,send


def test_internal_validation_redacts_unknown_field_names(internal):
    marker='synthetic-private-name@example.invalid'
    body=payload();body[marker]='synthetic-private-value'
    response=send(internal,body)
    assert response.status_code==422
    assert marker not in response.text and 'synthetic-private-value' not in response.text


def test_internal_predictor_dependency_error_redacted_but_legacy_unchanged(internal):
    client,headers=internal
    marker='synthetic-private-model-path-and-token-marker'
    def unavailable():raise HTTPException(503,marker)
    previous=app.dependency_overrides.get(get_predictor)
    app.dependency_overrides[get_predictor]=unavailable
    try:
        response=send(internal,payload())
        assert response.status_code==503 and marker not in response.text
        # Preserve the legacy API contract; it is private-network-only until T015.
        legacy=client.post('/api/analyze',json={'thread_id':'fixture','comments':[]})
        assert legacy.status_code==503 and marker in legacy.text
    finally:
        if previous is None:app.dependency_overrides.pop(get_predictor,None)
        else:app.dependency_overrides[get_predictor]=previous
