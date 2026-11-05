"""T016 design evidence: real legacy signals + declarative acceptance invariants.

No production policy engine or service exists here. Scores are synthetic;
integration cases in the JSON are specifications, not passing integration tests.
"""
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

DESIGN = Path(__file__).resolve().parents[1]
LEGACY = DESIGN if (DESIGN / "services/moderation-ai").is_dir() else DESIGN.parent / "ShieldVI_V3_Hybrid_Review"
sys.path.insert(0, str(LEGACY))

from app.engine import analyze_thread
from app.lexical import detect
from app.schemas import AnalyzeRequest

VECTORS = json.loads((DESIGN / "contracts/policy_acceptance_cases.json").read_text(encoding="utf-8"))


class StubPredictor:
    name = "T016 SYNTHETIC TEST SCORES"
    threshold = 0.41

    def __init__(self, scores):
        self.scores = scores

    def predict_scores(self, texts):
        return [self.scores[text] for text in texts]


@pytest.mark.parametrize("case", VECTORS["cases"], ids=lambda c: c["id"])
def test_real_legacy_signals_for_policy_acceptance_cases(case):
    signals = detect(case["text"])
    assert signals["lexical_review_recommended"] is case["lexical_review"]
    for key, field in (("directed", "directed_insult_candidate"), ("reported", "reported_or_apology_context")):
        if key in case:
            assert signals[field] is case[key]
    request = AnalyzeRequest.model_validate({
        "thread_id": case["id"],
        "comments": [{"comment_id": "c1", "user_id": "fixture-author",
                      "text": case["text"], "timestamp": "2026-10-30T00:00:00Z"}],
    })
    result = analyze_thread(request, StubPredictor({case["text"]: case["score"]}))
    assert result.model_threshold == result.repeated_rule_threshold == 0.41
    assert result.comments[0].toxicity_score == case["score"]
    assert not result.suspected_repeated_harassment
    assert result.evidence == []
    assert not hasattr(result, "visibility_status")  # Social decision is not AI output.


@pytest.mark.parametrize("parent_links,same_time,score,expected", [
    (True, False, 0.9, True),
    (False, False, 0.9, False),  # Root fallback low confidence is insufficient.
    (True, True, 0.9, False),
    (True, False, 0.02, False),  # Lexical hits never fabricate repeated evidence.
])
def test_repeated_requires_context_not_keywords(parent_links, same_time, score, expected):
    start = datetime(2026, 10, 30, tzinfo=timezone.utc)
    rows = [{"comment_id": "root", "user_id": "target", "text": "Xin chào", "timestamp": start}]
    for i in (1, 2):
        rows.append({"comment_id": f"c{i}", "user_id": "actor", "text": "f.u.c.k you",
                     "parent_id": "root" if parent_links else None,
                     "timestamp": start + timedelta(minutes=1 if same_time else i)})
    result = analyze_thread(AnalyzeRequest(thread_id="context-fixture", comments=rows),
                            StubPredictor({"Xin chào": 0.02, "f.u.c.k you": score}))
    assert result.suspected_repeated_harassment is expected
    assert result.risk_level == ("suspected_repeated" if expected else "needs_review")
    if expected:
        assert result.evidence[0].evidence_comment_ids == ["c1", "c2"]
        assert result.evidence[0].n_distinct_timestamps == 2


def test_shadow_acceptance_table_cannot_hold_hide_or_ban():
    assert VECTORS["artifact_type"] == "design_test_vectors_not_runtime_config"
    table = {row["risk"]: row for row in VECTORS["shadow_table"]}
    assert set(table) == {"LOW", "REVIEW", "HIGH", "UNKNOWN"}
    assert table["HIGH"]["visibility"] == "PUBLISHED_FLAGGED"
    assert table["HIGH"]["proposed_visibility"] == "HELD_FOR_REVIEW"
    assert table["UNKNOWN"]["visibility"] == "PENDING_MODERATION"
    for case in VECTORS["cases"]:
        assert case["visibility"] == table[case["risk"]]["visibility"]
        assert case["queue"] is table[case["risk"]]["queue"]
        assert case["risk"] != "HIGH"
    assert all(row["visibility"] not in {"HIDDEN", "HELD_FOR_REVIEW"} for row in table.values())


def test_false_positive_pair_does_not_become_high():
    cases = {c["id"]: c for c in VECTORS["cases"]}
    ordinary, false_positive = cases["ordinary"], cases["model_false_positive"]
    assert ordinary["text"] == false_positive["text"]
    assert ordinary["risk"] == "LOW"
    assert false_positive["risk"] == "REVIEW"
    assert false_positive["visibility"] == "PUBLISHED_FLAGGED"
    assert cases["at_threshold"]["visibility"] == "PUBLISHED_FLAGGED"


def test_existing_example_is_draft_with_enforcement_disabled():
    example = json.loads((DESIGN / "contracts/moderation_policy.example.json").read_text(encoding="utf-8"))
    assert example["policy_version"].startswith("draft-")
    assert example["mode"] == "shadow"
    assert example["model_threshold"] == 0.41
    high = next(row for row in example["decision_rules"] if row["risk_tier"] == "HIGH")
    assert high["enforcement_enabled"] is False
