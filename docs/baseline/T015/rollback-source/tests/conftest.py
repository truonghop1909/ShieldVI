import pytest
from fastapi.testclient import TestClient
from app.main import app, get_predictor


class FakePredictor:
    name = "TEST STUB — NO AI"
    threshold = 0.41

    def predict_scores(self, texts):
        return [0.9 if "[TEST_TOXIC]" in text else 0.02 for text in texts]


@pytest.fixture
def client(monkeypatch, tmp_path):
    # API unit tests use the explicit stub and must not load a local real checkpoint.
    monkeypatch.setattr('app.main.default_model_path', lambda: str(tmp_path / 'missing_checkpoint'))
    app.dependency_overrides[get_predictor] = lambda: FakePredictor()
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
