import hashlib
import json
from pathlib import Path
import shutil
import unicodedata

import pytest

from app.lexical import DATA_DIR, detect, load_rules
from scripts import import_lexicon


@pytest.mark.parametrize('text', [
    'Các bạn đã lớn và có công việc ổn định.',
    'Tôi đeo kính, mua bưởi và cắt tóc.',
    'Con trai tôi thích con chó và con mèo.',
    'Mình bực mình nhưng chỉ trích ý tưởng, không công kích cá nhân.',
    'Mình không đồng ý với kết luận; bạn có thể đưa bằng chứng không?',
    'Tôi nghĩ lập luận còn thiếu dữ kiện. Chúng ta nên kiểm tra lại.',
    'Cảm ơn các bác, buổi họp rất hữu ích.',
    'Hello, my class will discuss the assessment and job tomorrow.',
    'The Scunthorpe assignment uses a cocktail example.',
    'The shell and hello commands work on a Dell computer.',
    'I disagree with your argument; please provide evidence.',
    'shuffle sh1tbox xfuck fuckery éfuck fucké fuck_123 abc_vcl vcl123',
    'tôi thích văn học và tranh luận bình thường',
])
def test_false_positive_benign_and_normal_debate(text):
    result = detect(text)
    assert result['lexical_signals'] == []
    assert not result['profanity_detected']
    assert not result['lexical_review_recommended']
    assert not result['directed_insult_candidate']


@pytest.mark.parametrize('text', [
    'Bạn không nên nói óc chó với người khác.',
    'Đừng chửi người ta là óc chó nữa.',
    'Xin lỗi vì đã nói địt mẹ bạn.',
    'Tôi trích dẫn câu f.u.c.k you để báo cáo.',
    '“You are an idiot”',
    '"fuck you"',
    "'óc chó'",
    'The word idiot is an insult.',
])
def test_false_positive_quoted_reported_and_apology(text):
    result = detect(text)
    # Presence is real, but quoted speech is not treated as a direct attack.
    assert result['lexical_signals']
    assert result['reported_or_apology_context']
    assert not result['directed_insult_candidate']
    assert all('trích dẫn' in signal['reason'] for signal in result['lexical_signals'])


@pytest.mark.parametrize('text', [
    'Đm máy hết pin mất rồi!',
    'Đm con chuột hết pin.',
    'dm may het pin roi',
    'Sh1t, my laptop crashed again.',
    'f*ck this broken charger',
    'Holy shit, I forgot the keys.',
])
def test_false_positive_untargeted_exclamations(text):
    result = detect(text)
    assert result['profanity_detected']
    assert result['lexical_review_recommended']
    assert not result['directed_insult_candidate']


@pytest.mark.parametrize('text,canonical,language', [
    ('F.u.C.k you', 'fuck', 'en'), ('f*ck', 'fuck', 'en'),
    ('f**k', 'fuck', 'en'), ('f***k', 'fuck', 'en'),
    ('sh1t', 'shit', 'en'), ('$h!t', 'shit', 'en'), ('5h17', 'shit', 'en'),
    ('b1tch', 'bitch', 'en'), ('a55hole', 'asshole', 'en'),
    ('Đ.ị.t m.ẹ mày', 'địt mẹ', 'vi'), ('dit me', 'địt mẹ', 'vi'),
    ('đ.m', 'địt mẹ / đụ má', 'vi'), ('dcm', 'địt mẹ / đụ má', 'vi'),
    ('đéo', 'đéo', 'vi'), ('deo', 'đéo', 'vi'), ('d3o', 'đéo', 'vi'),
    ('óc chó', 'óc chó', 'vi'), ('oc cho', 'óc chó', 'vi'),
])
def test_reviewed_obfuscations_and_original_span(text, canonical, language):
    signals = detect(text)['lexical_signals']
    assert signals
    signal = signals[0]
    assert signal['canonical_form'] == canonical
    assert signal['language'] == language
    assert signal['matched_form'] == text[signal['start']:signal['end']]
    assert signal['category'] in import_lexicon.CATEGORIES
    assert signal['source_ids'] and signal['reason']


def test_unicode_normalization_preserves_original_accents_and_offsets():
    text = '🙂 ' + unicodedata.normalize('NFD', 'ĐỊT MẸ') + ' mày'
    signal = detect(text)['lexical_signals'][0]
    assert signal['canonical_form'] == 'địt mẹ'
    assert signal['matched_form'] == text[2:signal['end']]
    assert signal['start'] == 2


def test_longest_phrase_no_nested_duplicates_and_repeated_occurrences():
    result = detect('địt mẹ, địt mẹ. f.u.c.k!')
    assert [s['canonical_form'] for s in result['lexical_signals']] == ['địt mẹ', 'địt mẹ', 'fuck']


def test_canonical_is_the_original_word_not_just_a_family_name():
    for text, canonical in [('idiot', 'idiot'), ('a$$hole', 'asshole'), ('nao tan', 'não tàn'), ('vagina', 'vagina')]:
        assert detect(text)['lexical_signals'][0]['canonical_form'] == canonical


@pytest.mark.parametrize('text,category', [
    ('cc', 'ambiguous'), ('lon', 'ambiguous'), ('cac', 'ambiguous'),
    ('Giáo dục về quan hệ tình dục và âm đạo.', 'other_sensitive'),
    ('Medical information about the penis and vagina.', 'other_sensitive'),
    ('News reports about suicide prevention.', 'other_sensitive'),
])
def test_sensitive_and_ambiguous_are_not_automatic_review_alerts(text, category):
    result = detect(text)
    assert result['lexical_signals']
    assert all(s['category'] == category for s in result['lexical_signals'])
    assert not result['profanity_detected']
    assert not result['lexical_review_recommended']
    assert not result['directed_insult_candidate']


