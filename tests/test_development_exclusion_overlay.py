import hashlib,json
import pytest
from scripts.check_development_exclusions import check

def fixture(tmp_path):
    thread={'thread_id':'seen_synthetic','comments':[{'comment_id':'a','text':'Đây là lời bình luận tổng hợp phục vụ phát triển và kiểm thử hệ thống. '*3}]}
    path=tmp_path/'thread.json';path.write_text(json.dumps(thread),encoding='utf-8')
    manifest=tmp_path/'exclusions.json';manifest.write_text(json.dumps({'audit_completed':True,'thread_ids':['seen_synthetic'],
        'source_records':[{'path':'thread.json','format':'thread_json','sha256':hashlib.sha256(path.read_bytes()).hexdigest()}]}),encoding='utf-8')
    return thread,path,manifest

def test_versioned_overlay_blocks_same_thread_and_renamed_long_text(tmp_path):
    thread,_,manifest=fixture(tmp_path)
    assert check(manifest,thread,tmp_path)['status']=='EXCLUDED_DEVELOPMENT'
    thread['thread_id']='renamed'
    result=check(manifest,thread,tmp_path)
    assert result['matching_long_comment_ids']==['a'] and result['status']=='EXCLUDED_DEVELOPMENT'

def test_overlay_rejects_changed_development_source(tmp_path):
    thread,path,manifest=fixture(tmp_path);path.write_text('{}',encoding='utf-8')
    with pytest.raises(ValueError,match='missing/changed'):check(manifest,thread,tmp_path)

def test_overlay_no_match_does_not_approve_independent_evaluation(tmp_path):
    _,_,manifest=fixture(tmp_path)
    result=check(manifest,{'thread_id':'other','comments':[{'comment_id':'b','text':'Câu khác.'}]},tmp_path)
    assert result['status']=='NOT_MATCHED_BY_THIS_GUARD' and not result['independent_evaluation_approved']
