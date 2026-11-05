"""Persist task evidence and indexes for the user-authorized autonomous session."""
import argparse,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
STATES=('TODO','IN_PROGRESS','DONE','BLOCKED','WAITING_APPROVAL','SKIPPED_APPROVED')
def update(task,status,note,files=(),tests=(),next_task=''):
    assert status in STATES
    p=next((ROOT/'tasks/moderation-ai').glob(task+'-*.md'))
    text=p.read_text(encoding='utf-8-sig')
    text=re.sub(r'(\*\*Status:\*\*\s*)\w+',lambda m:m[1]+status,text,count=1)
    if status!='IN_PROGRESS':
        text+='\n### Autonomous session 02/11/2026\n\n- Status: '+status+'\n- '+note+'\n- Files: '+', '.join(files)+'\n- Tests: '+'; '.join(tests)+'\n'
    p.write_text(text,encoding='utf-8')
    for rel in ('tasks/moderation-ai/TASK_ORDER_AI.md','tasks/TASK_ORDER.md'):
        q=ROOT/rel;lines=q.read_text(encoding='utf-8-sig').splitlines()
        for i,line in enumerate(lines):
            if line.startswith('|') and (('**'+task+'**') in line or ('['+task+']') in line):
                lines[i]=re.sub(r'\|\s*(?:'+ '|'.join(STATES) +r')\s*\|','| '+status+' |',line)
        q.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    state_path=ROOT/'reports/ai_update/auto_session.json'
    state_path.parent.mkdir(parents=True,exist_ok=True)
    data=json.loads(state_path.read_text(encoding='utf-8')) if state_path.exists() else {'authorization':'User autonomous runner 2026-11-02; no training/deploy/external upload authorized','tasks':{}}
    data['tasks'][task]={'status':status,'note':note,'files':list(files),'tests':list(tests)}
    data['next_task']=next_task
    state_path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    lines=['# AUTO_PROGRESS — 02/11/2026','','User permits sequential safe tasks this session; older one-task stop rules are overridden only for this session. WAITING_APPROVAL is an explicit user-authorized status.','',
      'No checkpoint/0.41 changes, held-out edits, destructive DB operations, external data transfer, training or deployment.','',
      'T020 was already DONE before this session.','']
    for key,v in data['tasks'].items():
        lines += ['## '+key+' — '+v['status'],v['note'],'','Files: '+', '.join(v['files']),'Tests: '+'; '.join(v['tests']),'']
    lines+=['## Resume','Next: '+(next_task or 'determine highest-priority ready task from TASK_ORDER_AI.md'),
      'Root: ShieldVI_V3_Hybrid_Review. Use .venv/Scripts/python.exe; PYTHONDONTWRITEBYTECODE=1, STORE_SUMMARIES=0, temp DB paths for API tests. Read only current task/skill and relevant code.',
      'Evidence: reports/ai_update/auto_session.json. Do not repeat completed tasks. Missing human labels must remain NEEDS_REVIEW; do not infer approval from silence.','']
    (ROOT/'tasks/AUTO_PROGRESS.md').write_text('\n'.join(lines),encoding='utf-8')
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('task');a.add_argument('status',choices=STATES);a.add_argument('note');x=a.parse_args();update(x.task,x.status,x.note)
