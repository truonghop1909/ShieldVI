from app.lexical import detect


def test_english_obfuscations():
    for text in ['f.u.c.k you', 'f*ck this', 'f**k you', 'sh1t', 'you are an idiot', 'b1tch']:
        assert detect(text)['lexical_review_recommended'], text


def test_vietnamese_slang_obfuscations():
    for text in ['đ.m mày', 'địt mẹ mày', 'đ.ị.t m.ẹ mày', 'đéo hiểu', 'óc chó', 'vcl', 'dcm', 'não tàn']:
        assert detect(text)['lexical_review_recommended'], text


def test_profane_exclamation_is_not_always_targeted():
    result = detect('Đm tai nghe của tao hết pin rồi')
    assert result['profanity_detected']
    assert not result['directed_insult_candidate']


def test_normally_polite_and_apology():
    for text in ['Mình không hợp giọng hát đó lắm', 'Thôi tao dừng phần cãi nhau ở đây', 'Mình thích xe này']:
        assert not detect(text)['lexical_review_recommended'], text
    apology = detect('Đừng chửi người ta là óc chó nữa')
    assert apology['reported_or_apology_context']
    assert not apology['directed_insult_candidate']


def test_ambiguous_abbreviation_not_automatic_label():
    value = detect('cc')
    assert value['ambiguous_only']
    assert not value['lexical_review_recommended']


def test_no_automatic_toxic_label(client):
    payload = {'thread_id':'LEXICAL','comments':[
        {'comment_id':'a','user_id':'u1','text':'Mới mua laptop', 'timestamp':'2026-10-10T10:00:00Z'},
        {'comment_id':'b','user_id':'u2','parent_id':'a','text':'Đm máy hết pin mất rồi', 'timestamp':'2026-10-10T10:01:00Z'},
        {'comment_id':'c','user_id':'u2','parent_id':'a','text':'f.u.c.k you', 'timestamp':'2026-10-10T10:02:00Z'},
    ]}
    resp=client.post('/api/analyze',json=payload)
    assert resp.status_code==200,resp.text
    result=resp.json()
    assert result['suspected_repeated_harassment'] is False
    assert result['comments'][1]['profanity_detected']
    assert result['comments'][2]['lexical_review_recommended']
    assert not result['comments'][2]['toxic_for_moderation']


def test_sqlite_reviews_endpoints(client, monkeypatch, tmp_path):
    monkeypatch.setenv('REVIEW_DB_PATH',str(tmp_path/'review.sqlite'))
    payload={'thread_id':'T001','reviewer_id':'A','items':[
        {'comment_id':'c1','human_label':'clean','ai_label':'toxic','toxicity_score':0.85,'lexical_flag':False},
        {'comment_id':'c2','human_label':'toxic','ai_label':'clean','toxicity_score':0.12,'lexical_flag':True},
        {'comment_id':'c3','human_label':'uncertain','ai_label':'toxic','toxicity_score':0.90}
    ]}
    r=client.post('/api/reviews/batch',json=payload)
    assert r.status_code==200,r.text
    assert r.json()['saved']==3
    data=client.get('/api/reviews?thread_id=T001&reviewer_id=A').json()
    assert len(data['items'])==3
    stats=client.get('/api/reviews/stats').json()
    assert (stats['false_positive'],stats['false_negative'],stats['uncertain'])==(1,1,1)
    payload['items']=[{'comment_id':'c1','human_label':'toxic','ai_label':'toxic','toxicity_score':0.85}]
    assert client.post('/api/reviews/batch',json=payload).status_code==200
    assert client.get('/api/reviews/stats').json()['false_positive']==0
    export=client.get('/api/reviews/export')
    assert export.status_code==200
    assert 'T001' in export.text
    assert 'c2' in export.text
    assert 'nội dung' not in export.text


def test_validation_rejects_bad_review(client):
    assert client.post('/api/reviews/batch',json={
        'thread_id':'t','reviewer_id':'A','items':[{'comment_id':'c',
        'human_label':'toxic','ai_label':'clean','toxicity_score':1.5}]}).status_code==422
