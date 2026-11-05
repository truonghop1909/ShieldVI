import csv
import json

import pytest

from scripts.refine_model import clean_train, metrics, precision_tradeoff_gate, read_rows, test_gate as audit_gate, validation_gate


def test_training_excludes_held_out_duplicates_and_conflicting_labels():
    rows = [
        {'text': '  HELD  out ', 'label': 1},
        {'text': 'unique train', 'label': 0},
        {'text': 'UNIQUE train', 'label': 0},
        {'text': 'conflict', 'label': 0},
        {'text': 'Conflict', 'label': 1},
    ]
    cleaned, counts = clean_train(rows, ['held out'])
    assert cleaned == [rows[1]]
    assert counts == {'overlap_removed': 1, 'conflicting_removed': 2, 'duplicates_removed': 1}


def test_text_only_holdout_loading_does_not_parse_test_labels(tmp_path):
    path = tmp_path / 'holdout.csv'
    with path.open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['Comment', 'Toxicity'])
        writer.writeheader()
        writer.writerow({'Comment': 'Held-out text', 'Toxicity': 'DO NOT OPEN FOR SELECTION'})
    assert read_rows(path, with_labels=False)[0]['label'] is None
    with pytest.raises(ValueError):
        read_rows(path)


def test_fixed_deployment_threshold_and_confusion_metrics():
    result = metrics([0, 1, 1, 0], [0.4, 0.41, 0.3, 0.9])
    assert result['threshold'] == 0.41
    assert (result['tp'], result['fp'], result['tn'], result['fn']) == (1, 1, 1, 1)
    assert result['macro_f1'] == result['toxic_precision'] == result['toxic_recall'] == 0.5


def test_validation_gate_does_not_reward_reducing_recall_to_remove_false_positives():
    baseline = {'macro_f1': 0.76, 'toxic_precision': 0.62, 'toxic_recall': 0.54}
    assert not validation_gate(baseline, {'macro_f1': 0.79, 'toxic_precision': 0.8, 'toxic_recall': 0.4})
    assert not validation_gate(baseline, {'macro_f1': 0.78, 'toxic_precision': 0.6, 'toxic_recall': 0.7})
    assert validation_gate(baseline, {'macro_f1': 0.78, 'toxic_precision': 0.65, 'toxic_recall': 0.56})


def test_final_audit_rejects_regression():
    baseline = {'macro_f1': 0.74, 'toxic_precision': 0.55, 'toxic_recall': 0.53}
    assert audit_gate(baseline, baseline)
    assert not audit_gate(baseline, {'macro_f1': 0.73, 'toxic_precision': 0.56, 'toxic_recall': 0.53})
    assert not audit_gate(baseline, {'macro_f1': 0.76, 'toxic_precision': 0.58, 'toxic_recall': 0.49})


def test_precision_tradeoff_is_bounded_and_explicit():
    baseline = {'n': 2000, 'fp': 73, 'macro_f1': 0.7637, 'toxic_precision': 0.6294, 'toxic_recall': 0.5345}
    candidate = {'n': 2000, 'fp': 64, 'macro_f1': 0.7602, 'toxic_precision': 0.6484, 'toxic_recall': 0.5086}
    assert precision_tradeoff_gate(baseline, candidate)
    assert not validation_gate(baseline, candidate)
    assert not precision_tradeoff_gate(baseline, {**candidate, 'macro_f1': 0.75})
    assert not precision_tradeoff_gate(baseline, {**candidate, 'toxic_recall': 0.49})
    assert not precision_tradeoff_gate(baseline, {**candidate, 'fp': 72})


def test_runtime_only_auto_selects_approved_checkpoint(monkeypatch, tmp_path):
    from app import predictor
    monkeypatch.delenv('MODEL_PATH', raising=False)
    monkeypatch.setattr(predictor, 'REFINED_MODEL_PATH', tmp_path)
    config = tmp_path / 'threshold_config.json'
    weights = tmp_path / 'model.safetensors'
    config.write_text(json.dumps({'approval_status': 'rejected_by_test_audit'}), encoding='utf-8')
    weights.write_bytes(b'file presence fixture only')
    assert predictor.default_model_path() != str(tmp_path)
    config.write_text(json.dumps({'approval_status': 'approved'}), encoding='utf-8')
    assert predictor.default_model_path() == str(tmp_path)
    monkeypatch.setenv('MODEL_PATH', 'explicit-user-model')
    assert predictor.default_model_path() == 'explicit-user-model'
