from pathlib import Path
import json,re
R=Path.cwd();p=R/'notebooks/T029_Train_Candidate_Prepared.ipynb';nb=json.loads(p.read_text(encoding='utf-8'))
head=nb['cells'][0];text=''.join(head['source']);text+="\n\nCurrent completion note: the user-authorized bounded local CPU classifier-head experiment executed separately via configs/t029_genz500_cpu_head.json (534steps, encoder frozen). This notebook remains the optional full-encoder GPU recipe, unexecuted and not approved for paid execution; it is not evidence of fullGPU training. See reports/ai_update/all_tasks_cpu_20261103.\n";head['source']=text.splitlines(keepends=True);p.write_text(json.dumps(nb,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
p=R/'.agents/skills/shieldvi-ai-upgrade/SKILL.md';s=p.read_text(encoding='utf-8');needle='## Bất biến và kiểm chứng';s=s.replace(needle,'## Current all-task CPU alternative\n- Khi người dùng giao chạy hết task và cho phép sửa blocker, T029 hiện là thí nghiệm head-only CPU có giới hạn4threads/900s/cost0, receipt ràng buộc request/config/data; giữ encoder/base/0.41 và không biến quyền này thành paidGPU/fullfine-tune/production. T031 là review candidate bằng local shadow/fallback/rollback; có thể DONE bằng quyết định reject có bằng chứng. Xem task nguồn/AUTO_PROGRESS; không sửa tiêu chí theo kết quả.\n\n'+needle,1);p.write_text(s,encoding='utf-8')
# Parse both existing Vietnamese and English status conventions, without rewriting confirmed tasks.
rows=[]
for p in sorted((R/'tasks').glob('**/T[0-9][0-9][0-9]-*.md')):
 text=p.read_text(encoding='utf-8-sig')[:1500].replace('**','');match=re.search(r'(?:Status|Trạng thái)\s*:\s*(DONE|TODO|IN_PROGRESS|BLOCKED|WAITING_APPROVAL|SKIPPED_APPROVED)',text,re.I)
 if not match:raise ValueError('Unrecognized task status '+str(p))
 rows.append({'file':str(p.relative_to(R)).replace('\\','/'),'status':match.group(1)})
(R/'reports/ai_update/all_tasks_cpu_20261103/current_inventory.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Repository task inventory:',len(rows),'; remaining:',[(r['file'],r['status']) for r in rows if r['status']!='DONE'])
