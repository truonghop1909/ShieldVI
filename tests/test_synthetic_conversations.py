"""Behavior/negative tests; temporary data only, no original models or held-out edits."""
import copy,csv,io,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from synthetic_data.pipeline import Thread,compile_thread,generate,read_catalogue,validate,export_csv,file_sha,DATA

def example():return compile_thread(read_catalogue()[0])

def test_authored_pilot_distinguishes_speech_acts():
 threads=[compile_thread(s) for s in read_catalogue()[:10]]
 assert threads[0]['comments'][3]['annotation']['label']=='CLEAN'
 assert threads[5]['comments'][3]['annotation']['is_quote']
 assert threads[6]['comments'][3]['annotation']['category']=='defense'
 mixed=threads[8]['comments'][8]['annotation']
 assert mixed['is_apology'] and mixed['label']=='TOXIC'
 assert all(not t['human_gold'] and not t['evaluation_eligible'] for t in threads)

@pytest.mark.parametrize('kind',['future_parent','cycle','naive_time','backwards_time','self_target','foreign_id','two_users'])
def test_corrupt_thread_is_rejected(kind):
 t=example();c=t['comments']
 if kind=='future_parent':c[0]['parent_id']=c[1]['comment_id']
 elif kind=='cycle':c[0]['parent_id']=c[-1]['comment_id'];c[-1]['parent_id']=c[0]['comment_id']
 elif kind=='naive_time':c[0]['timestamp']='2025-01-01T00:00:00'
 elif kind=='backwards_time':c[-1]['timestamp']=c[0]['timestamp']
 elif kind=='self_target':c[5]['annotation']['directed_at_user_id']=c[5]['user_id']
 elif kind=='foreign_id':c[0]['comment_id']='other_thread_C01'
 else:
  for row in c:
   if row['user_id'] not in {c[0]['user_id'],c[1]['user_id']}:row['user_id']=c[0]['user_id']
 with pytest.raises(ValueError):Thread.model_validate(t)

def test_repeated_requires_matching_earlier_actor_and_target():
 spec=copy.deepcopy(read_catalogue()[0]);spec['rows'][9][0]='D'
 with pytest.raises(ValueError,match='Repeated evidence'):compile_thread(spec)
 t=example();t['comments'][9]['annotation']['evidence_comment_ids']=[t['comments'][9]['comment_id']]
 with pytest.raises(ValueError,match='Repeated evidence'):Thread.model_validate(t)

def test_repeated_evidence_survives_intervening_apology_but_is_not_invented():
 t=compile_thread(read_catalogue()[100]);row=t['comments'][14]
 assert row['annotation']['is_repeated_attack']
 assert t['comments'][9]['annotation']['category']=='apology'
 assert row['annotation']['evidence_comment_ids']==[t['comments'][4]['comment_id'],row['comment_id']]

def test_uncertain_needs_specific_authored_reason():
 spec=copy.deepcopy(read_catalogue()[1]);spec['rows'][4]=spec['rows'][4][:5]
 with pytest.raises(ValueError,match='specific reason'):compile_thread(spec)

def test_exact_and_near_duplicates_are_detected():
 t=example();t['comments'][1]['text']=t['comments'][0]['text']
 assert any(e['code']=='duplicate_comment_text' for e in validate([t])['errors'])
 t=example();t['comments'][0]['text']='Một bình luận dài dùng để kiểm tra phát hiện gần trùng, cần nhận ra dù khác một dấu chấm.'
 t['comments'][1]['text']=t['comments'][0]['text'][:-1]+'!'
 assert validate([t])['near_duplicate_comments']>=1

def test_csv_roundtrip_keeps_unicode_ids_nulls_and_reference_labels(tmp_path):
 t=example();export_csv([t],tmp_path)
 with (tmp_path/'comments.csv').open(encoding='utf-8-sig',newline='') as stream:comments=list(csv.DictReader(stream))
 with (tmp_path/'annotations.csv').open(encoding='utf-8-sig',newline='') as stream:annotations=list(csv.DictReader(stream))
 assert len(comments)==len(annotations)==len(t['comments'])
 assert comments[0]['text']==t['comments'][0]['text'] and comments[0]['parent_id']==''
 assert {r['comment_id'] for r in comments}=={r['comment_id'] for r in annotations}
 assert all(r['label_source']=='synthetic' for r in annotations)
 assert json.loads(annotations[9]['evidence_comment_ids'])==t['comments'][9]['annotation']['evidence_comment_ids']

def test_resume_is_idempotent_and_refuses_overwriting_edited_threads(tmp_path):
 report=generate(10,tmp_path,track_progress=False)
 original={p.name:file_sha(p) for p in (tmp_path/'threads').glob('*.json')}
 assert generate(10,tmp_path,track_progress=False)==report
 assert original=={p.name:file_sha(p) for p in (tmp_path/'threads').glob('*.json')}
 path=tmp_path/'threads/SYN200_0001.json';data=json.loads(path.read_text(encoding='utf-8'));data['comments'][0]['text']='Edited temporary review text'
 path.write_text(json.dumps(data),encoding='utf-8')
 with pytest.raises(ValueError,match='refuse overwrite'):generate(10,tmp_path,track_progress=False)
 assert json.loads(path.read_text())['comments'][0]['text']=='Edited temporary review text'

def test_completed_batch_resume_preserves_snapshot(tmp_path):
 generate(50,tmp_path,track_progress=False)
 manifest=tmp_path/'batches/batch_01.json';sha=file_sha(manifest)
 generate(50,tmp_path,track_progress=False)
 assert file_sha(manifest)==sha

def test_production_synthetic_dataset_is_complete_and_separate():
 manifest=json.loads((DATA/'manifest.json').read_text(encoding='utf-8'))
 threads=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((DATA/'threads').glob('*.json'))]
 report=validate(threads)
 assert report['threads']==200 and report['comments']==2048 and report['status']=='PASS'
 assert set(report['labels'])=={'CLEAN','TOXIC','UNCERTAIN'}
 assert len(report['topics'])==10 and set(report['topics'].values())=={20}
 assert manifest['batches_complete']==4 and not manifest['training_performed'] and not manifest['evaluation_eligible']
 assert report['threads_without_toxic']>0 and report['threads_ending_with_apology']<200
 for t in threads:assert file_sha(DATA/'threads'/(t['thread_id']+'.json'))==manifest['thread_checksums'][t['thread_id']]
