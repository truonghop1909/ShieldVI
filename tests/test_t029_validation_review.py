import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from review_t029_validation import review, validation_gates
from refine_model import file_hash

GATE = {"macroF1_min_delta": .005, "precision_loss_allowed": 0, "recall_loss_allowed": 0}
BASE = {"n": 2000, "threshold": .41, "macro_f1": .76, "toxic_precision": .64, "toxic_recall": .53}


@pytest.mark.parametrize("field", ["macro_f1", "toxic_precision", "toxic_recall"])
def test_any_failed_metric_rejects_even_when_other_metrics_improve(field):
    candidate = {**BASE, "macro_f1": .79, "toxic_precision": .69, "toxic_recall": .60}
    candidate[field] = BASE[field] - .001
    assert not all(validation_gates(candidate, {"V1": BASE}, GATE)["V1"].values())


def test_checks_both_original_and_existing_default():
    c = {**BASE, "macro_f1": .78, "toxic_precision": .66, "toxic_recall": .54}
    gates = validation_gates(c, {"V1": BASE, "default": {**BASE, "toxic_precision": .70}}, GATE)
    assert all(gates["V1"].values()) and not gates["default"]["toxic_precision"]


@pytest.mark.parametrize("field,value", [("macro_f1", float("nan")), ("toxic_precision", float("inf")), ("toxic_recall", -1), ("threshold", .4), ("n", 1000)])
def test_rejects_invalid_or_incomparable_validation(field, value):
    with pytest.raises(ValueError):
        validation_gates({**BASE, field: value}, {"V1": BASE}, GATE)


def artifacts(tmp_path):
    # Tiny stub checkpoint tests the review boundary, not inference quality.
    (tmp_path / "model.safetensors").write_bytes(b"test checkpoint")
    candidate = {**BASE, "macro_f1": .78, "toxic_precision": .66, "toxic_recall": .54}
    report = {"status": "COMPLETE_HEAD_TRAINED_NOT_ACTIVATED", "training_performed": True,
              "optimizer_steps": 4, "encoder_unchanged": True, "baseline_unchanged": True,
              "source_hashes_unchanged": True, "activated": False, "test_scored_during_training": False,
              "threshold": .41, "candidate_sha256": file_hash(tmp_path / "model.safetensors"),
              "candidate_validation": candidate, "selected": {"validation": candidate}, "baseline_validation": BASE}
    values = {"training_report.json": report, "references.json": {"original_V1": BASE}, "protocol.json": {"original_validation_gate": GATE}}
    for name, value in values.items():
        (tmp_path / name).write_text(json.dumps(value), encoding="utf-8")
    return [tmp_path / name for name in values] + [tmp_path / "review.json"]


def test_passing_screen_cannot_authorize_promotion_or_read_test(tmp_path):
    paths = artifacts(tmp_path)
    result = review(*paths)
    assert result["decision"] == "PASS_VALIDATION_SCREEN_ONLY"
    assert not result["promotion_allowed"] and not result["test_scored"] and not result["regression_scored"]
    with pytest.raises(FileExistsError):
        review(*paths)


def test_refuses_checkpoint_tampering(tmp_path):
    paths = artifacts(tmp_path)
    (tmp_path / "model.safetensors").write_bytes(b"changed checkpoint")
    with pytest.raises(ValueError, match="checkpoint hash"):
        review(*paths)


def test_refuses_changed_baseline_validation(tmp_path):
    paths = artifacts(tmp_path)
    references = {"original_V1": {**BASE, "n": 1999}}
    paths[1].write_text(json.dumps(references), encoding="utf-8")
    with pytest.raises(ValueError, match="Baseline validation"):
        review(*paths)


def test_actual_followup_preserves_original_gates_and_predeclared_recipe():
    p = ROOT / "reports/ai_update/candidate_revision_20261103"
    declaration = json.loads((p / "predeclared_experiment.json").read_text(encoding="utf-8"))
    for key, path in {
        "config_sha256": ROOT / "configs/t029_genz500_cpu_head_r04.json",
        "prepared_manifest_sha256": p / "prepared/manifest.json",
        "original_protocol_sha256": ROOT / "reports/ai_update/all_tasks_cpu_20261103/evaluation_protocol.json",
        "validation_references_sha256": p / "validation_references.json",
        "training_implementation_sha256": ROOT / "scripts/t029_cpu_head.py",
        "review_implementation_sha256": ROOT / "scripts/review_t029_validation.py",
    }.items():
        assert declaration[key] == file_hash(path)
    assert declaration["max_candidate_runs"] == 1 and not declaration["test_scoring_allowed"]
    assert declaration["historical_test_previously_inspected"] and not declaration["fresh_blind_benchmark_claim_allowed"]


def test_actual_followup_training_and_review_cannot_hide_failed_gate():
    p = ROOT / "reports/ai_update/candidate_revision_20261103"
    r = json.loads((p / "validation_review.json").read_text(encoding="utf-8"))
    cfg = json.loads((ROOT / "configs/t029_genz500_cpu_head_r04.json").read_text(encoding="utf-8"))
    model = Path(cfg["output_dir"])
    training = json.loads((model / "training_report.json").read_text(encoding="utf-8"))
    assert training["optimizer_steps"] > 0 and training["elapsed_seconds"] <= 900
    assert training["encoder_unchanged"] and training["baseline_unchanged"] and training["source_hashes_unchanged"]
    assert training["candidate_sha256"] == file_hash(model / "model.safetensors")
    assert r["candidate_validation"] == training["candidate_validation"]
    assert set(r["gates"]) == {"original_V1", "existing_default_V1_1"}
    passed = all(all(gates.values()) for gates in r["gates"].values())
    assert r["decision"] == ("PASS_VALIDATION_SCREEN_ONLY" if passed else "REJECT_PROMOTION_KEEP_EXISTING_DEFAULT")
    assert not r["promotion_allowed"] and not r["test_scored"] and not r["regression_scored"]
    assert not training["test_scored_during_training"] and not training["activated"]
