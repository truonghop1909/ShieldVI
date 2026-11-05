import json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
def update(stage,details):
    p=P/'progress.json';state=json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'training_performed':False,'T028':'BLOCKED','milestones':[]}
    state['current']=stage;state['milestones'].append({'stage':stage,'details':details})
    p.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as f:f.write('\n\n## Repeated recovery follow-up — '+stage+'\n\n'+details+'\n')
if __name__=='__main__':update(sys.argv[1],sys.argv[2])
