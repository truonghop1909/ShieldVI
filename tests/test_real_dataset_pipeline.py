"""Unit-only fabricated transport responses in tmp_path; never production dataset records."""
import copy,csv,hashlib,io,json,sys,urllib.error
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from real_dataset.core import Pseudonymizer,RealThread,extract_threads,structural_quality,visible_text,pii_hits,atomic_json,sha_file
from real_dataset.http_client import ApiClient,CollectionBlocked,validate_contact
from real_dataset.collector import collect
from real_dataset.store import ReviewStore,RevisionConflict
from real_dataset.review_app import create_app

def source_response(n=10,topic='unit',host='vi.wikipedia.org'):
    root={'id':'h-'+topic,'type':'heading','html':'<h2>Chủ đề thử cấu trúc</h2>','replies':[]};children=root['replies']
    for i in range(n):
        unique=hashlib.sha256((host+topic+str(i)).encode()).hexdigest()
        node={'id':'c-'+topic+'-'+str(i),'type':'comment','author':'UnitAuthor'+str(i%2),'timestamp':f'2020-01-01T00:{i:02d}:00Z',
          'html':'<p>Mình có ý kiến và không thay đổi nguyên văn, khum ko n0ob 🧡 '+unique+'</p>','replies':[]}
        children.append(node);children=node['replies']
    return {'discussiontoolspageinfo':{'threaditemshtml':[root]}}
def thread(tmp_path,n=3):
    p=Pseudonymizer(tmp_path,key=b'x'*32)
    return extract_threads(source_response(n),{'pageid':1,'lastrevid':10},'vi.wikipedia.org',p,'0'*64)[0]
def corpus(tmp_path,n=3):
    t=thread(tmp_path,n);receipt=tmp_path/'raw/cache/unit_source.json';atomic_json(receipt,source_response(n));t['source_response_sha256']=sha_file(receipt);atomic_json(tmp_path/'threads'/(t['thread_id']+'.json'),t);atomic_json(tmp_path/'manifests/sources.json',{'vi.wikipedia.org':{'status':'ALLOWED'}});return t

def payload(t,index=0,**extra):
    return {'thread_id':t['thread_id'],'comment_id':t['comments'][index]['comment_id'],'reviewer_id':'solo','review_round':1,'expected_revision':0,**extra}

def test_source_tree_time_and_full_text_preserved(tmp_path):
    t=thread(tmp_path)
    assert t['data_origin']=='real' and len(t['comments'])==3
    assert t['comments'][1]['parent_id']==t['comments'][0]['comment_id']
    assert t['comments'][1]['timestamp']=='2020-01-01T00:01:00Z'
    assert 'khum ko n0ob 🧡' in t['comments'][1]['text']
    assert not t['training_eligible'] and not t['evaluation_eligible']

def test_pseudonyms_consistent_and_pii_removed(tmp_path):
    p=Pseudonymizer(tmp_path,key=b'x'*32)
    a=p.user('vi.wikipedia.org','UnitAuthor')
    assert a==p.user('vi.wikipedia.org','UnitAuthor')
    assert a!=p.user('vi.wiktionary.org','UnitAuthor')
    value,changes=p.redact('UnitAuthor: test@example.org 0901234567 192.0.2.3 khum ko 🧡','vi.wikipedia.org',['UnitAuthor'])
    assert a in value and 'khum ko 🧡' in value and not pii_hits(value)
    assert 'example.org' not in value and changes['source_identity']==1

def test_missing_pseudonym_key_cannot_silently_change_existing_users(tmp_path):
    corpus(tmp_path)
    with pytest.raises(ValueError,match='key missing'):Pseudonymizer(tmp_path)

@pytest.mark.parametrize('kind',['parent','cycle','ids','timestamp'])
def test_invalid_structure_rejected_without_repairs(tmp_path,kind):
    t=thread(tmp_path)
    if kind=='parent':t['comments'][1]['parent_id']='missing'
    elif kind=='cycle':t['comments'][0]['parent_id']=t['comments'][2]['comment_id']
    elif kind=='ids':t['comments'][1]['comment_id']=t['comments'][0]['comment_id']
    else:t['comments'][0]['timestamp']='2020-01-01T00:00:00'
    with pytest.raises(ValueError):RealThread.model_validate(t)

