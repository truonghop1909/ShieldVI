"""Check relocation, backup fidelity, links, task states and protected doc hashes."""
import hashlib,json,re,zipfile
from collections import defaultdict
from pathlib import Path
from organize_docs import ROOT,OUT,sha,safe,save,states,markdown_scope,broken_links,LINK

def verify():
    plan=json.loads((OUT/'APPLIED.json').read_text(encoding='utf-8'));errors=[]
    for previous,destination in plan['moves'].items():
        if not safe(destination).is_file():errors.append('missing_destination:'+destination)
        if previous!='README.md' and safe(previous).exists():errors.append('old_active_copy:'+previous)
    for previous in set(plan['merged'])|set(plan['redundant_pointer_pages']):
        if safe(previous).exists():errors.append('redundant_page_remaining:'+previous)
    backup=OUT/'before.zip';restorable=0
    with zipfile.ZipFile(backup) as archive:
        if archive.testzip() is not None:errors.append('backup_crc_failed')
        for name in archive.namelist():
            if sha(archive.read(name))!=plan['original_sha256'][name]:errors.append('backup_changed:'+name)
            restorable+=1
    extra_backup=OUT/'before_index_update.zip'
    if extra_backup.exists():
        with zipfile.ZipFile(extra_backup) as archive:
            if archive.testzip() is not None:errors.append('additional_backup_crc_failed')
            for name in archive.namelist():
                if sha(archive.read(name))!=plan['original_sha256'][name]:errors.append('additional_backup_changed:'+name)
                restorable+=1
    if sha(backup.read_bytes())!=plan['backup_sha256']:errors.append('backup_archive_changed')
    if states()!=plan['task_states_before']:errors.append('task_states_changed')
    for name in plan['protected_documents_untouched']:
        if sha(safe(name).read_bytes())!=plan['original_sha256'][name]:errors.append('protected_document_changed:'+name)
    docs=[p for p in (ROOT/'docs').rglob('*.md') if not any(x in p.relative_to(ROOT).parts for x in ('baseline','repository-merge-evidence'))]
    groups=defaultdict(list)
    for path in docs:groups[sha(path.read_bytes())].append(path.relative_to(ROOT).as_posix())
    duplicates=[items for items in groups.values() if len(items)>1]
    if duplicates:errors.append('duplicate_active_documents')
    links=broken_links(markdown_scope())
    errors.extend('broken_link:'+item['source']+':'+item['href'] for item in links)
    for path in (ROOT/'.agents/skills').glob('*/SKILL.md'):
        text=path.read_text(encoding='utf-8-sig')
        if not text.startswith('---\n') or not re.search(r'^name:\s*\S',text,re.M):errors.append('invalid_skill_frontmatter:'+str(path))
    # Validate plain root paths in agent/task prose too, including paths followed by a sentence period.
    frozen=set(plan['protected_documents_untouched'])
    for path in markdown_scope():
        if path.name=='ORGANIZATION.md' or path.relative_to(ROOT).as_posix() in frozen:continue
        text=LINK.sub('',path.read_text(encoding='utf-8-sig'))
        for previous in set(plan['moves'])|set(plan['merged'])|set(plan['redundant_pointer_pages']):
            if previous=='README.md':continue
            if '/' not in previous and (path.parent/previous).is_file():continue
            if re.search(r'(?<![A-Za-z0-9_./-])'+re.escape(previous)+r'(?=$|[^A-Za-z0-9_.-]|\.(?=\s|$))',text):errors.append('stale_root_reference:'+path.relative_to(ROOT).as_posix()+':'+previous)
    result={'status':'PASS' if not errors else 'FAIL','errors':errors,'moves_verified':len(plan['moves']),'merged_files':len(plan['merged']),
        'redundant_pointer_pages_removed':len(plan['redundant_pointer_pages']),'backup_files_verified':restorable,'backup_sha256':plan['backup_sha256'],
        'task_statuses_unchanged':len(plan['task_states_before']),'protected_documents_unchanged':len(plan['protected_documents_untouched']),
        'active_documents':len(docs),'exact_duplicate_groups':duplicates,'broken_local_links':links,
        'top_level_project_markdown':[p.name for p in ROOT.glob('*.md')],'top_level_docs_markdown':[p.name for p in (ROOT/'docs').glob('*.md')],
        'runtime_code_changed':False,'model_or_dataset_changed':False,'training_performed':False}
    save(OUT/'VALIDATION.json',result);print(json.dumps(result,ensure_ascii=False));return result

if __name__=='__main__':raise SystemExit(0 if verify()['status']=='PASS' else 1)
