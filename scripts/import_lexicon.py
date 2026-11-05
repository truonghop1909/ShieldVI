"""Rebuild the offline lexicon from pinned source snapshots and explicit reviews.

No network by default. --download restores only the pinned files in snapshots.json;
updating revisions and reviewing new aliases is a separate, intentional operation.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import unicodedata
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1] / 'services' / 'moderation-ai' / 'app' / 'data' / 'lexicon'
SOURCES = [
    ('blue_eyes_vi', 'blue_eyes_vi', 'vn_offensive_words.txt', 'vi', 'MIT', 'LICENSE.md'),
    ('ldnoobw_v2_vi', 'ldnoobw_v2', 'data/vi.txt', 'vi', 'CC0-1.0', 'LICENSE'),
    ('ldnoobw_v2_en', 'ldnoobw_v2', 'data/en.txt', 'en', 'CC0-1.0', 'LICENSE'),
]
CATEGORIES = {'profanity', 'directed_insult', 'ambiguous', 'other_sensitive'}


def normalize(term: str) -> str:
    # Do NOT remove accents here: cac/các/cặc and lon/lớn/lồn are different.
    return ' '.join(unicodedata.normalize('NFC', term).casefold().split())


def clean_lines(text: str) -> tuple[list[str], dict]:
    counts = Counter(raw_lines=0, blank=0, comments=0, invalid=0, duplicates_within_source=0)
    terms, seen = [], set()
    for line in text.lstrip('\ufeff').splitlines():
        counts['raw_lines'] += 1
        term = normalize(line)
        if not term:
            counts['blank'] += 1
        elif term.startswith(('#', '//')):
            counts['comments'] += 1
        elif not any(c.isalnum() for c in term) or any(unicodedata.category(c) == 'Cc' for c in term):
            counts['invalid'] += 1
        elif term in seen:
            counts['duplicates_within_source'] += 1
        else:
            terms.append(term)
            seen.add(term)
    counts['unique_entries'] = len(terms)
    return terms, dict(counts)


def write_json(path: Path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def build(download: bool = False) -> dict:
    snapshots = json.loads((ROOT / 'sources' / 'snapshots.json').read_text(encoding='utf-8'))
    if download:
        for snapshot in snapshots.values():
            for info in snapshot['files'].values():
                request = Request(info['url'], headers={'User-Agent': 'ShieldVI-offline-lexicon-import'})
                with urlopen(request, timeout=30) as response:
                    (ROOT / 'sources' / info['local_file']).write_bytes(response.read())
    policy = json.loads((ROOT / 'reviewed_rules.json').read_text(encoding='utf-8'))
    rules = policy['rules']
    assert len({r['id'] for r in rules}) == len(rules), 'Duplicate review rule IDs'
    lookup, patterns = {}, []
    for rule in rules:
        assert rule['category'] in CATEGORIES
        for alias in rule['aliases']:
            key = normalize(alias)
            assert key not in lookup, f'Duplicate reviewed alias: {key}'
            lookup[key] = rule
        for pattern in rule.get('patterns', []):
            patterns.append((re.compile(pattern), rule))
    excluded = {normalize(t) for t in policy['excluded']}
    assert not excluded.intersection(lookup), 'An excluded term cannot be enabled'
    entries, source_stats = {}, []
    for ident, snapshot_id, filename, language, license_id, license_file in SOURCES:
        snapshot = snapshots[snapshot_id]
        info = snapshot['files'][filename]
        content = (ROOT / 'sources' / info['local_file']).read_bytes()
        terms, counts = clean_lines(content.decode('utf-8-sig'))
        counts['duplicates_across_sources'] = 0
        for term in terms:
            if term in entries:
                counts['duplicates_across_sources'] += 1
            entry = entries.setdefault(term, {'term': term, 'sources': [], 'language_hints': []})
            entry['sources'].append(ident)
            if language not in entry['language_hints']:
                entry['language_hints'].append(language)
        source_stats.append({
            'id': ident, 'language_hint': language, 'repository': snapshot['repository'],
            'revision': snapshot['revision'], 'url': info['url'],
            'license': license_id, 'license_url': snapshot['files'][license_file]['url'],
            'local_file': 'sources/' + info['local_file'],
            'local_license': 'sources/' + snapshot['files'][license_file]['local_file'],
            'sha256': hashlib.sha256(content).hexdigest(), **counts,
        })
    active = []
    for rule in rules:
        active.append({**rule, 'aliases': list(dict.fromkeys(normalize(a) for a in rule['aliases'])),
                       'sources': ['shieldvi_reviewed'], 'status': 'enabled_reviewed'})
    active_by_id = {rule['id']: rule for rule in active}
    for entry in entries.values():
        term = entry['term']
        rule = lookup.get(term) or next((r for p, r in patterns if p.fullmatch(term)), None)
        if term in excluded:
            entry.update(status='excluded', category='ambiguous', canonical=term,
                         language=entry['language_hints'][0], reason='Reviewed: ordinary/polysemous term; not enabled.')
        elif rule:
            canonical = rule.get('canonical_by_alias', {}).get(term, rule['canonical'])
            entry.update(status='enabled_reviewed', category=rule['category'], canonical=canonical,
                         language=rule['language'], rule_id=rule['id'], reason=rule['reason'])
            target = active_by_id[rule['id']]
            if term not in target['aliases']:
                target['aliases'].append(term)
            target['sources'] = sorted(set(target['sources'] + entry['sources']))
        else:
            entry.update(status='pending_review', category='ambiguous', canonical=term,
                         language=entry['language_hints'][0],
                         reason='Unreviewed source entry; language/category may be inaccurate. Disabled until explicitly reviewed.')
    statuses = Counter(e['status'] for e in entries.values())
    raw_lines = sum(s['raw_lines'] for s in source_stats)
    totals = {
        'raw_lines': raw_lines,
        'removed_blank': sum(s['blank'] for s in source_stats),
        'removed_comments': sum(s['comments'] for s in source_stats),
        'removed_invalid': sum(s['invalid'] for s in source_stats),
        'removed_duplicates_within_sources': sum(s['duplicates_within_source'] for s in source_stats),
        'removed_duplicates_across_sources': sum(s['duplicates_across_sources'] for s in source_stats),
        'unique_imported_entries': len(entries),
        'enabled_imported_entries': statuses['enabled_reviewed'],
        'pending_review_entries': statuses['pending_review'],
        'excluded_entries': statuses['excluded'],
        'active_rules': len(active),
        'active_aliases_including_project_rules': sum(len(r['aliases']) for r in active),
        'categories_enabled': dict(Counter(r['category'] for r in active)),
    }
    totals['removed_during_cleanup'] = raw_lines - len(entries)
    manifest = {'schema_version': 1, 'review_date': policy['review']['date'],
                'normalization': 'NFC + casefold + whitespace; accents preserved; global exact-term deduplication.',
                'activation_policy': policy['review'], 'totals': totals, 'sources': source_stats}
    write_json(ROOT / 'candidates.json', sorted(entries.values(), key=lambda e: e['term']))
    write_json(ROOT / 'active.json', {'schema_version': 1, 'rules': active})
    write_json(ROOT / 'manifest.json', manifest)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--download', action='store_true', help='Restore pinned source/license snapshots before rebuilding')
    args = parser.parse_args()
    print(json.dumps(build(args.download)['totals'], indent=2))
