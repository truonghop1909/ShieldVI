"""Live-HTTP test fixture only; never a production inference fallback."""
import os

if os.environ.get("SHIELDVI_SYNTHETIC_AI_FIXTURE") != "1":
    raise RuntimeError("Synthetic AI fixture must be explicitly enabled for testing")

from app.main import app, get_predictor


class SyntheticPredictor:
    name, threshold = "LIVE HTTP STUB — NOT REAL MODEL INFERENCE", .41

    def predict_scores(self, texts):
        return [.9 if "[TEST_TOXIC]" in text else .02 for text in texts]


app.dependency_overrides[get_predictor] = lambda: SyntheticPredictor()
