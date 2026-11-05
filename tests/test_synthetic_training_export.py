"""AI labels explicitly accepted by user must remain synthetic, never human gold."""
import csv,json,sys
from pathlib import Path
import pytest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from synthetic_data.training_export import export
from synthetic_data.pipeline import DATA,file_sha,atomic_json

@pytest.fixture
def source(tmp_path):
    root=tmp_path/'source';(root/'threads').mkdir(parents=True)
    checksums={}
    for name in ('SYN200_0001','SYN200_0002'):
        path=root/'threads'/(name+'.json');path.write_bytes((DATA/'threads'/path.name).read_bytes());checksums[name]=file_sha(path)
    atomic_json(root/'manifest.json',{'actual_threads':2,'thread_checksums':checksums})
    return root

def test_binary_mapping_excludes_uncertain_without_relabeling(source,tmp_path):
    out=tmp_path/'export';manifest=export(source,out)
    rows=[json.loads(line) for line in (out/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    uncertain=[json.loads(line) for line in (out/'excluded_uncertain.jsonl').read_text(encoding='utf-8').splitlines()]
    assert manifest['source_comments']==22 and len(rows)==21 and len(uncertain)==1
    assert all(row['label']=={'CLEAN':0,'TOXIC':1}[row['comment_label']] for row in rows)
    assert uncertain[0]['comment_label']=='UNCERTAIN' and 'label' not in uncertain[0]
    assert len({(row['thread_id'],row['comment_id']) for row in rows+uncertain})==22

def test_user_acceptance_does_not_forge_human_review_or_evaluation(source,tmp_path):
    out=tmp_path/'export';manifest=export(source,out)
    rows=[json.loads(line) for line in (out/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    assert not manifest['manual_review_required_for_this_export'] and not manifest['training_performed']
    assert all(row['label_source']=='synthetic' and not row['human_gold'] and not row['manual_review_performed'] and not row['evaluation_eligible'] for row in rows)
    assert all(row['split']=='train' and row['review_status']=='AI_REFERENCE_ACCEPTED_BY_USER' for row in rows)
    assert not (out/'test.jsonl').exists() and not (out/'validation.jsonl').exists()

def test_csv_preserves_raw_text_unicode_and_binary_targets(source,tmp_path):
    out=tmp_path/'export';export(source,out)
    with (out/'train.csv').open(encoding='utf-8-sig',newline='') as f:csvrows=list(csv.DictReader(f))
    rows=[json.loads(line) for line in (out/'train.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(csvrows)==len(rows)
    for csvrow,row in zip(csvrows,rows):assert csvrow['Comment']==row['text'] and int(csvrow['Toxicity'])==row['label']

def test_source_is_unchanged_and_export_resume_is_idempotent(source,tmp_path):
    before={p.name:file_sha(p) for p in (source/'threads').glob('*.json')};sha=file_sha(source/'manifest.json')
    out=tmp_path/'export';first=export(source,out);assert export(source,out)==first
    assert before=={p.name:file_sha(p) for p in (source/'threads').glob('*.json')} and file_sha(source/'manifest.json')==sha

def test_export_edited_by_user_is_not_overwritten(source,tmp_path):
    out=tmp_path/'export';export(source,out);(out/'train.csv').write_text('user edit',encoding='utf-8')
    with pytest.raises(FileExistsError,match='never overwrite'):export(source,out)
    assert (out/'train.csv').read_text()=='user edit'

def test_changed_source_checksum_is_rejected_before_export(source,tmp_path):
    path=source/'threads/SYN200_0001.json';t=json.loads(path.read_text(encoding='utf-8'));t['comments'][0]['text']='Edited source text';atomic_json(path,t)
    with pytest.raises(ValueError,match='checksum'):export(source,tmp_path/'export')
    assert not (tmp_path/'export').exists()
