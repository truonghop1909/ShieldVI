"""Versioned GenZ dataset: reuse legacy authoring/compiler, preserve old snapshots.
Python compiles explicitly Codex-authored utterances; it does not generate language.
"""
from __future__ import annotations
import argparse,copy,csv,json,re,sys
from collections import Counter,defaultdict
from pathlib import Path
from typing import Literal
from pydantic import Field,model_validator
from . import pipeline as old
ROOT=old.ROOT
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
DATA=old.DATA/'genz_v2';CATALOGUE=Path(__file__).parent/'genz_catalogue'
CHECKPOINTS=(200,220,250,300,350,400,450,500)
CASES=dict(zip('ABCDEFGHIJKLMNOPQRST',('normal_chat','heated_debate','profanity_venting','direct_insult','repeated_attack','mutual_attack','group_attack','intervention','attacker_apology','apology_response','quoted_abuse','indirect_attack','ambiguous_banter','english_abuse','obfuscated_abuse','constructive_criticism','self_defense','subtle_escalation','mixed_apology_attack','no_conflict')))
TOPICS={'idol':'fandom','fan_antifan':'fandom','fanart':'fanart_cosplay','tiktok':'tiktok_youtube'}

def profanity(text):
    text=text.casefold().replace('sh1t','shit');text=re.sub(r'(?<=\w)[.](?=\w)','',text)
    return bool(re.search(r'(?iu)(?<!\w)(?:đm|dm|dcm|djt|đệt|địt|đéo|lồn|cặc|vcl|vkl|vl|f(?:u|\*)?ck|shit|wtf)(?!\w)',text))

def target_cue(text):return bool(re.search(r'(?iu)\b(?:mày|may|you|m|đứa|thằng|loại|đồ|đầu|mặt|fan như)\b',text))

def observed_cases(t):
    tags=set();attacks=[];seen_actors=set();by_id={c['comment_id']:c for c in t['comments']}
    for c in t['comments']:
        a=c['annotation'];role=a['semantic_role']
        if a['label']=='TOXIC':
            tags.add('D');attacks.append((c['user_id'],a['directed_at_user_id']))
            if a['is_repeated_attack']:tags.add('E')
            if role=='indirect_attack':tags.add('L')
            if role=='indirect_attack' and c['user_id'] in seen_actors:tags.add('R')
            if re.search(r'(?i)\b(?:fuck|f\*ck|f\.u\.c\.k|trash|loser|l0ser|noob|n0ob)\b',c['text']):tags.add('N')
            if re.search(r'(?i)f\*ck|f\.u\.c\.k|sh1t|n0ob|l0ser|d\.m|djt',c['text']):tags.add('O')
        if a['is_apology'] and c['user_id'] in seen_actors:tags.add('I')
        if a['is_apology'] and a['label']=='TOXIC':tags.add('S')
        if a['is_directed_attack']:seen_actors.add(c['user_id'])
        if a['label']=='CLEAN' and a['has_profanity'] and not a['is_quote']:tags.add('C')
        if role=='criticism':tags.add('P')
        if role=='defense':tags.add('Q')
        if role=='intervention':tags.add('H')
        if a['is_quote'] and a['label']=='CLEAN':tags.add('K')
        if a['label']=='UNCERTAIN':tags.add('M')
        if c['parent_id'] and by_id[c['parent_id']]['annotation']['is_apology'] and c['user_id']!=by_id[c['parent_id']]['user_id']:tags.add('J')
    pairs=set(attacks)
    if any((b,a) in pairs for a,b in pairs):tags.add('F')
    targets=defaultdict(set)
    for actor,target in pairs:targets[target].add(actor)
    if any(len(actors)>1 for actors in targets.values()):tags.add('G')
    if not attacks:tags.add('T')
    if all(c['annotation']['label']=='CLEAN' for c in t['comments']):tags.add('A')
    if not attacks and any(c['annotation']['semantic_role']=='criticism' for c in t['comments']):tags.add('B')
    return sorted(tags)

class Annotation(old.Annotation):
    category:Literal['NONE','PROFANITY','INSULT','HARASSMENT','THREAT','OTHER']
    semantic_role:str
    has_profanity:bool
    is_directed_attack:bool
    needs_human_review:bool
    target_evidence:str|None=None
    attack_assertion:Literal['yes','no','uncertain']
