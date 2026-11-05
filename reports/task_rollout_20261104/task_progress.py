import json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json

def update(task,status,detail,evidence=()):
    assert status in {'NOT_STARTED','IN_PROGRESS','PARTIAL','BLOCKED','DONE_VERIFIED'}
    path=R/'tasks/moderation-ai/AUTO_EXECUTION_STATE.json';state=json.loads(path.read_text())
    item=state['tasks'][task];item.update(status=status,detail=detail,evidence=list(evidence));state['current']=task
    if status=='DONE_VERIFIED':
        ready=[key for key,value in state['tasks'].items() if value['status']=='NOT_STARTED' and all(state['tasks'][dep]['status']=='DONE_VERIFIED' for dep in value['dependencies'])]
        state['next_ready']=ready;state['current']=ready[0] if ready else task
    atomic_json(path,state)
    file=R/item['file'];text=file.read_text(encoding='utf-8');text=re.sub(r'(- \*\*Status:\*\*) [A-Z_]+',r'\g<1> '+status,text,count=1)
    text+='\n\n### Execution evidence\n\n'+detail+'\n\n'+''.join('- '+x+'\n' for x in evidence)
    file.write_text(text,encoding='utf-8')
    for name in ('TASK_ORDER_AI.md','TASK_ACCEPTANCE_MATRIX.md'):
        file=R/'tasks/moderation-ai'/name;text=file.read_text(encoding='utf-8')
        if name=='TASK_ORDER_AI.md':text=re.sub(r'(\| '+task+r' \| )[A-Z_]+( \|)',r'\g<1>'+status+r'\2',text)
        else:text=re.sub(r'(\| '+task+r' \|[^\n]*\| )[A-Z_]+( \|)',r'\g<1>'+status+r'\2',text)
        file.write_text(text,encoding='utf-8')
    with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as stream:
        stream.write('\n\n## '+task+' — '+status+'\n\n'+detail+'\n\nEvidence: '+', '.join(evidence)+'\n')
    (R/'tasks/AUTO_RESUME_T034_T043.md').write_text('# Resume local rollout T034–T043\n\nRead AGENTS/AUTO_PROGRESS and moderation-ai/AUTO_EXECUTION_STATE.json. Current/next: '+state['current']+'; last update '+task+' '+status+'.\n\n'+detail+'\n\nEvidence: '+', '.join(evidence)+'\n\nContinue ready tasks automatically under current user authorization; no paid resource/private data/r07/default/promote/deploy. Original readiness baseline must not be resealed. Prefer additive opt-in factories/modules; original Social schema0004 and existing auth/jobs/review reused. Only initialize extension schema in explicit disposable/local DB. No automation continues after this session ends.\n',encoding='utf-8')
    print(json.dumps({'task':task,'status':status,'next':state['current']}))
