import pytest
from app.lexical import detect

@pytest.mark.parametrize('text',['n0ob','l0ser','nooob','loooser','sh1t','f.u.c.k','f*ck','d.m','djt','vkl','NPC','cringe af','fake artist'])
def test_new_and_existing_forms_have_traceable_spans(text):
    found=detect(text)['lexical_signals'];assert found
    for s in found:
        assert text[s['start']:s['end']]==s['matched_form']
        assert s['source_ids'] and s['canonical_form']

@pytest.mark.parametrize('text',['dm@example.com','https://dm.com/path','dm.com','admin','my_n0ob_account','n0ob123'])
def test_boundaries_protect_domains_ids_and_words(text):
    assert detect(text)['lexical_signals']==[]

def test_neutral_npc_has_no_automatic_review():
    result=detect('NPC trong game đang đứng cạnh cửa.')
    assert result['ambiguous_only'] and not result['directed_insult_candidate']
    assert not result['lexical_review_recommended']

def test_reported_fake_artist_is_not_directed():
    assert not detect('Mình trích dẫn “fake artist” để báo cáo.')['directed_insult_candidate']
