"""Validate immutable synthetic regression inputs and prepare non-gold review rows."""
import csv,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.schemas import AnalyzeRequest
FIXTURES=ROOT/'datasets/fixtures/genz_regression'
def load_threads():
    result=[]
    for path in sorted(FIXTURES.glob('*.json')):
        data=json.loads(path.read_text(encoding='utf-8-sig'));thread=AnalyzeRequest.model_validate(data)
        if len(thread.comments)!=30 or len({c.user_id for c in thread.comments})!=5:raise ValueError('Expected 30 comments and 5 users')
        result.append((path,thread))
    if len(result)!=5:raise ValueError('Expected exactly five developer regression threads')
    return result

def review_rows():
    with (FIXTURES/'synthetic_reference_tags.csv').open(encoding='utf-8-sig',newline='') as f:refs=list(csv.DictReader(f))
    lookup={(r['thread_id'],r['comment_id']):r for r in refs}
    if len(lookup)!=150 or len(refs)!=150:raise ValueError('Duplicate/missing source tags')
    rows=[]
    for path,thread in load_threads():
        for c in thread.comments:
            ref=lookup.pop((thread.thread_id,c.comment_id))
            rows.append({'thread_id':thread.thread_id,'comment_id':c.comment_id,'user_id':c.user_id,
             'text_ref':path.relative_to(ROOT).as_posix()+'#'+c.comment_id,'source_type':'synthetic','split':'development_regression',
             'reference_tag':ref['reference_tag'],'expected_context':'','expected_target':'','expected_attack':'',
             'comment_label':'','review_status':'NEEDS_REVIEW','annotator_id':'','reviewed_at':'','notes':'AI-authored reference only; not gold; not training eligible'})
    if lookup:raise ValueError('Unmatched source tags')
    return rows

def export_review(path):
    rows=review_rows();path.parent.mkdir(parents=True,exist_ok=True)
    if path.exists():raise FileExistsError('Never overwrite human review edits')
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return rows
if __name__=='__main__':
    out=ROOT/'datasets/fixtures/genz_regression/reviewer_needed.csv';rows=export_review(out)
    print('Prepared',len(rows),'NEEDS_REVIEW rows; no human annotations invented.')