class Comment(old.Comment):annotation:Annotation
class Thread(old.Thread):
    thread_id:str=Field(pattern=r'^SGZ500_\d{4}$')
    comments:list[Comment]=Field(min_length=10,max_length=30)
    scenario_type:str
    scenario_family:str
    scenario_tags:list[str]
    split:Literal['train','development_challenge']
    random_seed:int
    authoring_plan:dict
    source_lineage:dict
    @model_validator(mode='after')
    def genz_rules(self):
        for c in self.comments:
            a=c.annotation
            if a.label=='UNCERTAIN' and (not a.needs_human_review or a.attack_assertion!='uncertain'):raise ValueError('Uncertain label must retain uncertainty/review flag')
            if a.is_directed_attack and (not a.target_evidence or not a.directed_at_user_id):raise ValueError('Asserted target needs authored textual evidence')
            if a.category=='THREAT' and a.label!='TOXIC':raise ValueError('Threat annotation inconsistent')
        return self

def convert(t,number,seed,plan=None,source_path=None,threats=()):
    t=copy.deepcopy(t);original_tid=t['thread_id'];tid=f'SGZ500_{number:04d}'
    def remap(value):return value.replace(original_tid,tid,1) if value else None
    for index,c in enumerate(t['comments'],1):
        c['comment_id']=remap(c['comment_id']);c['parent_id']=remap(c['parent_id']);c['user_id']=remap(c['user_id'])
        a=c['annotation'];role='threat' if index in threats else a['category'];uncertain=a['label']=='UNCERTAIN';attack=a['is_directed_attack'] is True
        a['directed_at_user_id']=None if uncertain else remap(a['directed_at_user_id']);a['evidence_comment_ids']=[remap(v) for v in a['evidence_comment_ids']]
        prof=profanity(c['text']);review=uncertain or (attack and not target_cue(c['text']))
        category='THREAT' if role=='threat' else 'HARASSMENT' if a['is_repeated_attack'] else 'INSULT' if attack else 'PROFANITY' if role=='profanity_exclamation' else 'OTHER' if role in ('quote','ambiguous') else 'NONE'
        a.update(category=category,semantic_role=role,has_profanity=prof,is_directed_attack=attack,needs_human_review=review,
          target_evidence=c['text'] if attack else None,attack_assertion='uncertain' if uncertain else 'yes' if attack else 'no')
    for p in t['participants']:p['user_id']=remap(p['user_id'])
    t['thread_id']=tid;t['topic']=TOPICS.get(t['topic'],t['topic']);tags=observed_cases(t);t['scenario_tags']=tags
    plan=plan or {};primary=plan.get('primary') or ('E' if 'E' in tags else 'M' if 'M' in tags else 'T' if 'T' in tags else 'D')
    family=plan.get('family') or 'legacy_'+t['topic']
    # Imported development/trained-on source always stays training; never claim a blind split.
    split='train' if number<=200 else 'development_challenge' if int(old.digest((str(seed)+family).encode())[:8],16)%5==0 else 'train'
    t.update(scenario_type=CASES.get(primary,primary),scenario_family=family,split=split,random_seed=seed,
      authoring_plan={'topic':t['topic'],'context':t['title'],'roles_and_voice':t['participants'],'primary_situation':primary,'family':family,
       'communicative_goal':plan.get('goal','explicitly authored in source dialogue'),'ending':plan.get('ending','open or scene-specific'),
       'planning_source':'new Codex-authored scenario header' if number>200 else 'legacy Codex catalogue; diagnostic categorization'},
      source_lineage={'original_thread_id':original_tid,'source_path':source_path,'source_sha256':old.file_sha(ROOT/source_path) if source_path else t['source_catalogue_sha256'],
        'method':'legacy text preserved; schema/IDs/categories adapted' if number<=200 else 'new Codex-authored utterances; deterministic schema compiler'})
    return Thread.model_validate(t).model_dump(mode='json')

def authored_specs(catalogue=CATALOGUE):
    specs=old.read_catalogue(catalogue);headers={}
    for path in sorted(Path(catalogue).glob('scenarios_*.txt')):
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if line.startswith('@@'):
                parts=line[2:].split('|');headers[int(parts[0])]={'primary':parts[4] if len(parts)>4 else 'A','family':parts[5] if len(parts)>5 else 'scene_'+parts[0],
                  'ending':parts[6] if len(parts)>6 else 'open','goal':parts[7] if len(parts)>7 else parts[2]}
    return [(spec,headers[spec['number']]) for spec in specs]