def test_missing_time_not_invented(tmp_path):
    t=thread(tmp_path);t['comments'][0]['timestamp']=None;t['comments'][0]['timestamp_origin']='missing_from_source'
    RealThread.model_validate(t)
    assert 'missing_source_timestamp' in structural_quality(t)['warnings']

def test_html_extraction_does_not_execute_scripts_or_rewrite_slang():
    assert visible_text('<p>khum  ko 🧡 f*ck</p><script>bad()</script>')=='khum  ko 🧡 f*ck'

def test_http_retry_budget_rate_limit_and_cache(tmp_path):
    calls=[];waits=[];time=[0.]
    def sleep(s):waits.append(s);time[0]+=s
    def transport(url):
        calls.append(url)
        if len(calls)<3:raise urllib.error.HTTPError(url,429,'rate',{'Retry-After':'2'},None)
        return {'batchcomplete':True}
    c=ApiClient('vi.wikipedia.org',tmp_path,'UnitTest/1',interval=1,retries=3,transport=transport,sleep=sleep,clock=lambda:time[0])
    one,h=c.get({'action':'query','meta':'siteinfo'});two,j=c.get({'action':'query','meta':'siteinfo'})
    assert one==two and h==j and len(calls)==3 and waits
    with pytest.raises(ValueError):c.get({'action':'edit'})

def test_exhausted_retry_is_finite(tmp_path):
    calls=[]
    def bad(url):calls.append(url);raise urllib.error.URLError('unit offline')
    c=ApiClient('vi.wikipedia.org',tmp_path,'UnitTest',transport=bad,retries=2,sleep=lambda _:None)
    with pytest.raises(CollectionBlocked):c.get({'action':'query'})
    assert len(calls)==2

def test_missing_contact_never_calls_network(tmp_path):
    def forbidden(*args,**kwargs):pytest.fail('No contact must stop before constructing live client')
    result=collect(tmp_path,contact='',client_factory=forbidden)
    assert result['status']=='BLOCKED' and result['threads']==0

class FakeClient:
    content_calls=0
    def __init__(self,host,cache,user_agent,**kwargs):self.host=host;self.requests=0;self.cache=Path(cache)
    def get(self,p):
        self.requests+=1
        def reply(data):
            path=self.cache/(hashlib.sha256((self.host+json.dumps(p,sort_keys=True)).encode()).hexdigest()+'.json');atomic_json(path,data);return data,sha_file(path)
        if p.get('meta')=='siteinfo':return reply({'query':{'rightsinfo':{'url':'https://creativecommons.org/licenses/by-sa/4.0/'}}})
        if p.get('action')=='discussiontoolspageinfo':
            FakeClient.content_calls+=1
            roots=[]
            for i in range(15):roots+=source_response(10,self.host+str(p['oldid'])+'_'+str(i),self.host)['discussiontoolspageinfo']['threaditemshtml']
            return reply({'discussiontoolspageinfo':{'threaditemshtml':roots}})
        return reply({'query':{'pages':[{'pageid':11,'lastrevid':12,'title':'Project:Unit','ns':4}]}})

def test_collector_batch_resume_stable_ids_without_redownload(tmp_path):
    FakeClient.content_calls=0
    a=collect(tmp_path,contact='unit@university.edu',through_batch=1,client_factory=FakeClient)
    assert a['status']=='COLLECTED' and a['threads']==20
    original={p.name:sha_file(p) for p in (tmp_path/'threads').glob('*.json')};calls=FakeClient.content_calls
    b=collect(tmp_path,contact=None,through_batch=1,client_factory=FakeClient)
    assert b['threads']==20 and FakeClient.content_calls==calls
    assert original=={p.name:sha_file(p) for p in (tmp_path/'threads').glob('*.json')}
    m=json.loads((tmp_path/'batches/batch_01/manifest.json').read_text())
    assert len(m['thread_ids'])==len(set(m['thread_ids']))==20

def test_labels_not_default_clean_and_uncertain_requires_notes(tmp_path):
    t=corpus(tmp_path);s=ReviewStore(tmp_path)
    assert s.list_reviews()==[]
    with pytest.raises(ValueError,match='notes'):s.save(payload(t,label='UNCERTAIN'))
    r=s.save(payload(t,label='UNCERTAIN',reviewer_notes='Cần đọc lại'))
    assert r['label']=='UNCERTAIN' and r['revision']==1