def test_directed_and_quoted_context_are_local_to_sentence():
    result = detect('Tôi trích dẫn "idiot". Fuck you!')
    assert result['reported_or_apology_context']
    assert result['directed_insult_candidate']
    assert 'trích dẫn' in result['lexical_signals'][0]['reason']
    assert 'hướng tới người' in result['lexical_signals'][1]['reason']


def test_clean_import_comments_blank_duplicates_and_accents():
    entries, stats = import_lexicon.clean_lines('\ufeff# note\n\n  FUCK  \nfuck\n// note\n / . \ncặc\ncác\ncac\n')
    assert entries == ['fuck', 'cặc', 'các', 'cac']
    assert (stats['raw_lines'], stats['blank'], stats['comments'], stats['invalid'], stats['duplicates_within_source']) == (9, 1, 2, 1, 1)


def test_pinned_sources_counts_licenses_and_statuses():
    manifest = json.loads((DATA_DIR / 'manifest.json').read_text(encoding='utf-8'))
    candidates = json.loads((DATA_DIR / 'candidates.json').read_text(encoding='utf-8'))
    totals = manifest['totals']
    assert len(manifest['sources']) == 3
    for source in manifest['sources']:
        raw = (DATA_DIR / source['local_file']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == source['sha256']
        assert len(source['revision']) == 40
        assert source['license'] in ('MIT', 'CC0-1.0')
        assert (DATA_DIR / source['local_license']).is_file()
        assert source['raw_lines'] == sum(source[k] for k in ('blank', 'comments', 'invalid', 'duplicates_within_source', 'unique_entries'))
    assert totals['raw_lines'] == totals['removed_during_cleanup'] + len(candidates)
    assert totals['unique_imported_entries'] == totals['enabled_imported_entries'] + totals['pending_review_entries'] + totals['excluded_entries']
    assert len({c['term'] for c in candidates}) == len(candidates)
    assert {c['status'] for c in candidates} == {'enabled_reviewed', 'pending_review', 'excluded'}
    assert all(c['category'] == 'ambiguous' for c in candidates if c['status'] == 'pending_review')
    assert next(c for c in candidates if c['term'] == 'con trai')['status'] == 'excluded'
    for source in manifest['sources']:
        assert any(source['id'] in c['sources'] and c['status'] == 'enabled_reviewed' for c in candidates)


def test_rebuild_is_offline_and_reproducible(monkeypatch, tmp_path):
    isolated = tmp_path / 'lexicon'
    shutil.copytree(DATA_DIR, isolated)
    monkeypatch.setattr(import_lexicon, 'ROOT', isolated)
    monkeypatch.setattr(import_lexicon, 'urlopen', lambda *a, **k: pytest.fail('Offline rebuild used network'))
    import_lexicon.build()
    for filename in ['active.json', 'candidates.json', 'manifest.json']:
        assert (isolated / filename).read_bytes() == (DATA_DIR / filename).read_bytes()


def test_pending_rules_are_never_loaded(tmp_path):
    active = json.loads((DATA_DIR / 'active.json').read_text(encoding='utf-8'))
    for rule in active['rules']:
        rule['status'] = 'pending_review'
    path = tmp_path / 'disabled.json'
    path.write_text(json.dumps(active), encoding='utf-8')
    assert load_rules(path) == []


def test_detection_uses_no_network(monkeypatch):
    import socket
    monkeypatch.setattr(socket, 'socket', lambda *a, **k: pytest.fail('Detector attempted network access'))
    assert detect('f.u.c.k you')['lexical_signals']


@pytest.mark.parametrize('text', [
    'Các bạn đã lớn.', 'Tôi trích dẫn "fuck you" để báo cáo.',
    'Đm máy hết pin rồi.', 'Tôi không đồng ý với lập luận của bạn.',
    'Medical information about sexual health.', 'f*ck you',
])
def test_api_additive_evidence_never_changes_probability_or_threshold(client, text):
    response = client.post('/api/analyze', json={'thread_id': 'LEXICON_FP', 'comments': [
        {'comment_id': 'one', 'user_id': 'u1', 'text': text, 'timestamp': '2026-10-29T00:00:00Z'}
    ]})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data['model_threshold'] == 0.41
    assert data['repeated_rule_threshold'] == 0.41
    assert data['evidence'] == []
    row = data['comments'][0]
    assert row['toxicity_score'] == 0.02  # Original predictor output, not a lexical score.
    assert not row['toxic_for_moderation']
    assert not row['toxic_for_repeated_rule']
    for signal in row['lexical_signals']:
        assert {'canonical_form', 'language', 'category', 'reason', 'matched_form'} <= signal.keys()


def test_lexical_entries_do_not_create_repeated_harassment(client):
    response = client.post('/api/analyze', json={'thread_id': 'LEXICON_REPEAT', 'comments': [
        {'comment_id': 'a', 'user_id': 'u1', 'text': 'Xin chào', 'timestamp': '2026-10-29T00:00:00Z'},
        {'comment_id': 'b', 'user_id': 'u2', 'parent_id': 'a', 'text': 'f*ck you', 'timestamp': '2026-10-29T00:01:00Z'},
        {'comment_id': 'c', 'user_id': 'u2', 'parent_id': 'a', 'text': 'mày là óc chó', 'timestamp': '2026-10-29T00:02:00Z'},
    ]})
    assert response.status_code == 200
    data = response.json()
    assert all(not row['toxic_for_moderation'] for row in data['comments'])
    assert data['evidence'] == []
    assert not data['suspected_repeated_harassment']