def load_candidates(through,seed,catalogue=CATALOGUE):
    threads=[]
    for n,path in enumerate(sorted((old.DATA/'threads').glob('*.json')),1):
        threads.append(convert(json.loads(path.read_text(encoding='utf-8')),n,seed,source_path=str(path.relative_to(ROOT))))
    if len(threads)!=200:raise ValueError('Expected immutable legacy source200, not a different inventory')
    specs=authored_specs(catalogue)
    if len(specs)<through-200:raise ValueError('Requested new dialogue has not yet been authored')
    for i,(spec,plan) in enumerate(specs[:through-200],201):
        spec=copy.deepcopy(spec);spec['number']=i;threats=[]
        for index,row in enumerate(spec['rows'],1):
            if row[1].startswith('K'):
                threats.append(index);row[1]=row[1].replace('K','T',1)
                if len(row)<6:row.append('Lời đe dọa hướng đến người trong tình huống hư cấu.')
        t=old.compile_thread(spec);threads.append(convert(t,i,seed,plan,threats=threats))
    return threads

def delex(text):
    text=old.normalized(text)
    for a,b in [('khum','không'),('hok','không'),('ko','không'),('tui','tôi'),('mình','tôi'),('tớ','tôi'),('bạn ấy','người kia'),('xin lỗi','nhận lỗi')]:text=re.sub(r'\b'+re.escape(a)+r'\b',b,text)
    text=re.sub(r'\b(?:[A-Fa-f]|u\d+)\b|\d+','<id>',text)
    return text

def validate(threads):
    checked=[Thread.model_validate(t).model_dump(mode='json') for t in threads]
    # Reuse legacy duplicate detector through an adapter; leave the original dataset unchanged.
    adapted=[]
    for n,t in enumerate(checked,1):
        x=copy.deepcopy(t);tid=f'SYN200_{n:04d}';previous=x['thread_id']
        for c in x['comments']:
            for key in ('comment_id','user_id','parent_id'):
                if c[key]:c[key]=c[key].replace(previous,tid,1)
            a=c['annotation'];a['directed_at_user_id']=a['directed_at_user_id'].replace(previous,tid,1) if a['directed_at_user_id'] else None
            a['evidence_comment_ids']=[v.replace(previous,tid,1) for v in a['evidence_comment_ids']]
            a['category']=a.pop('semantic_role')
            for key in ('has_profanity','needs_human_review','target_evidence','attack_assertion'):a.pop(key)
        for p in x['participants']:p['user_id']=p['user_id'].replace(previous,tid,1)
        x['thread_id']=tid
        for key in ('scenario_type','scenario_family','scenario_tags','split','random_seed','authoring_plan','source_lineage'):x.pop(key)
        adapted.append(x)
    report=old.validate(adapted)
    shapes=Counter();delex_grams=[];pairs=[]
    for t in checked:
        speaker_ids={uid:i for i,uid in enumerate(dict.fromkeys(c['user_id'] for c in t['comments']))}
        shapes[tuple((speaker_ids[c['user_id']],c['annotation']['semantic_role']) for c in t['comments'])]+=1
        g=old.grams(delex('\n'.join(c['text'] for c in t['comments'])))
        for i,other in enumerate(delex_grams):
            score=len(g&other)/len(g|other)
            if score>=.60:pairs.append({'threads':[checked[i]['thread_id'],t['thread_id']],'score':round(score,4)})
        delex_grams.append(g)
    if pairs:report['errors'].append({'code':'delexicalized_near_duplicate_threads','pairs':pairs})
    family_splits=defaultdict(set)
    for t in checked:family_splits[t['scenario_family']].add(t['split'])
    if any(len(s)>1 for s in family_splits.values()):report['errors'].append({'code':'scenario_family_split_leakage'})
    if max(shapes.values(),default=0)>max(10,len(checked)*.2):report['errors'].append({'code':'dominant_repeated_scenario_structure'})
    report.update(status='PASS' if not report['errors'] else 'FAIL',near_duplicate_threads=len(pairs),unique_role_structures=len(shapes),max_role_structure_frequency=max(shapes.values(),default=0),
      scenario_types=dict(Counter(t['scenario_type'] for t in checked)),scenario_coverage=dict(Counter(tag for t in checked for tag in t['scenario_tags'])),
      splits=dict(Counter(t['split'] for t in checked)),needs_review_comments=sum(c['annotation']['needs_human_review'] for t in checked for c in t['comments']),
      profanity_comments=sum(c['annotation']['has_profanity'] for t in checked for c in t['comments']),
      limitations=['AI labels, no human gold.','200 legacy threads reused with lineage; remaining text authored in-session by Codex.',
        'Metadata/ID/schedule/category conversion uses deterministic rules; profanity flags are heuristic, never label assignment.',
        'Character/delexicalized similarity and role-pattern statistics cannot prove semantic novelty or annotation correctness.',
        'Development challenge labels are AI-authored and are not independent real-world evaluation.'])
    report['quality_limitations']=report['limitations']
    return report

