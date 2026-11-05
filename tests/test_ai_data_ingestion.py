import copy,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from prepare_ai_update_data import prepare,normalized

def row(thread='a',text='Mình góp ý bố cục',id='c'):
    return {'thread_id':thread,'comment_id':id,'timestamp':'2026-01-01T00:00:00Z','raw_text':text,'parent_id':None,'source_id':'project','source_type':'synthetic','review_status':'NEEDS_REVIEW','human_label':None}

def test_raw_unicode_roundtrip_and_unverified_not_exported(tmp_path):
    text='  Xin lỗi bạn nhé 🧡  ';result=prepare([row(text=text)],tmp_path/'data')
    saved=json.loads((tmp_path/'data/review.jsonl').read_text(encoding='utf-8'))
    assert saved['raw_text']==text and saved['normalized_text']==normalized(text)
    assert result['partition_counts']=={'train':0,'validation':0,'test':0}

def test_idempotent_does_not_overwrite_review_edits(tmp_path):
    out=tmp_path/'d';a=prepare([row()],out);prepare([row()],out)
    with pytest.raises(FileExistsError):prepare([row(text='changed')],out)

def test_duplicate_threads_never_leak_between_partitions(tmp_path):
    rows=[dict(row(t),human_label='CLEAN',review_status='VERIFIED_SOLO',approved_for_training=True,license_approved=True) for t in ('a','b')]
    result=prepare(rows,tmp_path/'d')
    allrows=[json.loads(line) for p in (tmp_path/'d').glob('*.jsonl') if p.stem in ('train','test','validation') for line in p.read_text(encoding='utf-8').splitlines()]
    assert len(allrows)==1
    review=[json.loads(line) for line in (tmp_path/'d/review.jsonl').read_text(encoding='utf-8').splitlines()]
    assert review[0]['leakage_group']==review[1]['leakage_group']

def test_regression_never_becomes_training_even_with_verified_labels(tmp_path):
    x=dict(row(),split='development_regression',human_label='TOXIC',review_status='VERIFIED_SOLO',approved_for_training=True,license_approved=True)
    assert sum(prepare([x],tmp_path/'d')['partition_counts'].values())==0

def test_invalid_parent_rejects_thread_without_silent_loss(tmp_path):
    x=row();x['parent_id']='missing';m=prepare([x],tmp_path/'d')
    assert m['rejected_count']==1 and m['input_count']==m['rejected_count']+m['review_count']

def test_conflicting_verified_labels_not_exported(tmp_path):
    a=dict(row('a'),human_label='CLEAN',review_status='VERIFIED_SOLO',approved_for_training=True,license_approved=True)
    b=dict(a,thread_id='b',human_label='TOXIC')
    m=prepare([a,b],tmp_path/'d');assert m['conflicting_verified_texts']==1 and sum(m['partition_counts'].values())==0

def test_parent_time_compares_actual_timezone_instants(tmp_path):
    parent=row(id='parent');parent['timestamp']='2026-01-01T01:00:00+00:00'
    child=row(id='child');child.update(parent_id='parent',timestamp='2026-01-01T02:00:00+07:00')
    result=prepare([parent,child],tmp_path/'d')
    assert result['review_count']==0 and result['rejected_count']==2
