"""Human synthetic review overlay: temporary copies only; never labels production data."""
import copy,csv,io,json,sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from synthetic_data.pipeline import DATA
from synthetic_data.review_app import create_app
from synthetic_data.review_store import SyntheticReviewStore
from real_dataset.core import atomic_json,sha_file
from real_dataset.store import RevisionConflict

@pytest.fixture
def dataset(tmp_path):
    source=DATA/'threads/SYN200_0001.json';target=tmp_path/'threads'/source.name
    target.parent.mkdir();target.write_bytes(source.read_bytes())
    atomic_json(tmp_path/'manifest.json',{'actual_threads':1,'data_origin':'synthetic','thread_checksums':{'SYN200_0001':sha_file(target)}})
    return tmp_path

def payload(store,index=0,**extra):
    t=next(iter(store.corpus().values()));c=t['comments'][index]
    annotation={k:v for k,v in c['annotation'].items() if k not in ('label_reason','label_source')}
    return {'thread_id':t['thread_id'],'comment_id':c['comment_id'],'reviewer_id':'solo',
      'review_round':1,'expected_revision':0,'source_sha256':t['source_sha256'],**annotation,**extra}

def test_ai_references_never_count_as_human_reviews(dataset):
    store=SyntheticReviewStore(dataset);summary=store.summaries('solo')
    assert summary['counts']['labeled']==0 and summary['counts']['comments']==12
    assert summary['items'][0]['label_counts']['TOXIC']==2
    assert not store.list_reviews()
    with pytest.raises(ValueError,match='Chưa có'):store.reviewed_records('solo')

def test_drafts_are_persistent_but_not_exported_as_confirmed(dataset):
    store=SyntheticReviewStore(dataset);store.save(payload(store))
    reopened=SyntheticReviewStore(dataset)
    assert len(reopened.list_reviews())==1 and reopened.summaries('solo')['counts']['labeled']==0
    with pytest.raises(ValueError):reopened.reviewed_records('solo')

def test_confirmation_exports_human_overlay_without_changing_source(dataset):
    before={p.name:sha_file(p) for p in (dataset/'threads').glob('*.json')};manifest=sha_file(dataset/'manifest.json')
    store=SyntheticReviewStore(dataset);store.save(payload(store,annotation_status='ROUND1_DONE'))
    record=store.reviewed_records('solo')[0]
    assert record['data_origin']=='synthetic' and not record['human_gold'] and not record['evaluation_eligible']
    assert record['synthetic_annotation']['label_source']=='synthetic'
    assert record['annotation']['label_source']=='human_reviewed_synthetic' and record['ai_assisted_review']
    assert not store.summaries('someone_else')['counts']['labeled']
    assert before=={p.name:sha_file(p) for p in (dataset/'threads').glob('*.json')}
    assert sha_file(dataset/'manifest.json')==manifest
    assert (dataset/'human_review/annotations/reviews.sqlite3').exists()

def test_changing_ai_label_or_metadata_requires_reason(dataset):
    store=SyntheticReviewStore(dataset)
    with pytest.raises(ValueError,match='lý do'):store.save(payload(store,label='TOXIC',is_directed_attack=True))
    with pytest.raises(ValueError,match='lý do'):store.save(payload(store,category='other'))
    row=store.save(payload(store,label='UNCERTAIN',category='ambiguous',is_directed_attack=None,
      reviewer_notes='Cần đọc thêm ngữ cảnh.',change_reason='Mình chưa chắc thái độ của phát ngôn.',annotation_status='ROUND1_DONE'))
    assert row['label']=='UNCERTAIN' and not store.reviewed_records('solo')[0]['binary_training_candidate']

def test_uncertain_requires_human_notes_and_clean_cannot_keep_attack(dataset):
    store=SyntheticReviewStore(dataset)
    with pytest.raises(ValueError,match='notes'):store.save(payload(store,label='UNCERTAIN',change_reason='Thiếu ngữ cảnh.'))
    with pytest.raises(ValueError,match='CLEAN'):store.save(payload(store,5,label='CLEAN',change_reason='Kiểm lại phát ngôn.'))

