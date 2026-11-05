"""Validate documentation consolidation without loading a model or starting AI tasks."""
import csv,hashlib,json,re,subprocess,sys
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[2];E=Path(__file__).parent;B=R.parent
S=B/'ShieldVI_SocialAI_Design_Docs_v1'
M=json.loads((E/'CONSOLIDATION_MANIFEST.json').read_text(encoding='utf-8'))
def read(p):return p.read_text(encoding='utf-8-sig')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checks={};errors=[]
def check(name,condition):
 checks[name]=bool(condition)
 if not condition:errors.append(name)
check('all_341_source_files_preserved',len(M['source_files'])==341 and all((S/r).is_file() and sha(S/r)==h for r,h in M['source_files'].items()))
check('all_341_files_mapped_once',len(M['mapping'])==341 and {r['source'] for r in M['mapping']}==set(M['source_files']))
check('all_installed_files_match_recorded_hashes',all((R/r['destination']).is_file() and sha(R/r['destination'])==r['destination_sha256'] for r in M['mapping']))
check('no_ambiguous_duplicate_destinations',len({r['destination'] for r in M['mapping']})==len(M['mapping']))
check('existing_README_updates_match_manifest',all(sha(R/r)==h for r,h in M['existing_documentation_after'].items()))
metadata_changes=[]
for rel,before in M['protected_runtime_metadata_before'].items():
 p=R/rel
 if rel in M['allowed_existing_documentation_edits']:continue
 if not p.exists():metadata_changes.append(rel);continue
 st=p.stat()
 if {'size':st.st_size,'mtime_ns':st.st_mtime_ns}!=before:metadata_changes.append(rel)
check('existing_runtime_models_datasets_tests_DB_untouched',not metadata_changes)
status_counts=Counter();task_count=0
for p in (S/'tasks').rglob('T[0-9][0-9][0-9]-*.md'):
 q=R/p.relative_to(S);check(p.stem+'_unchanged',sha(p)==sha(q));task_count+=1
 status=re.search(r'\b(TODO|IN_PROGRESS|BLOCKED|DONE|SKIPPED_APPROVED)\b','\n'.join(read(q).splitlines()[:7]))
 assert status;status_counts[status.group(1)]+=1
check('13_DONE_and_14_TODO_preserved',dict(status_counts)=={'DONE':13,'TODO':14} and task_count==27)
check('AI_order_unchanged',sha(R/'tasks/moderation-ai/TASK_ORDER_AI.md')==sha(S/'tasks/moderation-ai/TASK_ORDER_AI.md'))
check('single_root_AGENTS', 'Root dự án thống nhất' in read(R/'AGENTS.md') and 'Workspace có hai root' not in read(R/'AGENTS.md'))
for folder in ('docs','tasks','.agents/skills','contracts','templates','datasets/fixtures','services','apps'):
 check('root_folder_'+folder,(R/folder).is_dir())
fixtures=list((R/'datasets/fixtures/genz_regression').glob('*.json'));keys=set()
for p in fixtures:
 data=json.loads(read(p));comments=data['comments'];assert len(comments)==30
 ids={c['comment_id'] for c in comments};assert len(ids)==30
 assert all(not c.get('parent_id') or c['parent_id'] in ids for c in comments)
 keys.update((data['thread_id'],c['comment_id']) for c in comments)
with (R/'datasets/fixtures/genz_regression/synthetic_reference_tags.csv').open(encoding='utf-8-sig',newline='') as f:tags=list(csv.DictReader(f))
check('5_fixtures_150_comments_and_tags',len(fixtures)==5 and len(keys)==len(tags)==150 and keys=={(r['thread_id'],r['comment_id']) for r in tags})
check('fixtures_and_templates_byte_preserved',all(sha(R/r['destination'])==r['source_sha256'] for r in M['mapping'] if r['source'].startswith(('datasets/fixtures/','templates/'))))
for folder in ('contracts','templates'):
 for p in (R/folder).glob('*.json'):json.loads(read(p))
check('contracts_templates_JSON_parse',True)
# Original AI update source still exists and has not been repaired silently.
ai_prior=json.loads((S/'docs/ai-update/merge-evidence/MERGE_MANIFEST.json').read_text(encoding='utf-8'))
ai_source=B/'ShieldVI_AI_Update_Codex_Tasks_v1'
check('original_AI_pack_preserved',all(sha(ai_source/r)==h for r,h in ai_prior['source_files_before'].items()))
validation_tool=Path(r'C:/Users/admin/.codex/skills/.system/skill-creator/scripts/quick_validate.py')
skills=[];names=[]
for p in (R/'.agents/skills').glob('*/SKILL.md'):
 run=subprocess.run([sys.executable,'-X','utf8',str(validation_tool),str(p.parent)],capture_output=True,text=True,encoding='utf-8')
 skills.append({'path':p.relative_to(R).as_posix(),'exit_code':run.returncode,'output':(run.stdout+run.stderr).strip()})
 names.append(re.search(r'^name:\s*(.+)$',read(p),re.M).group(1))
check('all_7_skills_valid_unique',len(skills)==7 and all(x['exit_code']==0 for x in skills) and len(names)==len(set(names)))
# Archived baseline snapshots intentionally remain byte-identical; validate active docs only.
docs=[R/'AGENTS.md',R/'README.md']+list((R/'docs').glob('*.md'))+list((R/'docs/ai-update').glob('*.md'))+list((R/'tasks').rglob('*.md'))+list((R/'.agents').rglob('*.md'))+list((R/'datasets/fixtures').rglob('*.md'))
docs += [R/p for p in M['allowed_existing_documentation_edits'] if p!='README.md']
links=[]
for p in docs:
 for value in re.findall(r'\[[^\]]*\]\(([^)]+)\)',read(p)):
  value=value.split('#',1)[0].strip('<>')
  if not value or re.match(r'\w+://',value):continue
  links.append({'file':p.relative_to(R).as_posix(),'target':value,'exists':(p.parent/value).exists()})
check('all_active_Markdown_links_resolve',all(x['exists'] for x in links))
check('documentation_test_17_passed',M['baseline_test']['exit_code']==0 and M['post_merge_test']['exit_code']==0 and M['post_merge_test']['passed']==17)
result={'status':'PASS' if not errors else 'FAIL','date':'2026-11-02','checks':checks,'errors':errors,
 'source_files':341,'runtime_metadata_changes':metadata_changes,'task_status_counts':dict(status_counts),
 'skills':skills,'markdown_links_checked':len(links),'markdown_links':links,'source_AI_skill_warning':ai_prior['source_manifest_mismatches'],
 'baseline_test':M['baseline_test'],'post_merge_test':M['post_merge_test'],
 'no_training':True,'no_deploy':True,'no_AI_task_started':True,'snapshots_preserved_as_history':True}
(E/'VALIDATION_RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'errors':errors,'links':len(links),'source_files':341,'task_status_counts':dict(status_counts),'skills':len(skills),'runtime_metadata_changes':metadata_changes},ensure_ascii=True))
raise SystemExit(0 if not errors else 1)
