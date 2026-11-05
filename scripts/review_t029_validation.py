"""Validation-only screening of a bounded follow-up; never loads test examples.

Passing this screen is insufficient for promotion. Existing regression and final
audit gates remain mandatory, and previously inspected data is not blind data.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from refine_model import file_hash
from synthetic_data.pipeline import atomic_json


def validation_gates(candidate, references, gate):
    """Use the original numeric gates verbatim, against every baseline."""
    result = {}
    for name, baseline in references.items():
        for field in ("macro_f1", "toxic_precision", "toxic_recall"):
            for metrics in (candidate, baseline):
                value = metrics[field]
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
                    raise ValueError("Invalid validation metric: " + field)
        if candidate["n"] != baseline["n"] or candidate["threshold"] != .41 or baseline["threshold"] != .41:
            raise ValueError("Validation population/threshold mismatch")
        result[name] = {
            "macro_f1": candidate["macro_f1"] >= baseline["macro_f1"] + gate["macroF1_min_delta"],
            "toxic_precision": candidate["toxic_precision"] >= baseline["toxic_precision"] - gate["precision_loss_allowed"],
            "toxic_recall": candidate["toxic_recall"] >= baseline["toxic_recall"] - gate["recall_loss_allowed"],
        }
    if not result:
        raise ValueError("Missing baseline validation metrics")
    return result


def review(training_report, references_path, protocol_path, output):
    training_report, references_path, protocol_path, output = map(Path, (training_report, references_path, protocol_path, output))
    if output.exists():
        raise FileExistsError("Never overwrite a previous review")
    report = json.loads(training_report.read_text(encoding="utf-8"))
    references = json.loads(references_path.read_text(encoding="utf-8"))
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    if report["status"] != "COMPLETE_HEAD_TRAINED_NOT_ACTIVATED" or not report["training_performed"] or report["optimizer_steps"] < 1:
        raise ValueError("A real completed training run is required")
    if not all(report.get(k) is True for k in ("encoder_unchanged", "baseline_unchanged", "source_hashes_unchanged")):
        raise ValueError("Protected artifact integrity failed")
    if report["activated"] or report["test_scored_during_training"] or report["threshold"] != .41:
        raise ValueError("Experiment boundary violated")
    if report["candidate_sha256"] != file_hash(training_report.parent / "model.safetensors"):
        raise ValueError("Candidate checkpoint hash mismatch")
    if report["candidate_validation"] != report["selected"]["validation"]:
        raise ValueError("Selected validation metrics mismatch")
    baseline, expected = report["baseline_validation"], references["original_V1"]
    same = all(key in baseline and (
        math.isclose(baseline[key], value, rel_tol=0, abs_tol=1e-6)
        if isinstance(value, float) and key != "threshold" else baseline[key] == value
    ) for key, value in expected.items())
    if not same:
        raise ValueError("Baseline validation population or scores changed")
    gates = validation_gates(report["candidate_validation"], references, protocol["original_validation_gate"])
    passed = all(all(values.values()) for values in gates.values())
    result = {
        "status": "VALIDATION_SCREEN_COMPLETE",
        "decision": "PASS_VALIDATION_SCREEN_ONLY" if passed else "REJECT_PROMOTION_KEEP_EXISTING_DEFAULT",
        "candidate_validation": report["candidate_validation"], "reference_validation": references,
        "gates": gates, "threshold": .41,
        "training_report_sha256": file_hash(training_report), "candidate_sha256": report["candidate_sha256"],
        "reference_sha256": file_hash(references_path), "original_protocol_sha256": file_hash(protocol_path),
        "test_scored": False, "regression_scored": False, "promotion_allowed": False,
        "production_changed": False, "historical_data_not_fresh_blind": True,
        "next_action": "Fresh independent evidence and unchanged regression/release gates required before any promotion" if passed else "Stop this recipe; retain default and negative result. Do not relax gates or rescore test.",
    }
    atomic_json(output, result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--training-report", type=Path, required=True)
    p.add_argument("--references", type=Path, required=True)
    p.add_argument("--protocol", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    a = p.parse_args()
    r = review(a.training_report, a.references, a.protocol, a.output)
    print(json.dumps({k: r[k] for k in ("status", "decision", "gates", "test_scored", "promotion_allowed")}))


if __name__ == "__main__":
    main()