def test_repeated_needs_earlier_human_evidence_not_ai_reference(dataset):
    store=SyntheticReviewStore(dataset)
    with pytest.raises(ValueError,match='human-labeled'):store.save(payload(store,9,annotation_status='ROUND1_DONE'))
    store.save(payload(store,5,annotation_status='ROUND1_DONE'))
    store.save(payload(store,9,annotation_status='ROUND1_DONE'))
    assert store.reviewed_records('solo')[-1]['annotation']['is_repeated_attack']

def test_stale_revision_and_source_checksum_never_overwrite_review(dataset):
    store=SyntheticReviewStore(dataset);p=payload(store,annotation_status='ROUND1_DONE');store.save(p)
    with pytest.raises(RevisionConflict):store.save(p)
    p=payload(store,1);p['source_sha256']='0'*64
    with pytest.raises(RevisionConflict):store.save(p)
    assert len(store.list_reviews())==1

def test_source_file_tampering_is_detected(dataset):
    store=SyntheticReviewStore(dataset);store.corpus()
    path=dataset/'threads/SYN200_0001.json';t=json.loads(path.read_text(encoding='utf-8'));t['comments'][0]['text']='Changed unit text'
    atomic_json(path,t)
    with pytest.raises(RevisionConflict,match='checksum'):store.corpus()

def test_second_round_uses_same_reviewer_and_round1_revision(dataset):
    store=SyntheticReviewStore(dataset);first=store.save(payload(store,annotation_status='ROUND1_DONE'))
    with pytest.raises(ValueError):store.save(payload(store,review_round=2,reviewer_id='other',round1_revision=first['revision']))
    second=store.save(payload(store,review_round=2,round1_revision=first['revision'],annotation_status='ROUND2_DONE'))
    assert second['review_round']==2 and store.reviewed_records('solo')[0]['annotation']['review_round']==2
    history=store.history(first['thread_id'],first['comment_id']);assert len(history)==2

def test_csv_roundtrip_and_atomic_revision_guard(dataset):
    store=SyntheticReviewStore(dataset);store.save(payload(store,annotation_status='ROUND1_DONE'))
    text=store.export_csv('solo');assert 'source_sha256' in text
    assert store.import_csv(text)==1
    records=list(csv.DictReader(io.StringIO(text.lstrip('\ufeff'))));records[0]['expected_revision']='0'
    buffer=io.StringIO();writer=csv.DictWriter(buffer,fieldnames=records[0]);writer.writeheader();writer.writerows(records)
    with pytest.raises(RevisionConflict):store.import_csv(buffer.getvalue())
    assert len(store.reviewed_records('solo'))==1

def test_loopback_api_shows_references_filters_and_exports_only_confirmed(dataset):
    app=create_app(dataset,test_mode=True)
    with TestClient(app) as client:
        session=client.get('/session').json();assert not session['blind_review'] and session['ai_reference_labels_visible']
        assert not session['model_predictions_enabled']
        thread=client.get('/api/threads/SYN200_0001').json();assert thread['comments'][5]['annotation']['label']=='TOXIC'
        assert client.get('/api/threads?reviewer_id=solo').json()['counts']['labeled']==0
        p=payload(app.state.store,annotation_status='ROUND1_DONE')
        assert client.post('/api/reviews',json=p).status_code==403
        headers={'X-Review-Token':session['token']}
        assert client.post('/api/reviews',headers={**headers,'Origin':'https://wrong.invalid'},json=p).status_code==403
        assert client.post('/api/reviews',headers=headers,json=p).status_code==200
        export=client.get('/api/reviewed.jsonl?reviewer_id=solo');assert export.status_code==200
        assert json.loads(export.text.strip())['annotation']['reviewer_id']=='solo'
        assert client.get('/api/reviewed.jsonl?reviewer_id=other').status_code==422
        assert client.post('/api/lock',headers=headers,json={'reviewer_id':'solo'}).status_code==409
        assert client.get('/api/analyze').status_code==404


def test_repeated_cannot_promote_unconfirmed_ai_seed_draft(dataset):
    store=SyntheticReviewStore(dataset)
    first=store.save(payload(store,5))
    with pytest.raises(ValueError,match='bản nháp'):
        store.save(payload(store,9,annotation_status='ROUND1_DONE'))
    store.save(payload(store,5,expected_revision=first['revision'],annotation_status='ROUND1_DONE'))
    store.save(payload(store,9,annotation_status='ROUND1_DONE'))
    assert len(store.reviewed_records('solo'))==2