def verified_export(directory=DATA):
    """Recompute eligibility from immutable records, not a user-edited READY flag."""
    directory=Path(directory);manifest=json.loads((directory/'dataset_manifest.json').read_text(encoding='utf-8'))
    if manifest['threads']!=500 or manifest['data_origin']!='synthetic' or manifest['human_gold'] is not False:
        raise ValueError('Expected complete AI-only GenZ500 version')
    for name,sha in manifest['output_sha256'].items():
        if old.file_sha(directory/name)!=sha:raise ValueError('GenZ output checksum mismatch: '+name)
    threads=[]
    for tid,sha in manifest['thread_sha256'].items():
        path=directory/'threads'/(tid+'.json')
        if old.file_sha(path)!=sha:raise ValueError('GenZ thread checksum mismatch: '+tid)
        threads.append(Thread.model_validate_json(path.read_text(encoding='utf-8')).model_dump(mode='json'))
    report=validate(threads)
    if report['status']!='PASS':raise ValueError('GenZ validation failed')
    expected=[]
    for t in threads:
        for c in t['comments']:
            a=c['annotation']
            if t['split']=='train' and a['label']!='UNCERTAIN' and not a['needs_human_review']:
                expected.append((t['thread_id'],c['comment_id'],c['text'],str(int(a['label']=='TOXIC'))))
    with (directory/'train_comments.csv').open(encoding='utf-8-sig',newline='') as f:
        actual=[(r['thread_id'],r['comment_id'],r['Comment'],r['Toxicity']) for r in csv.DictReader(f)]
    if expected!=actual:raise ValueError('Training CSV disagrees with eligible authored annotations')
    challenge=[t for t in threads if t['split']=='development_challenge']
    if not challenge:raise ValueError('Missing separate development challenge')
    stored=[json.loads(line) for line in (directory/'development_threads.jsonl').read_text(encoding='utf-8').splitlines()]
    if stored!=challenge:raise ValueError('Challenge export differs from thread records')
    return manifest,threads,report

