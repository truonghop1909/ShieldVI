"""Prepare local Vietnamese social-media corpora without conflating label tasks.

Offline by default. --download restores pinned public snapshots from catalog.json;
gated Hugging Face repositories require the user's own acceptance and are skipped.
No inference code, checkpoint, threshold or manual-review database is modified.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
import hashlib
import json
from pathlib import Path
import shutil
import unicodedata
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1] / 'datasets'
SPECS = {
    'vilexnorm': {
        'task': 'lexical_normalization', 'license': 'CC-BY-NC-SA-4.0',
        'source': 'https://github.com/ngxtnhi/ViLexNorm',
        'license_declaration': 'raw/vilexnorm/README.md',
        'label_origin': 'published_human_lexical_normalization',
        'files': {'train': 'data__train.csv', 'validation': 'data__dev.csv', 'test': 'data__test.csv'},
    },
    'vihos': {
        'task': 'offensive_spans', 'license': 'MIT',
        'source': 'https://github.com/phusroyal/ViHOS',
        'license_declaration': 'raw/vihos/LICENSE',
        'label_origin': 'published_human_offensive_span_annotation',
        'files': {'train': 'data__Span_Extraction_based_version__train.csv',
                  'validation': 'data__Span_Extraction_based_version__dev.csv', 'test': 'data__Test_data__test.csv'},
    },
    'victsd': {
        'task': 'comment_toxicity', 'license': 'not_reverified_for_local_user_copy',
        'source': 'local_user_provided_original_ViCTSD_files',
        'license_declaration': None,
        'label_origin': 'user_provided_original_ViCTSD_Toxicity',
        'files': {'train': 'ViCTSD_train.csv', 'validation': 'ViCTSD_valid.csv', 'test': 'ViCTSD_test.csv'},
    },
}


def key(text):
    # Preserve accents and slang in stored text. This is only a deduplication key.
    return ' '.join(unicodedata.normalize('NFC', text).casefold().split())


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def normalize_record(dataset, split, row, index):
    spec = SPECS[dataset]
    text = row.get('original' if dataset == 'vilexnorm' else 'content' if dataset == 'vihos' else 'Comment')
    if not isinstance(text, str) or not text.strip():
        raise ValueError('empty_text')
    result = {
        'id': f'{dataset}:{split}:{row.get("") or index}', 'text': text,
        'source_dataset': dataset, 'source_split': split, 'task': spec['task'],
        'label_origin': spec['label_origin'], 'license': spec['license'],
        'is_synthetic': False, 'toxicity_label': None, 'normalized_text': None,
        'offensive_span_indices': None, 'offensive_span_present': None,
    }
    if dataset == 'vilexnorm':
        normalized = row.get('normalized')
        if not isinstance(normalized, str) or not normalized.strip():
            raise ValueError('missing_normalization')
        result['normalized_text'] = normalized
    elif dataset == 'vihos':
        try:
            spans = json.loads(row['index_spans'])
        except (ValueError, KeyError) as exc:
            raise ValueError('invalid_span_json') from exc
        if not isinstance(spans, list) or any(type(i) is not int or not 0 <= i < len(text) for i in spans):
            raise ValueError('invalid_span_indices')
        # Do not strip/normalize this text: original character offsets must remain valid.
        result['offensive_span_indices'] = spans
        result['offensive_span_present'] = int(bool(spans))
    else:
        if row.get('Toxicity') not in ('0', '1'):
            raise ValueError('invalid_toxicity_label')
        result['toxicity_label'] = int(row['Toxicity'])
    return result


def text_keys(row):
    return {key(t) for t in (row['text'], row.get('normalized_text')) if t}


def label_signature(row):
    if row['task'] == 'lexical_normalization':
        return key(row['normalized_text'])
    if row['task'] == 'offensive_spans':
        return row['offensive_span_present']
    return row['toxicity_label']


def prepare_train(rows, blocked):
    counts = Counter(input_rows=len(rows), heldout_overlap_removed=0, duplicates_removed=0, conflicting_rows_removed=0)
    groups = defaultdict(list)
    for row in rows:
        if text_keys(row) & blocked:
            counts['heldout_overlap_removed'] += 1
        else:
            groups[key(row['text'])].append(row)
    prepared = []
    for group in groups.values():
        if len({label_signature(r) for r in group}) > 1:
            counts['conflicting_rows_removed'] += len(group)
        else:
            prepared.append(group[0])
            counts['duplicates_removed'] += len(group) - 1
    counts['prepared_rows'] = len(prepared)
    return prepared, dict(counts)


def normalization_candidates(rows):
    """Train-only alignments are review candidates, not context-free replacements."""
    candidates = {}
    for row in rows:
        original = row['text'].split()
        normalized = row['normalized_text'].split()
        matcher = SequenceMatcher(a=original, b=normalized, autojunk=False)
        for op, a, b, c, d in matcher.get_opcodes():
            if op != 'replace' or not 1 <= b-a <= 3 or not 1 <= d-c <= 4:
                continue
            before, after = ' '.join(original[a:b]), ' '.join(normalized[c:d])
            if key(before) == key(after) or not any(ch.isalpha() for ch in before):
                continue
            pair = (before, after)
            candidate = candidates.setdefault(pair, {'original': before, 'normalized': after,
                'occurrences': 0, 'example_row_ids': [], 'status': 'needs_context_review',
                'source_dataset': 'vilexnorm', 'source_split': 'train'})
            candidate['occurrences'] += 1
            if len(candidate['example_row_ids']) < 3:
                candidate['example_row_ids'].append(row['id'])
    return sorted(candidates.values(), key=lambda r: (-r['occurrences'], r['original'], r['normalized']))


def export_victsd_csv(path, rows):
    if any(r['task'] != 'comment_toxicity' or r['toxicity_label'] not in (0, 1) for r in rows):
        raise ValueError('Only original binary toxicity labels can enter this CSV')
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['', 'Comment', 'Toxicity', 'source_dataset'])
        writer.writerows([r['id'], r['text'], r['toxicity_label'], r['source_dataset']] for r in rows)


def restore_downloads(catalog):
    for info in catalog.values():
        if info.get('gated') or info.get('status') == 'requires_user_acceptance':
            continue
        for item in info.get('downloads', []):
            destination = (ROOT / item['local_file']).resolve()
            if not destination.is_relative_to(ROOT.resolve()):
                raise ValueError('Download path escapes datasets directory')
            request = Request(item['url'], headers={'User-Agent': 'ShieldVI-dataset-import'})
            with urlopen(request, timeout=45) as response:
                content = response.read()
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)


def build(download=False, victsd_from=None):
    catalog = json.loads((ROOT / 'raw' / 'catalog.json').read_text(encoding='utf-8'))
    if download:
        restore_downloads(catalog)
    if victsd_from:
        destination = ROOT / 'raw' / 'victsd'
        destination.mkdir(parents=True, exist_ok=True)
        for filename in SPECS['victsd']['files'].values():
            shutil.copyfile(Path(victsd_from) / filename, destination / filename)
    records, summaries, rejections = {}, {}, []
    for dataset, spec in SPECS.items():
        if not (ROOT / 'raw' / dataset).is_dir():
            continue
        splits, source_files = {}, []
        for split, filename in spec['files'].items():
            path = ROOT / 'raw' / dataset / filename
            with path.open(encoding='utf-8-sig', newline='') as f:
                raw = list(csv.DictReader(f))
            rows = []
            for index, row in enumerate(raw):
                try:
                    rows.append(normalize_record(dataset, split, row, index))
                except ValueError as exc:
                    rejections.append({'dataset': dataset, 'split': split, 'row': index, 'reason': str(exc)})
            if len({r['id'] for r in rows}) != len(rows):
                raise ValueError(f'Duplicate source row IDs: {dataset}/{split}')
            splits[split] = rows
            write_jsonl(ROOT / 'processed' / dataset / f'{split}.jsonl', rows)
            source_files.append({'split': split, 'path': path.relative_to(ROOT).as_posix(),
                                 'sha256': sha256(path), 'raw_rows': len(raw), 'loaded_rows': len(rows)})
        records[dataset] = splits
        summaries[dataset] = {
            **{k: v for k, v in spec.items() if k != 'files'},
            'revision': catalog.get(dataset, {}).get('revision'),
            'raw_files': source_files, 'split_counts': {s: len(r) for s, r in splits.items()},
            'total_rows': sum(len(r) for r in splits.values()),
        }
        summaries[dataset]['label_distribution_by_split'] = {
            split: (dict(Counter(str(r['toxicity_label']) for r in rows)) if dataset == 'victsd' else
                    dict(Counter(str(r['offensive_span_present']) for r in rows)) if dataset == 'vihos' else
                    dict(Counter('unchanged' if r['text'] == r['normalized_text'] else 'normalized' for r in rows)))
            for split, rows in splits.items()
        }
        # Hash upstream license/readme declarations as well as actual data files.
        declaration = spec.get('license_declaration')
        if declaration:
            summaries[dataset]['license_declaration_sha256'] = sha256(ROOT / declaration)
    # Keep all official holdouts intact. Block their original AND normalized views
    # from every task's prepared train pool to avoid multi-task leakage.
    blocked = set()
    for splits in records.values():
        for split in ('validation', 'test'):
            for row in splits[split]:
                blocked.update(text_keys(row))
    plans = []
    for dataset, splits in records.items():
        prepared, stats = prepare_train(splits['train'], blocked)
        summaries[dataset]['training_cleanup'] = stats
        path = ROOT / 'prepared' / f'{dataset}_train.jsonl'
        write_jsonl(path, prepared)
        if dataset == 'victsd':
            export_victsd_csv(ROOT / 'prepared' / 'victsd_train.csv', prepared)
            for split in ('validation', 'test'):
                export_victsd_csv(ROOT / 'prepared' / f'victsd_{split}.csv', splits[split])
        if dataset == 'vilexnorm':
            pairs = normalization_candidates(prepared)
            write_jsonl(ROOT / 'review' / 'teencode_normalization_candidates.jsonl', pairs)
            summaries[dataset]['train_only_alignment_candidates'] = len(pairs)
        plans.append({'dataset': dataset, 'task': SPECS[dataset]['task'],
                      'train': path.relative_to(ROOT).as_posix(),
                      'validation': f'processed/{dataset}/validation.jsonl',
                      'test': f'processed/{dataset}/test.jsonl',
                      'automatic_mapping_to_toxicity': False})
    challenge_path = ROOT / 'review' / 'mxh_style_challenge.json'
    challenge_count = 0
    if challenge_path.exists():
        challenge = json.loads(challenge_path.read_text(encoding='utf-8'))
        challenge_count = len(challenge['items'])
        if any(r.get('human_label') is not None or r.get('is_synthetic') is not True for r in challenge['items']):
            raise ValueError('Unreviewed synthetic challenge must not claim human labels')
        base_time = datetime(2026, 10, 29, 18, 0, tzinfo=timezone(timedelta(hours=7)))
        comments = [{'comment_id': r['comment_id'], 'user_id': r['user_id'], 'text': r['text'],
                     'parent_id': r['parent_id'], 'mentioned_user_ids': [],
                     'timestamp': (base_time + timedelta(minutes=i)).isoformat()}
                    for i, r in enumerate(challenge['items'])]
        write_json(ROOT.parent / 'examples' / 'DEMO_MXH_TEENCODE_NOILAI_30.json', {
            'thread_id': 'DEMO_MXH_TEENCODE_NOILAI_30', 'profile': 'conservative',
            '_provenance': 'AI-authored fictional challenge, not real social-media data or gold labels.',
            'comments': comments,
        })
    manifest = {
        'schema_version': 1, 'prepared_date': '2026-10-29',
        'sources': summaries,
        'gated_sources': {k: {**v, 'status': 'requires_user_acceptance', 'downloaded_rows': 0}
                          for k, v in catalog.items() if v.get('gated')},
        'totals': {'new_public_rows': sum(s['total_rows'] for k, s in summaries.items() if k != 'victsd'),
                   'existing_victsd_rows': summaries.get('victsd', {}).get('total_rows', 0),
                   'all_public_rows': sum(s['total_rows'] for s in summaries.values()),
                   'prepared_training_rows_across_distinct_tasks': sum(s['training_cleanup']['prepared_rows'] for s in summaries.values()),
                   'rejected_invalid_rows': len(rejections), 'synthetic_challenge_rows_not_for_training': challenge_count},
        'policy': 'Preserve social spelling and official holdouts. Keep toxicity, normalization and offensive-span labels separate. No checkpoint is trained or changed by this import.',
    }
    write_json(ROOT / 'manifest.json', manifest)
    write_json(ROOT / 'training_plan.json', {'tasks': plans, 'checkpoint_modified': False})
    write_jsonl(ROOT / 'review' / 'import_rejections.jsonl', rejections)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true', help='Restore pinned PUBLIC snapshots; gated repositories are skipped')
    parser.add_argument('--import-victsd-from', type=Path, help='Copy the existing original three ViCTSD CSVs into this data directory')
    args = parser.parse_args()
    print(json.dumps(build(args.download, args.import_victsd_from)['totals'], indent=2))
