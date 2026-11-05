from datetime import datetime, timezone
from app.engine import analyze_thread
from app.schemas import AnalyzeRequest


class Predictor:
    name = "FAKE_TEST_ONLY"
    threshold = 0.41
    def predict_scores(self, texts):
        return [0.5] * len(texts)


def make_data():
    return {"thread_id": "t1", "comments": [
        {"comment_id": "1", "user_id": "A", "text": "1", "timestamp": "2026-01-01T00:00:00Z"},
        {"comment_id": "2", "user_id": "B", "text": "2", "parent_id": "1", "timestamp": "2026-01-01T00:01:00Z"},
        {"comment_id": "3", "user_id": "A", "text": "3", "parent_id": "2", "timestamp": "2026-01-01T00:02:00Z"},
        {"comment_id": "4", "user_id": "B", "text": "4", "parent_id": "3", "timestamp": "2026-01-01T00:03:00Z"},
    ]}


def test_nontoxic_target_not_same_user():
    data = AnalyzeRequest(**make_data())
    out = analyze_thread(data, Predictor())
    assert all(c.target_user_id != c.user_id for c in out.comments)


def test_repeated_does_not_use_gold_label():
    data = make_data()
    for c in data["comments"]:
        c["toxicity"] = 0  # gold labels are not part of the API schema
        c["target_user_id"] = "LEAK_TEST"
    out = analyze_thread(AnalyzeRequest(**data), Predictor())
    assert not any(c.target_user_id == "LEAK_TEST" for c in out.comments)


def test_no_repeated_if_identical_timestamp():
    data = make_data()
    data["comments"][3]["timestamp"] = data["comments"][1]["timestamp"]
    # parent c3 then predates c4 => invalid, instead make legitimate unrelated reply links
    data["comments"][3]["parent_id"] = "1"
    out = analyze_thread(AnalyzeRequest(**data), Predictor())
    assert out.suspected_repeated_harassment is False


def test_unconfident_root_fallback_excluded_in_conservative():
    data = {"thread_id": "x", "comments": [
        {"comment_id": "1", "user_id": "A", "text": "1", "timestamp": "2026-01-01T00:00:00Z"},
        {"comment_id": "2", "user_id": "B", "text": "2", "timestamp": "2026-01-01T00:01:00Z"},
        {"comment_id": "3", "user_id": "B", "text": "3", "timestamp": "2026-01-01T00:02:00Z"},
    ]}
    out = analyze_thread(AnalyzeRequest(**data), Predictor())
    assert out.suspected_repeated_harassment is False
