"""Offline, reviewed lexical evidence. Never changes ViSoBERT probabilities/labels.

Import snapshots and pending candidates are deliberately NOT executable rules.
Only active.json, produced from reviewed_rules.json, is loaded once per process.
"""
from __future__ import annotations

import json
from pathlib import Path
import re
import unicodedata

DATA_DIR = Path(__file__).resolve().parent / 'data' / 'lexicon'


def fold(value: str) -> str:
    """Accent folding for context cues only, never for indiscriminate word matching."""
    value = unicodedata.normalize('NFKD', value.casefold()).replace('đ', 'd')
    return ''.join(ch for ch in value if not unicodedata.combining(ch))


def normalized_view(text: str) -> tuple[str, list[tuple[int, int]]]:
    """NFC/casefold plus offsets back to the exact original, including NFD accents."""
    characters, offsets = [], []
    for cluster in re.finditer(r'[^\W\d_][\u0300-\u036f]*|[\s\S]', text):
        value = unicodedata.normalize('NFC', cluster.group()).casefold()
        characters.append(value)
        offsets.extend([(cluster.start(), cluster.end())] * len(value))
    return ''.join(characters), offsets


def load_rules(path: Path = DATA_DIR / 'active.json'):
    data = json.loads(path.read_text(encoding='utf-8'))
    compiled = []
    for rule in data['rules']:
        if rule.get('status') != 'enabled_reviewed':
            continue
        aliases = [r'\s+'.join(re.escape(part) for part in a.split())
                   for a in sorted(rule['aliases'], key=len, reverse=True)]
        # Unicode word boundaries protect words in every script, numbers and IDs.
        expressions = aliases + rule.get('patterns', [])
        compiled.append((rule, re.compile(r'(?<!\w)(?:' + '|'.join(expressions) + r')(?!\w)')))
    return compiled


COMPILED = load_rules()
DIRECTED = re.compile(r'(?<!\w)(?:mày|bạn|bác|cậu|may|ban|bac|cau|you|your)(?!\w)')
MACHINE = re.compile(r'(?<!\w)may\s+(?:tinh|het\s+pin|in|giat|lanh)(?!\w)')
REPORTED = re.compile(
    r'\b(?:xin\s+loi|rut\s+lai|dung\s+noi|khong\s+nen|trich\s+dan|tu\s+do|goi\s+la|'
    r'cau\s+chui|noi\s+rang|da\s+chui|dung\s+chui|bao\s+nguoi\s+khac|report|'
    r'quoted|quotation|the\s+word|apologi[sz]e|sorry\s+for)\b'
)
QUOTED = re.compile(r'“[^”]*”|«[^»]*»|"[^"\n]*"|(?<!\w)\x27[^\x27\n]+\x27(?!\w)')
SENTENCE_BREAK = re.compile(r'[!?;\n]|\.(?=\s|$)')


def detect(text: str) -> dict:
    plain, offsets = normalized_view(text)
    candidates = []
    for rule, pattern in COMPILED:
        for match in pattern.finditer(plain):
            candidates.append((match.start(), match.end(), rule))
    # Keep the longest phrase at each overlapping location; no nested duplicate alerts.
    candidates.sort(key=lambda item: (item[0], -(item[1] - item[0]), item[2]['id']))
    selected = []
    for start, end, rule in candidates:
        if selected and start < selected[-1][1]:
            continue
        selected.append((start, end, rule))
    quotes = [(m.start(), m.end()) for m in QUOTED.finditer(plain)]
    breaks = [(m.start(), m.end()) for m in SENTENCE_BREAK.finditer(plain)]
    signals, any_reported, any_directed = [], False, False
    for start, end, rule in selected:
        left = max((b for _, b in breaks if b <= start), default=0)
        right = min((a for a, _ in breaks if a >= end), default=len(plain))
        sentence = plain[left:right]
        reported = any(a <= start and end <= b for a, b in quotes) or bool(REPORTED.search(fold(sentence)))
        nearby = plain[max(left, start - 40):min(right, end + 40)]
        nearby = MACHINE.sub('', nearby)
        addressed = bool(DIRECTED.search(nearby))
        # Rude imperatives already imply an addressee. A bare noun or exclamation does not.
        directed = rule['category'] in ('profanity', 'directed_insult') and not reported and (
            addressed or rule['id'] == 'en_rude_command'
        )
        any_reported |= reported
        any_directed |= directed
        reason = rule['reason']
        if reported:
            reason += ' Có dấu hiệu trích dẫn/tường thuật/xin lỗi; không coi là công kích trực tiếp.'
        elif directed:
            reason += ' Có dấu hiệu hướng tới người gần cụm từ; cần xác nhận thủ công.'
        elif rule['category'] == 'profanity':
            reason += ' Chưa có đủ dấu hiệu nhắm vào người; có thể là cảm thán.'
        original_start, original_end = offsets[start][0], offsets[end - 1][1]
        matched_key = ' '.join(plain[start:end].split())
        canonical = rule.get('canonical_by_alias', {}).get(matched_key, rule['canonical'])
        signals.append({
            'rule_id': rule['id'], 'category': rule['category'],
            'matched_form': text[original_start:original_end],
            'canonical_form': canonical, 'language': rule['language'],
            'strength': rule['strength'], 'reason': reason,
            'source_ids': rule['sources'], 'start': original_start, 'end': original_end,
        })
    return {
        'profanity_detected': any(s['category'] == 'profanity' for s in signals),
        'lexical_review_recommended': any(s['category'] in ('profanity', 'directed_insult') for s in signals),
        'directed_insult_candidate': any_directed,
        'ambiguous_only': bool(signals) and all(s['category'] == 'ambiguous' for s in signals),
        'reported_or_apology_context': any_reported,
        'lexical_signals': signals,
    }
