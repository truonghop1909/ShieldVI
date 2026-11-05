# In a consolidated repository, validate the current layout; historical fallback remains below.
import runpy as _merge_runpy
from pathlib import Path as _MergePath
if (_MergePath(__file__).resolve().parents[2] / 'repository-merge-evidence/validate_consolidation.py').is_file():
    _merge_runpy.run_path(str(_MergePath(__file__).resolve().parents[2] / 'repository-merge-evidence/validate_consolidation.py'), run_name='__main__')
    raise SystemExit(0)
"""Read-only structural checks; only writes validation evidence, never runs AI tasks."""
import csv,hashlib,json,re,subprocess,sys
from collections import Counter
from datetime import datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT.parent
SOURCE=BASE/'ShieldVI_AI_Update_Codex_Tasks_v1'
RUNTIME=BASE/'ShieldVI_V3_Hybrid_Review'
EVID=Path(__file__).parent
M=json.loads((EVID/'MERGE_MANIFEST.json').read_text(encoding='utf-8'))
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return p.read_text(encoding='utf-8-sig')
checks={};errors=[]
def check(name,condition):
 checks[name]=bool(condition)
 if not condition:errors.append(name)
# Preserve original source (including the reported damaged file).
check('source_file_inventory_unchanged',set(M['source_files_before'])=={p.relative_to(SOURCE).as_posix() for p in SOURCE.rglob('*') if p.is_file()})
check('source_hashes_unchanged',all((SOURCE/r).exists() and digest(SOURCE/r)==h for r,h in M['source_files_before'].items()))
check('existing_task_files_byte_identical',all(digest(ROOT/r)==h for r,h in M['task_files_before'].items()))
check('all_unchanged_existing_files_byte_identical',all(digest(ROOT/r)==M['existing_files_before'][r] for r in M['unchanged_existing_files']))
check('all_mapped_payloads_preserved',all((ROOT/r).is_file() and digest(ROOT/r)==h for r,h in M['after_hashes'].items()))
files=list((ROOT/'tasks/moderation-ai').glob('T[0-9][0-9][0-9]-*.md'))
ai=[p for p in files if 20<=int(p.name[1:4])<=33]
check('exactly_14_unique_ai_tasks',sorted(p.name[1:4] for p in ai)==[f'{n:03d}' for n in range(20,34)])
check('ai_tasks_all_remain_TODO',all(re.search(r'\*\*Status:\*\*\s*TODO\b',read(p)) for p in ai))
check('ai_order_byte_identical',digest(ROOT/'tasks/moderation-ai/TASK_ORDER_AI.md')==digest(SOURCE/'tasks/moderation-ai/TASK_ORDER_AI.md'))
check('no_duplicate_task_IDs',len([p.name[1:4] for p in (ROOT/'tasks').rglob('T[0-9][0-9][0-9]-*.md')])==len({p.name[1:4] for p in (ROOT/'tasks').rglob('T[0-9][0-9][0-9]-*.md')}))
# Validate JSON payloads and references within each of the five fixture threads.
fixture_dir=ROOT/'datasets/fixtures/genz_regression'
fixtures=sorted(fixture_dir.glob('*.json'));keys=set();fixture_counts=[]
for p in fixtures:
 t=json.loads(read(p));comments=t['comments'];lookup={c['comment_id']:c for c in comments}
 check(p.name+'_shape',len(comments)==30 and len(lookup)==30 and len({c['user_id'] for c in comments})==5)
 for c in comments:
  stamp=datetime.fromisoformat(c['timestamp'].replace('Z','+00:00'))
  assert stamp.utcoffset() is not None
  par=c.get('parent_id')
  assert not par or (par in lookup and par!=c['comment_id'])
  seen={c['comment_id']}
  while par:
   assert par not in seen
   seen.add(par);par=lookup[par].get('parent_id')
  assert c['text'].strip()
  keys.add((t['thread_id'],c['comment_id']))
 fixture_counts.append(len(comments))
check('five_fixtures_150_comments',len(fixtures)==5 and sum(fixture_counts)==150 and len(keys)==150)
with (fixture_dir/'synthetic_reference_tags.csv').open(encoding='utf-8-sig',newline='') as f:tags=list(csv.DictReader(f))
check('all_150_reference_tags_match_fixtures',len(tags)==150 and {(r['thread_id'],r['comment_id']) for r in tags}==keys)
check('templates_preserved',all(digest(ROOT/'templates'/p.name)==digest(p) for p in (SOURCE/'templates').iterdir() if p.is_file()))
with (ROOT/'templates/solo_review_template.csv').open(encoding='utf-8-sig',newline='') as f:
 reader=csv.DictReader(f);check('review_template_columns',all(k in reader.fieldnames for k in ('thread_id','comment_id','review_status','annotator_id')));list(reader)
for directory in ('contracts','templates'):
 for p in (ROOT/directory).glob('*.json'):json.loads(read(p))