def checkpoint(through=500,seed=20261103,output=DATA):
    if through not in CHECKPOINTS:raise ValueError('Use checkpoints 200,220,250,300,350,400,450,500')
    output=Path(output);threads=load_candidates(through,seed);report=validate(threads)
    if report['status']!='PASS':old.atomic_json(output/'batches/rejected_validation.json',report);raise ValueError('Content rejected; inspect issues and revise new authored content, never relax quality gates')
    previous=json.loads((output/'dataset_manifest.json').read_text(encoding='utf-8')) if (output/'dataset_manifest.json').exists() else {}
    if previous and (previous['seed']!=seed or previous['threads']>through):raise ValueError('Use new version for seed changes; never shrink')
    for t in threads:
        path=output/'threads'/(t['thread_id']+'.json')
        if path.exists() and json.loads(path.read_text(encoding='utf-8'))!=t:raise FileExistsError('Existing thread changed; never overwrite')
        if not path.exists():old.atomic_json(path,t)
        clean={'thread_id':t['thread_id'],'comments':[{k:c[k] for k in ('comment_id','parent_id','user_id','timestamp','text')} for c in t['comments']]}
        from app.schemas import AnalyzeRequest
        AnalyzeRequest.model_validate(clean)
        old.atomic_json(output/'dashboard_threads'/(t['thread_id']+'.json'),clean)
    train=[];review=[];excluded=[]
    for t in threads:
        for c in t['comments']:
            a=c['annotation'];review.append({'thread_id':t['thread_id'],'comment_id':c['comment_id'],'text':c['text'],'ai_label':a['label'],'human_label':'',
              'needs_human_review':a['needs_human_review'],'label_source':'synthetic','split':t['split'],'reason':a['label_reason']})
            row={'thread_id':t['thread_id'],'comment_id':c['comment_id'],'Comment':c['text'],'Toxicity':int(a['label']=='TOXIC') if a['label']!='UNCERTAIN' else None,
              'label_source':'synthetic','data_origin':'synthetic','scenario_family':t['scenario_family'],'needs_human_review':a['needs_human_review']}
            if t['split']=='train' and a['label']!='UNCERTAIN' and not a['needs_human_review']:train.append(row)
            elif t['split']=='train':excluded.append({'thread_id':t['thread_id'],'comment_id':c['comment_id'],'label':a['label'],'reason':'UNCERTAIN or annotation review flag'})
    for name,rows in [('train_comments.csv',train),('labels_review.csv',review)]:
        with (output/name).open('w',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    for name,rows in [('train_threads.jsonl',[t for t in threads if t['split']=='train']),('development_threads.jsonl',[t for t in threads if t['split']=='development_challenge']),('excluded_training_targets.jsonl',excluded)]:
        (output/name).write_text(''.join(json.dumps(row,ensure_ascii=False)+'\n' for row in rows),encoding='utf-8')
    completed=[x for x in CHECKPOINTS if x<=through]
    for end in completed:
        start=0 if end==200 else CHECKPOINTS[CHECKPOINTS.index(end)-1];subset=threads[start:end]
        for block in ([subset[i:i+50] for i in range(0,200,50)] if end==200 else [subset]):
            ids=[t['thread_id'] for t in block];name='import_'+ids[0] if end==200 else 'new_'+str(end)
            value={'threads':len(block),'thread_ids':ids,'checksums':{tid:old.file_sha(output/'threads'/(tid+'.json')) for tid in ids},'data_origin':'synthetic','labels':'AI_reference_not_human','validation':'PASS global corpus'}
            path=output/'batches'/(name+'.json')
            if not path.exists():old.atomic_json(path,value)
    manifest={'status':'COMPLETE_AI_LABELED_NOT_HUMAN_GOLD' if through==500 else 'IN_PROGRESS','threads':through,'target':500,'comments':report['comments'],
      'legacy_reused':200,'new_codex_authored':through-200,'seed':seed,'label_source':'synthetic','data_origin':'synthetic','human_gold':False,'real_threads':0,
      'family_splits':{t['scenario_family']:t['split'] for t in threads},'splits':report['splits'],'training_rows':len(train),'training_targets_excluded':len(excluded),
      'labels':report['labels'],'batch_manifests':len(list((output/'batches').glob('import_*.json')))+len(list((output/'batches').glob('new_*.json'))),
      'thread_sha256':{t['thread_id']:old.file_sha(output/'threads'/(t['thread_id']+'.json')) for t in threads},
      'output_sha256':{name:old.file_sha(output/name) for name in ('train_comments.csv','train_threads.jsonl','development_threads.jsonl','labels_review.csv','excluded_training_targets.jsonl')},
      'training_performed':False,'evaluation_kind':'synthetic_development_only','next_checkpoint':next((x for x in CHECKPOINTS if x>through),None)}
    old.atomic_json(output/'dataset_manifest.json',manifest);old.atomic_json(output/'batches/quality_latest.json',report)
    lines=['# GenZ v2 quality report','',f"Synthetic {through}/500; comments {report['comments']}; legacy200 preserved; REAL=0.",
      'Labels: '+json.dumps(report['labels']),'Topics: '+json.dumps(report['topics']),'Splits: '+json.dumps(report['splits']),
      'Scenario coverage: '+json.dumps(report['scenario_coverage']),'Duplicate comments: '+str(report['exact_duplicate_comments'])+'; near comments: '+str(report['near_duplicate_comments'])+'; near threads: '+str(report['near_duplicate_threads']),
      'Unique role structures: '+str(report['unique_role_structures'])+'; max frequency: '+str(report['max_role_structure_frequency']),
      'Human-review flags: '+str(report['needs_review_comments'])+'; binary training rows: '+str(len(train)),'',*['- '+v for v in report['limitations']]]
    (output/'quality_report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    progress=ROOT/'reports/ai_update/autonomous_20261103/progress.json';state=json.loads(progress.read_text(encoding='utf-8'));state.update(synthetic_threads=through,synthetic_comments=report['comments'],synthetic_batches=manifest['batch_manifests'],next_action='Author next batch' if through<500 else 'Run T029 development preparation and independent T030-T033 work');old.atomic_json(progress,state)
    with (ROOT/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as f:f.write(f"\nGenZ v2 checkpoint {through}/500: {report['comments']} comments, {manifest['batch_manifests']} batch manifests; validation PASS, exact/near duplicate 0; REAL remains0/BLOCKED. Next checkpoint {manifest['next_checkpoint']}. Source catalogue scripts/synthetic_data/genz_catalogue; all original200 snapshots untouched.\n")
    return manifest

def main():
    p=argparse.ArgumentParser();p.add_argument('--through',type=int,choices=CHECKPOINTS,default=500);p.add_argument('--seed',type=int,default=20261103);a=p.parse_args();m=checkpoint(a.through,a.seed)
    print(json.dumps({k:m[k] for k in ('status','threads','comments','legacy_reused','new_codex_authored','training_rows','splits','labels','next_checkpoint')},ensure_ascii=True))
if __name__=='__main__':main()
