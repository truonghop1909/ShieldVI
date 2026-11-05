"""A missing research baseline must not prevent the approved realtime demo."""
import hashlib
import json
import pytest
from test_studio_datasets import studio
from test_live_api import live
from ml_studio import evaluation


@pytest.fixture
def local_registry(studio, tmp_path, monkeypatch):
    root = tmp_path / 'project'
    (root / 'configs').mkdir(parents=True)
    models = {}
    for key, role in [('v1', 'baseline'), ('v1_1', 'active_existing'), ('candidate_r06', 'experimental')]:
        folder = root / key
        folder.mkdir()
        artifacts = {'model.safetensors': key.encode(), 'config.json': b'{}',
                     'threshold_config.json': b'{"threshold":0.41}', 'tokenizer_config.json': b'{}'}
        for name, content in artifacts.items():
            (folder / name).write_bytes(content)
        models[key] = {'path': str(folder), 'role': role, 'threshold': .41,
                       'sha256': {name: hashlib.sha256(content).hexdigest() for name, content in artifacts.items()}}
    (root / 'configs/model_registry.repeated_recovery.local.json').write_text(json.dumps({'models': models}))
    lock = root / 'lock.json'
    lock.write_text(json.dumps({'models': {key: {'weights_sha256': entry['sha256']['model.safetensors']}
                                         for key, entry in models.items()}}))
    monkeypatch.setattr(evaluation, 'ROOT', root)
    monkeypatch.setattr(evaluation, 'LOCK', lock)
    monkeypatch.setattr(evaluation.TrainingJobs, 'list', lambda self: [])
    return evaluation.EvaluationJobs(studio[1]), models, studio


def test_strict_initialization_still_requires_original_baseline(local_registry):
    jobs, models, _ = local_registry
    from pathlib import Path
    Path(models['v1']['path'], 'model.safetensors').unlink()
    with pytest.raises(FileNotFoundError):
        jobs.initialize()
    assert not (jobs.store.root / 'registry/latest.json').exists()


def test_demo_initialization_reports_missing_v1_and_blocks_evaluation(local_registry):
    jobs, models, fixture = local_registry
    from pathlib import Path
    Path(models['v1']['path'], 'model.safetensors').unlink()
    result = jobs.initialize(allow_missing_baseline=True)
    assert result['evaluation_enabled'] is False
    catalog = jobs.list_models()
    assert catalog['default'] == 'v1_1' and catalog['activation_enabled'] is False
    assert catalog['evaluation_blocker'] == 'ORIGINAL_V1_UNAVAILABLE'
    assert next(m for m in catalog['models'] if m['id'] == 'v1')['state'] == 'UNAVAILABLE'
    assert jobs.list() == []
    c, _, _, staff, _, _ = fixture[0]
    response = c.get('/api/studio/models', headers=staff)
    assert response.status_code == 200 and response.json()['evaluation_enabled'] is False
    assert c.get('/api/studio/evaluations', headers=staff).status_code == 200
    request = {'dataset_version': 'a'*24, 'models': ['v1_1', 'candidate_r06']}
    with pytest.raises(ValueError, match='Original V1'):
        jobs.preflight(request)
    assert c.post('/api/studio/evaluations', headers=staff, json=request).status_code == 422
    assert jobs.list() == []  # Never queue an impossible rollback/evaluation.


@pytest.mark.parametrize('key', ['v1', 'v1_1', 'candidate_r06'])
def test_demo_mode_never_ignores_corrupt_artifacts(local_registry, key):
    jobs, models, _ = local_registry
    from pathlib import Path
    Path(models[key]['path'], 'config.json').write_text('tampered')
    with pytest.raises(ValueError, match='integrity'):
        jobs.initialize(allow_missing_baseline=True)
    assert not (jobs.store.root / 'registry/latest.json').exists()


def test_missing_default_is_fatal_even_in_demo_mode(local_registry):
    jobs, models, _ = local_registry
    from pathlib import Path
    Path(models['v1_1']['path'], 'model.safetensors').unlink()
    with pytest.raises(FileNotFoundError):
        jobs.initialize(allow_missing_baseline=True)


def test_intact_registry_remains_eligible_without_changing_fallback(local_registry):
    jobs, _, _ = local_registry
    assert jobs.initialize(allow_missing_baseline=True)['evaluation_enabled'] is True
    registry, _ = jobs.catalog()
    assert registry.fallback == 'v1'
    assert jobs.list_models()['evaluation_blocker'] is None


def test_missing_v1_does_not_hide_corruption_in_remaining_v1_files(local_registry):
    jobs, models, _ = local_registry
    from pathlib import Path
    Path(models['v1']['path'], 'model.safetensors').unlink()
    Path(models['v1']['path'], 'config.json').write_text('tampered')
    with pytest.raises(ValueError, match='integrity'):
        jobs.initialize(allow_missing_baseline=True)