def test_revision_conflict_preserves_label(tmp_path):
    t=corpus(tmp_path);s=ReviewStore(tmp_path);s.save(payload(t,label='CLEAN'))
    with pytest.raises(RevisionConflict):s.save(payload(t,label='TOXIC',change_reason='unit'))
    assert s.list_reviews()[0]['label']=='CLEAN'

def test_same_human_two_rounds_history_and_round1_revision(tmp_path):
    t=corpus(tmp_path);s=ReviewStore(tmp_path);r=s.save(payload(t,label='CLEAN',annotation_status='ROUND1_DONE'))
    with pytest.raises(ValueError):s.save(payload(t,reviewer_id='different',review_round=2,round1_revision=1,label='TOXIC'))
    second=s.save(payload(t,review_round=2,round1_revision=r['revision'],label='TOXIC',annotation_status='ROUND2_DONE',change_reason='Đọc lại có công kích'))
    h=s.history(t['thread_id'],t['comments'][0]['comment_id']);assert h[-1]['previous_label']=='CLEAN' and h[-1]['new_label']=='TOXIC'
    assert h[-1]['review_round']==2 and second['reviewer_id']=='solo'
    s.save(payload(t,expected_revision=1,label='CLEAN',annotation_status='ROUND1_DONE',reviewer_notes='new review'))
    with pytest.raises(RevisionConflict):s.save(payload(t,expected_revision=1,review_round=2,round1_revision=1,label='TOXIC',change_reason='stale'))

def test_round2_queue_and_csv_safe_roundtrip(tmp_path):
    t=corpus(tmp_path);s=ReviewStore(tmp_path);s.save(payload(t,label='CLEAN',reviewer_notes='=1+1',annotation_status='ROUND1_DONE'))
    assert len(s.round2_queue('solo'))==1
    exported=s.export_csv('solo');assert "'=1+1" in exported
    assert s.import_csv(exported)==1
    assert s.list_reviews()[0]['reviewer_notes']=='=1+1'

def test_csv_import_rollback_when_any_revision_is_stale(tmp_path):
    t=corpus(tmp_path);s=ReviewStore(tmp_path);s.save(payload(t,label='CLEAN'));s.save(payload(t,1,label='CLEAN'))
    stream=io.StringIO(s.export_csv().lstrip('\ufeff'));rows=list(csv.DictReader(stream));fields=list(rows[0]);rows[0].update(label='TOXIC',change_reason='unit');rows[1]['expected_revision']='0'
    buf=io.StringIO();w=csv.DictWriter(buf,fieldnames=fields);w.writeheader();w.writerows(rows)
    with pytest.raises(RevisionConflict):s.import_csv(buf.getvalue())
    assert all(r['label']=='CLEAN' for r in s.list_reviews())

def test_repeated_attack_requires_same_actor_target_and_real_evidence(tmp_path):
    t=corpus(tmp_path,4);s=ReviewStore(tmp_path);target=t['comments'][1]['user_id']
    s.save(payload(t,0,label='TOXIC',is_directed_attack=True,directed_at_user_id=target))
    current=payload(t,2,label='TOXIC',is_directed_attack=True,directed_at_user_id=target,is_repeated_attack=True,evidence_comment_ids=[t['comments'][0]['comment_id'],t['comments'][2]['comment_id']])
    assert s.save(current)['is_repeated_attack']
    current.update(comment_id=t['comments'][3]['comment_id'],evidence_comment_ids=[t['comments'][0]['comment_id'],t['comments'][3]['comment_id']])
    with pytest.raises(ValueError):s.save(current)

def test_empty_or_unverified_dataset_cannot_be_locked(tmp_path):
    s=ReviewStore(tmp_path)
    with pytest.raises(ValueError):s.lock_evaluation('solo')
    corpus(tmp_path)
    with pytest.raises(ValueError,match='Round 2'):s.lock_evaluation('solo')

def test_loopback_app_blind_session_csrf_and_autosave(tmp_path):
    t=corpus(tmp_path);app=create_app(tmp_path,test_mode=True)
    with TestClient(app) as c:
        session=c.get('/session').json();assert session['blind_review'] and not session['model_predictions_enabled']
        assert c.get('/').status_code==200
        assert c.get('/api/analyze').status_code==404
        assert c.post('/api/reviews',json=payload(t,label='CLEAN')).status_code==403
        h={'X-Review-Token':session['token']}
        assert c.post('/api/reviews',headers=h,json=payload(t,label='CLEAN')).status_code==200
        assert c.post('/api/reviews',headers=h,json=payload(t,label='TOXIC',change_reason='stale')).status_code==409
        assert c.post('/api/reviews',headers={**h,'Origin':'https://untrusted.invalid'},json=payload(t,label='CLEAN')).status_code==403
        assert c.get('/api/threads').json()['counts']['labeled']==1

