"""Compile explicit AI-authored recovery examples; never modifies existing fixtures."""
import copy,json,sys,hashlib,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from synthetic_data import pipeline as old
from app.schemas import AnalyzeRequest
DATA=ROOT/'datasets/fixtures/context_recovery_v1'

def generate():
    DATA.mkdir(parents=True,exist_ok=True)
    # The shared reader accepts scenario files; a task-owned scratch directory preserves its naming convention.
    temp=ROOT/'reports/ai_update/context_recovery_20261103/catalogue';temp.mkdir(parents=True,exist_ok=True)
    source=Path(__file__).parent/'synthetic_data/context_recovery_catalogue.txt'
    (temp/'scenarios_recovery.txt').write_bytes(source.read_bytes());specs=old.read_catalogue(temp)
    expected=[]
    for spec in specs:
        spec=copy.deepcopy(spec);ack=[]
        for i,row in enumerate(spec['rows']):
            if row[1]=='X':ack.append(i);row[1]='N'
        t=old.compile_thread(spec);previous=t['thread_id'];tid='CTX_RECOVERY_V1_'+str(spec['number']).zfill(2)
        for c in t['comments']:
            for key in ('comment_id','user_id','parent_id'):
                if c[key]:c[key]=c[key].replace(previous,tid)
            a=c['annotation']
            if a['directed_at_user_id']:a['directed_at_user_id']=a['directed_at_user_id'].replace(previous,tid)
            a['evidence_comment_ids']=[v.replace(previous,tid) for v in a['evidence_comment_ids']]
        for p in t['participants']:p['user_id']=p['user_id'].replace(previous,tid)
        t.update(thread_id=tid,label_source='synthetic',human_gold=False,training_eligible=False,evaluation_eligible=False)
        for i in ack:t['comments'][i]['annotation']['category']='acknowledgement'
        history={}
        for c in t['comments']:
            a=c['annotation']
            if a['label']=='TOXIC' and a['is_directed_attack']:
                pair=(c['user_id'],a['directed_at_user_id']);prior=history.setdefault(pair,[])
                a['is_repeated_attack']=bool(prior);a['evidence_comment_ids']=prior+[c['comment_id']] if prior else []
                prior.append(c['comment_id'])
        payload={'thread_id':tid,'comments':[{k:c[k] for k in ('comment_id','user_id','parent_id','text','timestamp')} for c in t['comments']]}
        AnalyzeRequest.model_validate(payload)
        for folder,value in [('threads',t),('dashboard_threads',payload)]:
            path=DATA/folder/(tid+'.json');path.parent.mkdir(exist_ok=True)
            if path.exists() and json.loads(path.read_text(encoding='utf-8'))!=value:raise FileExistsError('Never overwrite authored expectations')
            if not path.exists():old.atomic_json(path,value)
        expected.append(t)
    game=next((ROOT/'datasets/fixtures/genz_regression').glob('*GAME*.json'));t=json.loads(game.read_text(encoding='utf-8'))
    attachment=Path('C:/Users/admin/.codex/attachments/34824cb4-342d-49db-8742-f6045883b790/Pasted text.txt')
    ref={'thread_id':t['thread_id'],'input_file':str(game.relative_to(ROOT)).replace('\\','/'),'input_sha256':old.file_sha(game),
      'label_source':'user_provided_reference','human_gold':False,'review_status':'REFERENCE_ONLY','independent_evaluation_eligible':False,
      'provenance_note':'User correction for development regression, not an independently adjudicated human-gold dataset.',
      'attachment_sha256':old.file_sha(attachment),'labels':{c['comment_id']:'TOXIC' if c['comment_id'] in ('c08','c11','c15','c18') else 'CLEAN' for c in t['comments']},
      'expected_repeated':{'actor_user_id':'U02','target_user_id':'U03','evidence_comment_ids':['c08','c11','c15','c18']},
      'focus_context_AI_reference':{'c12':'INTERVENTION','c16':'INTERVENTION','c21':'ACKNOWLEDGEMENT','c23':'APOLOGY','c24':'DEFENSE'}}
    path=DATA/'game_rank_30_reference.json'
    if path.exists() and json.loads(path.read_text(encoding='utf-8'))!=ref:raise FileExistsError('User reference is frozen')
    if not path.exists():old.atomic_json(path,ref)
    texts=[c['text'] for t in expected for c in t['comments']]
    if len({old.normalized(v) for v in texts})!=len(texts):raise ValueError('Duplicate authored comment')
    manifest={'status':'GENERATED_BEFORE_RULE_CHANGES','data_origin':'synthetic','label_source':'synthetic','human_gold':False,'new_threads':len(expected),'new_comments':len(texts),
      'existing_synthetic500_preserved':True,'user_reference_comments':30,'source_sha256':old.file_sha(source),'independent_test':False,
      'file_sha256':{str(p.relative_to(DATA)).replace('\\','/'):old.file_sha(p) for p in sorted(DATA.glob('threads/*.json'))},'user_reference_sha256':old.file_sha(path)}
    old.atomic_json(DATA/'manifest.json',manifest)
    (DATA/'README.md').write_text('# Context recovery development dataset\n\n12 newly AI-authored synthetic threads /120comments (3–4speakers,10comments each), authored and frozen before rules were edited. New text in scripts/synthetic_data/context_recovery_catalogue.txt. Labels are AI references, not human gold, and training_eligible=false because these are rule-development examples. No real dataset/contact/collector/manual labeling required.\n\nGAME input is the unchanged existing fixture referenced by game_rank_30_reference.json; all30labels are the user-provided correction, reference-only/not independent human gold. ExpectedTOXIC only c08,c11,c15,c18; remaining26CLEAN. Original fixtures/test/GenZ500 are not overwritten.\n\nPaired cases cover intervention, apology, responsibility, victim feelings, quoted/endorsed abuse, threats and new attacks after apology/acknowledgment separated by comma/period/contrast. Do not alter labels to pass a rule test. See reports/ai_update/context_recovery_20261103 for before/after and regressions.\n',encoding='utf-8')
    print(json.dumps({'new_threads':len(expected),'new_comments':len(texts),'user_reference_comments':30,'human_gold':False}))
if __name__=='__main__':generate()
