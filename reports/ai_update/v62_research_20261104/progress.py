import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json

def record(stage,detail):
    path=P/'progress.json';state=json.loads(path.read_text()) if path.exists() else {'scope':'controlled_v62_research','training_performed':False,'milestones':[]}
    state['current']=stage
    if not any(x['stage']==stage for x in state['milestones']):
        state['milestones'].append({'stage':stage,'detail':detail})
        with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as stream:stream.write('\n\n## Controlled v6.2 — '+stage+'\n\n'+detail+'\n')
    atomic_json(path,state)