def test_parent_display_and_full_text_are_not_truncated(tmp_path):
    t=corpus(tmp_path);t['comments'][0]['text']='Đầy đủ '+('văn bản dài 🧡 '*1000);atomic_json(tmp_path/'threads'/(t['thread_id']+'.json'),t)
    with TestClient(create_app(tmp_path,test_mode=True)) as c:
        out=c.get('/api/threads/'+t['thread_id']).json();assert out['comments'][0]['text']==t['comments'][0]['text']
        assert out['comments'][1]['parent_id']==out['comments'][0]['comment_id']

def test_progress_counts_follow_human_save(tmp_path):
    t=corpus(tmp_path);s=ReviewStore(tmp_path)
    s.save(payload(t,label='UNCERTAIN',reviewer_notes='Cần xem lại'))
    progress=json.loads((tmp_path/'manifests/progress.json').read_text(encoding='utf-8'))
    assert progress['annotated_comments']==1 and progress['uncertain_comments']==1

def test_locked_dataset_refuses_further_label_edits(tmp_path):
    t=corpus(tmp_path);s=ReviewStore(tmp_path);atomic_json(tmp_path/'manifests/evaluation_lock.json',{'unit_test_only':True})
    with pytest.raises(RevisionConflict,match='locked'):s.save(payload(t,label='CLEAN'))

def test_license_url_path_does_not_allow_unknown_domain(tmp_path):
    from real_dataset.collector import audited_source
    class Unknown:
        host='vi.wikipedia.org'
        def get(self,p):return {'query':{'rightsinfo':{'url':'https://untrusted.invalid/licenses/by-sa/4.0/'}}},'0'*64
    with pytest.raises(CollectionBlocked):audited_source(Unknown(),tmp_path)
    assert json.loads((tmp_path/'manifests/sources.json').read_text())['vi.wikipedia.org']['status']=='UNKNOWN'

def test_host_header_rebinding_blocked(tmp_path):
    app=create_app(tmp_path,test_mode=True)
    with TestClient(app) as client:assert client.get('/session',headers={'Host':'untrusted.invalid'}).status_code==403

def test_lock_requires_source_receipt_and_human_checks_and_is_immutable(tmp_path):
    t=corpus(tmp_path,2)
    receipt=tmp_path/'raw/cache/unit_source.json';atomic_json(receipt,{'unit_test_mock_transport_only':True})
    t['source_response_sha256']=sha_file(receipt);atomic_json(tmp_path/'threads'/(t['thread_id']+'.json'),t)
    store=ReviewStore(tmp_path)
    for i in range(2):
        first=store.save(payload(t,i,label='CLEAN',annotation_status='ROUND1_DONE'))
        store.save(payload(t,i,review_round=2,round1_revision=first['revision'],label='CLEAN',annotation_status='ROUND2_DONE'))
    with pytest.raises(ValueError,match='review missing'):store.lock_evaluation('solo')
    store.check_thread(t['thread_id'],'solo',True,True,True)
    atomic_json(tmp_path/'manifests/development_exclusions.json',{'audit_completed':True,'thread_ids':[],'long_text_sha256':[],'source_records':[]})
    result=store.lock_evaluation('solo')
    assert result['comments']==2 and result['evaluation_eligible']
    assert 'not inter-annotator' in result['review_protocol']
    export=[json.loads(line) for line in (tmp_path/'annotations/evaluation_export.jsonl').read_text(encoding='utf-8').splitlines()]
    assert all(r['review_status']=='VERIFIED_SOLO' and r['source_type']=='real_anonymized' for r in export)
    with pytest.raises(RevisionConflict):store.import_csv(store.export_csv())

def test_round2_does_not_rewrite_existing_label_without_reason(tmp_path):
    t=corpus(tmp_path);store=ReviewStore(tmp_path);first=store.save(payload(t,label='CLEAN',annotation_status='ROUND1_DONE'))
    with pytest.raises(ValueError,match='reason'):store.save(payload(t,review_round=2,round1_revision=first['revision'],label='TOXIC',annotation_status='ROUND2_DONE'))

