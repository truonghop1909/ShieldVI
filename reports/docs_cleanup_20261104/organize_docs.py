"""Scoped, reversible documentation consolidation. No code/data/model relocation."""
import argparse,hashlib,json,os,re,zipfile
from collections import defaultdict
from pathlib import Path
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[2];OUT=Path(__file__).resolve().parent
def sha(data):return hashlib.sha256(data).hexdigest()
def save(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def safe(name):
    path=(ROOT/name).resolve()
    if not path.is_relative_to(ROOT) or path==ROOT:raise ValueError('Path outside repository: '+name)
    return path
def rel(path):return Path(path).relative_to(ROOT).as_posix()

def layout():
    moves={}
    for path in (ROOT/'docs').glob('*.md'):
        name=path.name
        if re.match(r'^\d{2}_',name):target='docs/design/'+name
        elif name in ('ARCHITECTURE.md','DATABASE.md','API_CONTRACT.md','MIGRATION.md','T016_POLICY_SPEC.md'):target='docs/architecture/'+name
        elif name in ('RUN_LOCAL.md','DEMO_ABCD.md'):target='docs/guides/'+name
        elif name=='SOCIAL_DESIGN_README.md':target='docs/design/README.md'
        elif name=='REPOSITORY_MERGE_REPORT.md':target='docs/archive/merges/'+name
        elif name.startswith('T0'):target='docs/archive/implementation_reports/'+name
        else:raise ValueError('Unclassified root document '+name)
        moves[rel(path)]=target
    moves.update({
        'README.md':'docs/archive/legacy_guides/V3_OVERVIEW.md','CHANGELOG.md':'docs/CHANGELOG.md',
        'AGENTS_SOCIAL_ADDENDUM.md':'docs/governance/AGENTS_SOCIAL_ADDENDUM.md',
        'HUONG_DAN_SAO_CHEP.md':'docs/archive/legacy_guides/HUONG_DAN_SAO_CHEP.md',
        'PROMPT_CODEX_KHOI_DONG.md':'docs/archive/legacy_guides/PROMPT_CODEX_KHOI_DONG.md',
        'PROMPT_CODEX_TAI_LIEU.md':'docs/archive/legacy_guides/PROMPT_CODEX_TAI_LIEU.md',
        'services/social-api/README.md':'docs/modules/social_api.md',
        'services/moderation-ai/README.md':'docs/modules/moderation_ai.md',
        'apps/social-web/README.md':'docs/modules/social_web.md',
        'apps/moderation-web/README.md':'docs/modules/moderation_web.md',
        'apps/moderation-web/legacy-v3/README.md':'docs/modules/legacy_research_dashboard.md',
        'examples/DEMO_HYBRID_GIAI_THICH.md':'docs/guides/DEMO_HYBRID_GIAI_THICH.md'})
    merged={'frontend/README.md':'docs/modules/legacy_research_dashboard.md'}
    redundant={'docs/demo/REALTIME_TRAINING_DEMO.md':'docs/ai-update/final-report/REALTIME_DEMO_GUIDE.md'}
    redirects={**moves,**merged,**redundant,'README.md':'docs/README.md'}
    return moves,merged,redundant,redirects

def pinned():
    names=set()
    for file in ['reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json','reports/ai_update/v62_research_20261104/V62_LOCK.json']:
        data=json.loads(safe(file).read_text(encoding='utf-8-sig'));names.update(data.get('files',{}))
    return names

def markdown_scope():
    paths=set(ROOT.glob('*.md'))
    for folder in ('docs','tasks','.agents'):
        paths.update(path for path in (ROOT/folder).rglob('*.md') if not any(part in ('baseline','repository-merge-evidence') for part in path.relative_to(ROOT).parts))
    for name in ('services/social-api/README.md','services/moderation-ai/README.md','apps/social-web/README.md','apps/moderation-web/README.md','apps/moderation-web/legacy-v3/README.md','frontend/README.md','examples/DEMO_HYBRID_GIAI_THICH.md'):
        if safe(name).exists():paths.add(safe(name))
    return sorted(paths)

LINK=re.compile(r'(?<!!)\[([^\]\n]*)\]\(([^)\n]+)\)')
def link_parts(value):
    title=''
    if value.startswith('<') and '>' in value:
        index=value.index('>');return value[1:index],value[index+1:]
    match=re.match(r'^(\S+)\s+(["\x27].*)$',value)
    return (match[1], ' '+match[2]) if match else (value,title)
def external(value):return value.startswith('#') or bool(re.match(r'^(?:https?|mailto|app|plugin|data):',value))
def resolve_link(source,href):
    name=unquote(href.split('#',1)[0])
    target=(source.parent/name).resolve()
    if not target.exists() and not name.startswith(('.', '/')) and (ROOT/name).exists():target=(ROOT/name).resolve()
    return target

def rewrite(text,old,new,redirects):
    def change(match):
        href,title=link_parts(match[2])
        if external(href):return match[0]
        target=resolve_link(old,href);fragment=('#'+href.split('#',1)[1]) if '#' in href else ''
        if target.is_relative_to(ROOT):
            key=rel(target)
            if key in redirects:target=safe(redirects[key])
        if old==new and target==resolve_link(old,href):return match[0]
        destination=os.path.relpath(target,new.parent).replace('\\','/')+fragment
        if ' ' in destination:destination='<'+destination+'>'
        return '['+match[1]+']('+destination+title+')'
    text=LINK.sub(change,text)
    # Repository-root paths in backticks/prose also occur in AGENTS/skill/task instructions.
    for previous,destination in sorted(redirects.items(),key=lambda item:-len(item[0])):
        if previous=='README.md':continue
        text=re.sub(r'(?<![A-Za-z0-9_./-])'+re.escape(previous)+r'(?=$|[^A-Za-z0-9_.-]|\.(?=\s|$))',lambda _:destination,text)
    return text

def states():
    result={}
    for path in (ROOT/'tasks').rglob('T0*.md'):
        matches=re.findall(r'^(?:-\s+)?\*\*(?:Status|Trạng thái):\*\*\s*(.+)$',path.read_text(encoding='utf-8-sig'),re.M)
        if matches:result[rel(path)]=matches[0]
    return result

def broken_links(paths):
    result=[]
    for path in paths:
        text=path.read_text(encoding='utf-8-sig')
        for match in LINK.finditer(text):
            href,_=link_parts(match[2])
            if external(href):continue
            target=resolve_link(path,href)
            if not target.exists():result.append({'source':rel(path),'href':href,'resolved':str(target)})
    return result

def prepare():
    moves,merged,redundant,redirects=layout();frozen=pinned();sources=set(moves)|set(merged)|set(redundant)
    if sources&frozen:raise ValueError('Attempted to relocate pinned artifacts')
    for name,target in moves.items():
        assert safe(name).is_file(),name
        assert not safe(target).exists(),target
    assert len(set(moves.values()))==len(moves)
    scope=markdown_scope();original={rel(path):path.read_bytes() for path in scope};edits={}
    for name,data in original.items():
        if name in merged or name in redundant:continue
        destination=moves.get(name,name);text=data.decode('utf-8-sig');updated=rewrite(text,safe(name),safe(destination),redirects)
        if name=='README.md':updated='> Lưu nội dung hướng dẫn V3 cũ để tra cứu. Hướng dẫn hiện hành: [mục lục tài liệu](../../README.md).\n\n'+updated
        if updated!=text:
            if name in frozen:raise ValueError('Pinned document would need edits: '+name)
            edits[name]=('\ufeff' if data.startswith(b'\xef\xbb\xbf') else '')+updated
    for name,target in merged.items():
        parent=next(old for old,new in moves.items() if new==target)
        content=rewrite(original[name].decode('utf-8-sig'),safe(name),safe(target),redirects)
        base=edits.get(parent,original[parent].decode('utf-8-sig'))
        edits[parent]=base+'\n\n## Compatibility entrypoint tại frontend/\n\n'+content.replace('# V3 dashboard compatibility','### Ghi chú compatibility',1)+'\n'
    groups=defaultdict(list)
    for name,data in original.items():
        if name.startswith('docs/') or name in sources:groups[sha(data)].append(name)
    plan={'root':str(ROOT),'moves':moves,'merged':merged,'redundant_pointer_pages':redundant,'redirects':redirects,
        'edited_files':sorted(edits),'task_states_before':states(),'protected_documents_untouched':[name for name in original if name in frozen],
        'exact_duplicate_groups_before':[names for names in groups.values() if len(names)>1],
        'preexisting_broken_links':broken_links(scope),'original_sha256':{name:sha(data) for name,data in original.items()},
        'retained_outside_docs':'Root AGENTS.md and minimal README entrypoint; operational tasks/skills/contracts and dataset/model/license/evidence metadata; sibling original source packs are outside this repository.'}
    save(OUT/'PLAN.json',plan)
    return plan,original,edits

def apply():
    plan,original,edits=prepare()
    backup=OUT/'before.zip'
    if backup.exists():raise ValueError('Previous backup exists; never overwrite')
    changed=set(plan['moves'])|set(plan['merged'])|set(plan['redundant_pointer_pages'])|set(edits)
    with zipfile.ZipFile(backup,'x',compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(changed):archive.writestr(name,original[name])
    for name,target in plan['moves'].items():
        source=safe(name);destination=safe(target)
        assert sha(source.read_bytes())==plan['original_sha256'][name]
        destination.parent.mkdir(parents=True,exist_ok=True);source.rename(destination)
    for previous,content in edits.items():safe(plan['moves'].get(previous,previous)).write_text(content,encoding='utf-8')
    for previous in set(plan['merged'])|set(plan['redundant_pointer_pages']):
        path=safe(previous);assert sha(path.read_bytes())==plan['original_sha256'][previous];path.unlink()
    empty=safe('docs/demo')
    if empty.exists() and not any(empty.iterdir()):empty.rmdir()
    safe('README.md').write_text('# ShieldVI Social AI\n\nTài liệu dự án tập trung tại **[docs/README.md](docs/README.md)**.\n\n- [Chạy demo trên Windows](docs/ai-update/final-report/REALTIME_DEMO_GUIDE.md)\n- [Dataset, gán nhãn và training](docs/ai-update/final-report/DATASET_ANNOTATION_GUIDE.md)\n- [Tiến độ nhiệm vụ](tasks/AUTO_PROGRESS.md)\n',encoding='utf-8')
    assert states()==plan['task_states_before'],'Task status changed'
    plan.update(applied=True,backup_sha256=sha(backup.read_bytes()),moved_files=len(plan['moves']),merged_files=len(plan['merged']),removed_pointer_files=len(plan['redundant_pointer_pages']),reference_files_updated=len(edits))
    save(OUT/'APPLIED.json',plan)
    print(json.dumps({key:plan[key] for key in ('applied','moved_files','merged_files','removed_pointer_files','reference_files_updated')}))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    if args.apply:apply()
    else:
        plan,_,_=prepare();print(json.dumps({'moves':len(plan['moves']),'merge':len(plan['merged']),'remove_redundant_pointer':len(plan['redundant_pointer_pages']),'reference_edits':len(plan['edited_files']),'exact_duplicate_groups':plan['exact_duplicate_groups_before'],'preexisting_broken_links':len(plan['preexisting_broken_links'])}))
