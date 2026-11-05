import json
from pathlib import Path

import pytest

from app.schemas import AnalyzeRequest
from scripts import prepare_social_datasets as data


def test_normalization_pair_is_not_a_toxicity_label():
    row = data.normalize_record('vilexnorm', 'train', {'original': 't ko bt :))', 'normalized': 'tôi không biết :))'}, 0)
    assert row['text'] == 't ko bt :))'
    assert row['normalized_text'] == 'tôi không biết :))'
    assert row['toxicity_label'] is None
    assert row['offensive_span_present'] is None
    assert row['is_synthetic'] is False


def test_span_offsets_and_raw_spelling_are_preserved():
    original = '  Đm máy hết pin :)) '
    row = data.normalize_record('vihos', 'train', {'content': original, 'index_spans': '[2,3]'}, 1)
    assert row['text'] == original
    assert ''.join(row['text'][i] for i in row['offensive_span_indices']) == 'Đm'
    assert row['offensive_span_present'] == 1
    assert row['toxicity_label'] is None


@pytest.mark.parametrize('spans', ['[-1]', '[999]', '[true]', '["1"]', '{}', '__import__("os")'])
def test_bad_span_annotations_are_rejected_without_evaluation(spans):
    with pytest.raises(ValueError):
        data.normalize_record('vihos', 'train', {'content': 'hello', 'index_spans': spans}, 0)


def test_training_excludes_normalized_views_of_heldout_text():
    row = data.normalize_record('vilexnorm', 'train', {'original': 'ko bt', 'normalized': 'không biết'}, 0)
    prepared, counts = data.prepare_train([row], {data.key('KHÔNG BIẾT')})
    assert prepared == []
    assert counts['heldout_overlap_removed'] == 1


def test_conflicting_expansions_are_quarantined_and_accents_remain_distinct():
    rows = [data.normalize_record('vilexnorm', 'train', {'original': 't', 'normalized': target}, i)
            for i, target in enumerate(['tôi', 'tao'])]
    prepared, counts = data.prepare_train(rows, set())
    assert prepared == []
    assert counts['conflicting_rows_removed'] == 2
    assert len({data.key(t) for t in ['các', 'cac', 'cặc']}) == 3


def test_proxy_and_normalization_rows_cannot_enter_toxicity_csv(tmp_path):
    span = data.normalize_record('vihos', 'train', {'content': 'idiot', 'index_spans': '[0,1]'}, 0)
    normalized = data.normalize_record('vilexnorm', 'train', {'original': 'ko', 'normalized': 'không'}, 0)
    for row in [span, normalized]:
        with pytest.raises(ValueError):
            data.export_victsd_csv(tmp_path / 'bad.csv', [row])


def test_gated_sources_never_trigger_anonymous_download(monkeypatch, tmp_path):
    monkeypatch.setattr(data, 'ROOT', tmp_path)
    monkeypatch.setattr(data, 'urlopen', lambda *a, **k: pytest.fail('A gated source was requested'))
    data.restore_downloads({'gated': {'gated': 'auto', 'downloads': [
        {'url': 'https://example.invalid/train.csv', 'local_file': 'raw/train.csv'}
    ]}})
    assert not (tmp_path / 'raw').exists()


def test_download_destinations_are_confined_to_data_directory(monkeypatch, tmp_path):
    monkeypatch.setattr(data, 'ROOT', tmp_path)
    with pytest.raises(ValueError, match='escapes'):
        data.restore_downloads({'public': {'downloads': [
            {'url': 'https://example.invalid/train.csv', 'local_file': '../escape.csv'}
        ]}})


def read_jsonl(path):
    with path.open(encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def test_downloaded_snapshot_counts_hashes_and_separate_tasks():
    manifest = json.loads((data.ROOT / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['totals']['new_public_rows'] == 21523
    assert manifest['totals']['existing_victsd_rows'] == 10000
    expected = {'vilexnorm': 10467, 'vihos': 11056, 'victsd': 10000}
    for source, count in expected.items():
        info = manifest['sources'][source]
        assert info['total_rows'] == count
        for raw in info['raw_files']:
            assert data.sha256(data.ROOT / raw['path']) == raw['sha256']
            rows = read_jsonl(data.ROOT / 'processed' / source / f"{raw['split']}.jsonl")
            assert len(rows) == raw['loaded_rows']
            assert all(r['task'] == data.SPECS[source]['task'] and not r['is_synthetic'] for r in rows)
            if source != 'victsd':
                assert all(r['toxicity_label'] is None for r in rows)
    assert set(manifest['gated_sources']) == {'vihsd', 'vithsd'}
    assert all(s['downloaded_rows'] == 0 for s in manifest['gated_sources'].values())


def test_all_prepared_tasks_exclude_every_official_holdout():
    blocked = set()
    for source in data.SPECS:
        for split in ('validation', 'test'):
            for row in read_jsonl(data.ROOT / 'processed' / source / f'{split}.jsonl'):
                blocked.update(data.text_keys(row))
    total = 0
    for source in data.SPECS:
        rows = read_jsonl(data.ROOT / 'prepared' / f'{source}_train.jsonl')
        assert all(not (data.text_keys(row) & blocked) for row in rows)
        assert len({data.key(row['text']) for row in rows}) == len(rows)
        total += len(rows)
    assert total == 24120


def test_alignment_review_candidates_only_use_prepared_normalization_train():
    rows = read_jsonl(data.ROOT / 'review' / 'teencode_normalization_candidates.jsonl')
    ids = {r['id'] for r in read_jsonl(data.ROOT / 'prepared' / 'vilexnorm_train.jsonl')}
    assert len(rows) == 4317
    assert all(r['source_split'] == 'train' and r['status'] == 'needs_context_review' for r in rows)
    assert all(set(r['example_row_ids']) <= ids for r in rows)


def test_natural_style_demo_is_valid_and_explicitly_not_gold():
    root = data.ROOT.parent
    seed = json.loads((data.ROOT / 'review' / 'mxh_style_challenge.json').read_text(encoding='utf-8'))
    assert not seed['is_gold'] and not seed['training_eligible']
    assert all(r['human_label'] is None and r['is_synthetic'] for r in seed['items'])
    assert any('noi_lai_candidate' in r['phenomena'] for r in seed['items'])
    example = json.loads((root / 'examples' / 'DEMO_MXH_TEENCODE_NOILAI_30.json').read_text(encoding='utf-8'))
    request = AnalyzeRequest.model_validate(example)
    assert len(request.comments) == 30
    assert [c.text for c in request.comments] == [r['text'] for r in seed['items']]
