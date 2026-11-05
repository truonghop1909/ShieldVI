import json,hashlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from test_live_api import live
from shieldvi_social.studio_routes import router,DatasetStore,ImportInput
from ml_studio.datasets import safe_csv,ROOT
from real_dataset.core import atomic_json,comparison

def sample(**changes):
    row={'thread_id':'STUDIO_DEMO_100','comment_id':'c1','parent_id':None,'user_id':'ParticipantA','timestamp':'2026-11-04T00:00:00Z','text':'Bản thông báo đăng ký ngày hội làm vườn của nhóm mình đã được cập nhật lịch mới.','label':'CLEAN'}
    row.update(changes);return row
def payload(rows=None,**changes):
    result={'content':json.dumps(rows or [sample()],ensure_ascii=False),'format':'json','dataset_type':'SYNTHETIC','data_origin':'synthetic'};result.update(changes);return result
@pytest.fixture
def studio(live,tmp_path):
    manifest=tmp_path/'exclusions.json';atomic_json(manifest,{'audit_completed':True,'thread_ids':['EXCLUDED_SAMPLE'],'source_records':[]})
    store=DatasetStore.initialize(tmp_path/'studio',manifest)
    live[0].app.state.studio=store;live[0].app.include_router(router)
    return live,store
def upload(studio,value=None,headers=None):
    live,_=studio;return live[0].post('/api/studio/datasets',headers=headers or live[3],json=value or payload())

def test_admin_required_no_upload_or_export_for_users(studio):
    live,store=studio
    assert upload(studio,headers=live[1]).status_code==403
    assert not store.list()
    assert live[0].get('/api/studio/datasets',headers=live[2]).status_code==403

def test_import_immutable_hashes_pseudonyms_split_and_deduplication(studio):
    first=upload(studio);assert first.status_code==201;value=first.json();assert value['status']=='ACCEPTED' and value['report']['training_eligible']
    assert value['manifest']['not_human_gold'] and value['manifest']['label_source']=='synthetic_reference'
    rows=studio[1].rows(value['id']);assert rows[0]['user_id'].startswith('U_') and rows[0]['user_id']!='ParticipantA'
    assert upload(studio).json()['replayed'] and len(studio[1].list())==1
    path=studio[1].root/'versions'/value['id']/'comments.jsonl';path.write_text('[]',encoding='utf-8')
    with pytest.raises(ValueError,match='changed'):studio[1].rows(value['id'])

@pytest.mark.parametrize('row,code',[(sample(label='BAD'),'INVALID_SCHEMA'),(sample(label=True),'INVALID_LABEL_TYPE'),(sample(parent_id='missing'),'PARENT_MISSING_FUTURE_OR_CYCLE'),(sample(text='  '),'EMPTY_TEXT'),(sample(target_user_id='Unknown'),'INVALID_TARGET')])
def test_invalid_rows_rejected_with_codes(studio,row,code):
    value=upload(studio,payload([row])).json();assert value['status']=='REJECTED';assert code in {e['code'] for e in value['report']['errors']}

def test_pii_formula_rights_and_development_overlap_quarantined(studio):
    for row,changes,code in [(sample(text='Liên hệ demo.person@example.org để tham gia.'),{},'PII_REQUIRES_REDACTION'),(sample(text='=HYPERLINK("https://example.org")'),{},'CSV_FORMULA_RISK'),(sample(thread_id='EXCLUDED_SAMPLE'),{},'DEVELOPMENT_OR_PRIOR_SPLIT_OVERLAP'),(sample(thread_id='RIGHTS_PENDING'),{'data_origin':'real'},'REAL_SOURCE_RIGHTS_REQUIRE_MANUAL_VERIFICATION')]:
        value=upload(studio,payload([row],**changes)).json();assert value['status']=='QUARANTINED' and not value['report']['training_eligible'];assert code in {e['code'] for e in value['report']['quarantine']}

def test_csv_mapping_label_vocabulary_and_safe_export(studio):
    text='body,y,thread_id,comment_id,user_id,timestamp\nCùng xem lịch sự kiện mới nhé,0,CSV_DEMO,c1,A,2026-11-04T00:00:00Z\n'
    value=upload(studio,payload(content=text,format='csv',mapping={'text':'body','label':'y'})).json();assert value['status']=='ACCEPTED'
    c,_,_,staff,_,_=studio[0];assert 'CLEAN' in c.get('/api/studio/datasets/'+value['id']+'/export?format=csv',headers=staff).text
    assert "'=1+1" in safe_csv([{'text':'=1+1'}])
    assert upload(studio,payload(content='broken,header\n1,2',format='csv')).json()['status']=='REJECTED'

def test_duplicate_and_thread_grouped_split(studio):
    a=sample();b=sample(comment_id='c2',parent_id='c1',timestamp='2026-11-04T00:01:00Z')
    value=upload(studio,payload([a,b])).json();assert value['status']=='ACCEPTED' and not value['report']['training_eligible'];assert value['report']['warnings'][0]['code']=='EXACT_DUPLICATE'
    assert len({r['split'] for r in studio[1].rows(value['id'])})==1
    assert upload(studio,payload([a,a])).json()['status']=='REJECTED'

def test_bounded_input_unsupported_archive_and_invalid_json(studio):
    assert upload(studio,payload(content='x'*1048577)).status_code==422
    assert upload(studio,payload(content='x'*2097153)).status_code==413
    assert upload(studio,payload(format='zip')).status_code==422
    assert upload(studio,payload(content='{')).json()['status']=='REJECTED'
    assert upload(studio,payload(content=json.dumps([sample(text='Nội dung dài '*2000)]))).json()['status']=='REJECTED'

def test_concurrent_upload_same_version_and_explicit_lineage(studio):
    with ThreadPoolExecutor(max_workers=2) as pool:values=list(pool.map(lambda _:upload(studio).json(),range(2)))
    assert values[0]['id']==values[1]['id'] and len(studio[1].list())==1
    assert upload(studio,payload(provenance={'note':'changed metadata'})).status_code==422
    value=upload(studio,payload(provenance={'note':'changed metadata'},parent_version=values[0]['id'])).json();assert value['manifest']['parent_version']==values[0]['id']

def test_upload_boundary_allows_legal_file_larger_than_original_auth_limit(studio):
    rows=[sample(comment_id=f'c{i}',thread_id=f'BOUNDARY_{i}',text=f'Thông báo số {i}: Mời đọc lịch và nội dung công việc nhóm cho tuần mới.') for i in range(100)]
    value=upload(studio,payload(rows));assert value.status_code==201 and value.json()['report']['comments']==100

def test_pinned_source_near_overlap_and_source_mutation_fail_closed(tmp_path):
    source=tmp_path/'development.json';text='Câu chuyện về khu vườn ban công được kể chi tiết trong buổi họp chuẩn bị triển lãm vào tháng mười một.'
    atomic_json(source,{'thread_id':'DEV_PINNED','comments':[{'text':text}]})
    manifest=tmp_path/'near_manifest.json';atomic_json(manifest,{'audit_completed':True,'source_records':[{'path':source.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'format':'thread_json'}]})
    store=DatasetStore.initialize(tmp_path/'near_studio',manifest)
    result=store.import_dataset(payload([sample(text=text+'!')]),'test-admin')
    assert result['status']=='QUARANTINED' and any(r['code']=='NEAR_DEVELOPMENT_COMMENT_OVERLAP' for r in result['report']['quarantine'])
    source.write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError,match='missing/changed'):DatasetStore(store.root)