check('contract_and_template_JSON_parse',True)
# Check every installed skill frontmatter with the official validator, without invoking any skill workflow.
validator=Path(r'C:/Users/admin/.codex/skills/.system/skill-creator/scripts/quick_validate.py')
skill_results=[];names=[]
for p in sorted((ROOT/'.agents/skills').glob('*/SKILL.md')):
 result=subprocess.run([sys.executable,'-X','utf8',str(validator),str(p.parent)],capture_output=True,text=True,encoding='utf-8')
 skill_results.append({'path':p.relative_to(ROOT).as_posix(),'exit_code':result.returncode,'output':(result.stdout+result.stderr).strip()})
 match=re.search(r'^name:\s*(.+)$',read(p),re.M);names.append(match.group(1) if match else None)
check('all_skills_valid',all(r['exit_code']==0 for r in skill_results))
check('skill_names_unique',None not in names and len(names)==len(set(names)))
check('misplaced_upgrade_metadata_removed', 'name: shieldvi-ai-upgrade' not in read(ROOT/'.agents/skills/shieldvi-ai-integration/SKILL.md'))
# Validate active documentation links, excluding archived baseline evidence and retained source backups.
docs=[ROOT/'AGENTS.md',ROOT/'README.md']+list((ROOT/'tasks').rglob('*.md'))+list((ROOT/'.agents').rglob('*.md'))+list((ROOT/'datasets/fixtures').rglob('*.md'))+list((ROOT/'docs').glob('*.md'))+list((ROOT/'docs/ai-update').glob('*.md'))
link_results=[]
for p in docs:
 for dest in re.findall(r'\[[^\]]*\]\(([^)]+)\)',read(p)):
  dest=dest.split('#',1)[0].strip('<>')
  if not dest or re.match(r'\w+://',dest):continue
  q=(p.parent/dest).resolve();exists=q.exists()
  link_results.append({'file':p.relative_to(ROOT).as_posix(),'target':dest,'exists':exists})
check('active_markdown_links_resolve',all(r['exists'] for r in link_results))
# Classify inline root-relative paths in AI docs/tasks, including globs and migrated legacy aliases.
path_results=[];planned={'reports/ai_update/baseline/','tests/fixtures/ai_update/'}
for p in docs:
 if not (p.is_relative_to(ROOT/'docs/ai-update') or p in ai or p==ROOT/'AGENTS.md' or p==ROOT/'tasks/TASK_ORDER.md' or p==ROOT/'.agents/skills/shieldvi-ai-upgrade/SKILL.md'):continue
 for token in re.findall(r'`([^`\n]+)`',read(p)):
  if not re.match(r'^(docs|tasks|contracts|templates|datasets|services|apps|app|frontend|tests|reports|\.agents)/',token):continue
  if ' ' in token:continue
  if token in planned:classification='planned_output_not_created'
  elif any(c in token for c in '<>') or 'Txxx' in token or 'TXXX' in token:classification='documented_placeholder'
  elif '*' in token:classification='glob_resolves' if list(ROOT.glob(token)) or list(RUNTIME.glob(token)) else 'unresolved'
  elif (ROOT/token).exists():classification='documentation_root'
  elif (RUNTIME/token).exists():classification='runtime_root'
  elif (p.parent/token).exists():classification='relative_to_document'
  elif token.startswith('app/') and (RUNTIME/'services/moderation-ai'/token).exists():classification='legacy_alias_to_canonical_runtime'
  else:classification='unresolved'
  path_results.append({'file':p.relative_to(ROOT).as_posix(),'reference':token,'classification':classification})
check('inline_AI_paths_resolved_or_explicitly_planned',all(r['classification']!='unresolved' for r in path_results))
# Every source file is represented exactly once in the merge mapping, including source manifest and addendum merge.
check('all_source_files_accounted_for',len(M['mapping'])==len(M['source_files_before']) and {r['source'] for r in M['mapping']}==set(M['source_files_before']))
check('merge_report_exists',(ROOT/'docs/ai-update/MERGE_REPORT.md').is_file())
result={'date':'2026-11-02','status':'PASS' if not errors else 'FAIL','checks':checks,'errors':errors,
 'source_integrity_warning':M['source_manifest_mismatches'],'skill_validation':skill_results,
 'active_document_count':len(docs),'markdown_links_checked':len(link_results),'markdown_link_results':link_results,
 'inline_path_results':path_results,'fixture_count':len(fixtures),'fixture_comment_count':sum(fixture_counts),
 'runtime_tests':'NOT_RUN_documentation_only','training':'NOT_RUN','AI_tasks_started':False,
 'scope_note':'Only active docs, imported fixtures and templates; archived baseline evidence is not rewritten or reinterpreted.'}
(EVID/'VALIDATION_RESULTS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':result['status'],'checks':len(checks),'errors':errors,'skills':len(skill_results),'markdown_links':len(link_results),'inline_paths':len(path_results),'fixture_comments':150,'source_warnings':len(M['source_manifest_mismatches'])},ensure_ascii=True))
raise SystemExit(0 if not errors else 1)