def test_a_real_flag_without_source_receipt_is_not_valid_data(tmp_path):
    from real_dataset.validation import validate_dataset
    t=corpus(tmp_path)
    t['source_response_sha256']='0'*64;atomic_json(tmp_path/'threads'/(t['thread_id']+'.json'),t)
    assert any(e['code']=='missing_source_response_receipt' for e in validate_dataset(tmp_path)['errors'])


def test_collector_progress_does_not_reset_human_labels(tmp_path):
    from real_dataset.collector import write_progress
    t=corpus(tmp_path);store=ReviewStore(tmp_path)
    store.save(payload(t,label='UNCERTAIN',reviewer_notes='unit only'))
    progress=write_progress(tmp_path,{})
    assert progress['annotated_comments']==1 and progress['uncertain_comments']==1
    assert progress['unlabeled_comments']==2


def test_lock_quality_detects_changed_export(tmp_path):
    from real_dataset.validation import validate_dataset
    t=corpus(tmp_path,2);store=ReviewStore(tmp_path)
    for i in range(2):
        first=store.save(payload(t,i,label='CLEAN',annotation_status='ROUND1_DONE'))
        store.save(payload(t,i,review_round=2,round1_revision=first['revision'],label='CLEAN',annotation_status='ROUND2_DONE'))
    store.check_thread(t['thread_id'],'solo',True,True,True)
    atomic_json(tmp_path/'manifests/development_exclusions.json',{'audit_completed':True,'thread_ids':[],'long_text_sha256':[],'source_records':[]})
    store.lock_evaluation('solo')
    assert validate_dataset(tmp_path)['independent_evaluation_ready']
    path=tmp_path/'annotations/evaluation_export.jsonl';path.write_text('unit tampering',encoding='utf-8')
    report=validate_dataset(tmp_path)
    assert not report['independent_evaluation_ready']
    assert any(e['code']=='evaluation_snapshot_missing_or_changed' for e in report['errors'])


def test_resume_recovers_missing_completed_batch_manifest_without_network(tmp_path):
    from real_dataset.collector import recover_batch_manifests,collect
    for index in range(20):
        folder=tmp_path/('test_case_'+str(index));thread=corpus(folder,2)
        thread['thread_id']='T_'+format(index,'024x')
        atomic_json(tmp_path/'threads'/(thread['thread_id']+'.json'),thread)
    recover_batch_manifests(tmp_path)
    manifest=json.loads((tmp_path/'batches/batch_01/manifest.json').read_text())
    assert len(manifest['thread_ids'])==20 and len(manifest['checksums'])==20
    assert collect(tmp_path,through_batch=1)['resume'].startswith('target already present')


def test_repeated_attack_with_unknown_source_time_is_validation_error(tmp_path):
    t=corpus(tmp_path);t['comments'][2].update(timestamp=None,timestamp_origin='missing_from_source')
    atomic_json(tmp_path/'threads'/(t['thread_id']+'.json'),t)
    store=ReviewStore(tmp_path)
    with pytest.raises(ValueError,match='timestamp'):
        store.save(payload(t,2,label='TOXIC',is_directed_attack=True,is_repeated_attack=True,directed_at_user_id=t['comments'][1]['user_id'],evidence_comment_ids=[t['comments'][0]['comment_id'],t['comments'][2]['comment_id']]))


def test_existing_supervised_csv_text_cannot_enter_new_evaluation(tmp_path):
    import real_dataset.store as module
    t=corpus(tmp_path,2);store=ReviewStore(tmp_path)
    for i in range(2):
        first=store.save(payload(t,i,label='CLEAN',annotation_status='ROUND1_DONE'))
        store.save(payload(t,i,review_round=2,round1_revision=first['revision'],label='CLEAN',annotation_status='ROUND2_DONE'))
    store.check_thread(t['thread_id'],'solo',True,True,True)
    repo=Path(module.__file__).resolve().parents[2];source=tmp_path/'unit_supervised.csv'
    with source.open('w',encoding='utf-8',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=['Comment']);writer.writeheader();writer.writerow({'Comment':t['comments'][0]['text']})
    atomic_json(tmp_path/'manifests/development_exclusions.json',{'audit_completed':True,'thread_ids':[],'long_text_sha256':[],
      'source_records':[{'path':source.relative_to(repo).as_posix(),'sha256':sha_file(source),'format':'csv','text_field':'Comment'}]})
    with pytest.raises(ValueError,match='text overlap'):store.lock_evaluation('solo')
