"""Append new Social Feed requirements by task ID; retain historical evidence."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'ShieldVI_T034_T043_Moi_Task_Mot_File';IDS=[f'T{x:03}' for x in range(34,44)]
STATE=ROOT/'tasks/moderation-ai/AUTO_EXECUTION_STATE.json'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def render():
    state=json.loads(STATE.read_text(encoding='utf-8'));rows=state['social_feed_v2']['tasks']
    table='\n## Social Feed v2 — current acceptance\n\nEarlier DONE_VERIFIED describes the previous rollout. This table separately tracks the new requirements; historical evidence is retained.\n\n| Task | v2 status | Dependencies | Canonical task |\n|---|---|---|---|\n'
    for task in IDS:
        row=rows[task];name=Path(state['tasks'][task]['file']).name
        table+=f"| {task} | {row['status']} | {', '.join(row['dependencies'])} | [{name}]({name}) |\n"
    path=ROOT/'tasks/moderation-ai/TASK_ORDER_AI.md'
    path.write_text(path.read_text(encoding='utf-8').split('\n<!-- SOCIAL_FEED_V2 -->')[0]+'\n<!-- SOCIAL_FEED_V2 -->'+table,encoding='utf-8')
    path=ROOT/'tasks/AUTO_RESUME_T034_T043.md'
    pending=[t for t in IDS if rows[t]['status']!='DONE_VERIFIED']
    text='\n## Social Feed v2 resume\n\nCurrent: '+str(state['social_feed_v2']['current'])+'; remaining: '+', '.join(pending)+'.\nUse AUTO_EXECUTION_STATE.json/social_feed_v2 and reports/social_feed_v2_20261104/. Do not rerun historical training automatically.\n'
    path.write_text(path.read_text(encoding='utf-8').split('\n<!-- SOCIAL_FEED_V2 -->')[0]+'\n<!-- SOCIAL_FEED_V2 -->'+text,encoding='utf-8')
def checkpoint(task,status,detail,evidence=()):
    state=json.loads(STATE.read_text(encoding='utf-8'));state['social_feed_v2']['tasks'][task].update(status=status,detail=detail,evidence=list(evidence))
    state['social_feed_v2']['current']=task if status=='IN_PROGRESS' else None;save(STATE,state)
    note=f'\n## {task} Social Feed v2 — {status}, 04/11/2026\n\n{detail}\n\nEvidence: '+', '.join(evidence)+'\n'
    for path in (ROOT/state['tasks'][task]['file'],ROOT/'tasks/AUTO_PROGRESS.md'):
        with path.open('a',encoding='utf-8') as output:output.write(note)
    render()
def main():
    manifest=json.loads((SOURCE/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
    for name,entry in manifest.items():
        path=(SOURCE/name).resolve();assert path.is_relative_to(SOURCE.resolve())
        assert digest(path)==entry['sha256'] and path.stat().st_size==entry['size'],name
    state=json.loads(STATE.read_text(encoding='utf-8'));assert 'social_feed_v2' not in state,'Already merged'
    targets={t:ROOT/state['tasks'][t]['file'] for t in IDS}
    controls=[STATE]+[ROOT/p for p in ('tasks/moderation-ai/TASK_ORDER_AI.md','tasks/TASK_ORDER.md','tasks/AUTO_PROGRESS.md','tasks/moderation-ai/TASK_MERGE_REPORT.md','tasks/AUTO_RESUME_T034_T043.md','tasks/moderation-ai/RULES_REALTIME_STUDIO.md')]
    originals=list(targets.values())+controls
    with zipfile.ZipFile(OUT/'before_merge.zip','x',zipfile.ZIP_DEFLATED) as backup:
        for p in originals:backup.writestr(p.relative_to(ROOT).as_posix(),p.read_bytes())
    result={'source':str(SOURCE),'source_files_verified':len(manifest),'backup_sha256':digest(OUT/'before_merge.zip'),'before_sha256':{p.relative_to(ROOT).as_posix():digest(p) for p in originals},'tasks':{}}
    common=None
    for task in IDS:
        source=next((SOURCE/'tasks/moderation-ai').glob(task+'_*.md'))
        head,tail=source.read_text(encoding='utf-8').split('## Quy tắc chung bắt buộc',1)
        rules=tail.split('## 8. Nhật ký thi công',1)[0].strip()
        if common is None:common=rules
        else:assert common==rules,'Safeguards differ'
        with targets[task].open('a',encoding='utf-8') as output:
            output.write('\n\n---\n\n## Additional Social Feed v2 specification — 04/11/2026\n\nInitial source status below is not an override of verified historical work. Current v2 acceptance is tracked separately.\n\n'+head+'\nShared safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md), Social Feed v2 section. The source journal was unstarted; actual execution follows below.\n')
        result['tasks'][task]={'source':source.relative_to(SOURCE).as_posix(),'source_sha256':digest(source),'destination':targets[task].relative_to(ROOT).as_posix(),'id_collision':'merged; old body preserved'}
    with (ROOT/'tasks/moderation-ai/RULES_REALTIME_STUDIO.md').open('a',encoding='utf-8') as output:
        output.write('\n## Social Feed v2 source safeguards\n\n'+common+'\n\nCurrent user explicitly requests continuation through dependencies, overriding the older one-task-per-turn limit for this session. Paid resources, external data transfer and production changes remain outside scope.\n')
    deps={'T034':[],'T035':['T034'],'T036':['T035'],'T037':['T034','T035','T036'],'T038':['T035','T036','T037'],'T039':['T038'],'T040':['T039'],'T041':['T039'],'T042':['T041'],'T043':IDS[:-1]}
    state['social_feed_v2']={'current':None,'tasks':{t:{'status':'TODO','dependencies':deps[t],'evidence':[]} for t in IDS},'automatic_training_rerun_allowed':False}
    save(STATE,state);save(OUT/'MERGE_MANIFEST.json',result)
    with (ROOT/'tasks/moderation-ai/TASK_MERGE_REPORT.md').open('a',encoding='utf-8') as output:
        output.write('\n## Per-file Social Feed v2 merge — 04/11/2026\n\n10 ID collisions merged into canonical task files, with historical body/status/evidence retained and shared safeguards deduplicated.13source entries SHA/size verified; source pack untouched.17original files backed up in reports/social_feed_v2_20261104/before_merge.zip; source/destination SHA map in MERGE_MANIFEST.json. New Social Feed acceptance is tracked independently; old completion does not imply new acceptance.\n')
    with (ROOT/'tasks/TASK_ORDER.md').open('a',encoding='utf-8') as output:
        output.write('\n## Social Feed v2 current acceptance\n\nThe new10per-file requirements are merged by ID. Current acceptance: [AI order](moderation-ai/TASK_ORDER_AI.md#social-feed-v2--current-acceptance), AUTO_EXECUTION_STATE.json/social_feed_v2. Historical statuses remain unchanged; formal T028/T029 BLOCKED and T030–T033 PARTIAL.\n')
    checkpoint('T034','IN_PROGRESS','Verified and merged the new source pack; audit Social Feed gaps before runtime changes.',['reports/social_feed_v2_20261104/MERGE_MANIFEST.json'])
    print('Merged10tasks; verified13source files; backed up17originals; T034 v2 IN_PROGRESS.')
if __name__=='__main__':main()
