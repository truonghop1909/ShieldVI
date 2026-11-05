from __future__ import annotations
import argparse,collections,hashlib,json,os,re,time
from pathlib import Path
from urllib.parse import quote,urlsplit
from .core import DATA,HOSTS,LICENSE,RealThread,Pseudonymizer,atomic_json,load_json,sha_file,extract_threads,structural_quality,thread_text,near_similarity,comparison,now
from .http_client import ApiClient,CollectionBlocked,validate_contact
TARGETS=(20,50,100,200)
PREFIXES={'vi.wikipedia.org':['Thảo luận','Bàn tham khảo','Tin nhắn cho bảo quản viên','Biểu quyết xoá bài'],
 'vi.wiktionary.org':['Thảo luận','Bàn thảo luận'], 'vi.wikibooks.org':['Bàn thảo luận','Thảo luận']}
TOPICS=['Liên Minh Huyền Thoại','YouTube','Sơn Tùng M-TP','Âm nhạc','Bóng đá','Điện thoại thông minh','Trí tuệ nhân tạo','Giáo dục','TikTok','Điện ảnh','Ẩm thực Việt Nam','Du lịch Việt Nam','Manga','Cosplay','Taylor Swift','Việt Nam']
def vietnamese_candidate(thread):
    value=thread_text(thread)
    return len(re.findall(r'[ăâđêôơưĂÂĐÊÔƠƯàáảãạèéẻẽẹìíỉĩịòóỏõọùúủũụỳýỷỹỵ]',value))>=15 and bool(re.search(r'(?i)\b(?:và|của|không|nhưng|các|được|người|mình)\b',value))
def audited_source(client,data_root):
    path=Path(data_root)/'manifests/sources.json';sources=load_json(path,{})
    data,key=client.get({'action':'query','meta':'siteinfo','siprop':'rightsinfo'})
    rights=data.get('query',{}).get('rightsinfo',{})
    license_url=urlsplit(rights.get('url',''));allowed=license_url.hostname=='creativecommons.org' and license_url.path.startswith('/licenses/by-sa/4.0/')
    info={'source_platform':client.host,'api':'https://'+client.host+'/w/api.php','checked_at':now(),'status':'ALLOWED' if allowed else 'UNKNOWN',
     'rightsinfo':rights,'rights_response_sha256':key,'evaluation_only':True,'training_authorized':False,'attribution':'source/revision/history page link + CC BY-SA notice + change notice',
     'retention':'local raw ignored; no public release before privacy/source review; respect suppression/recheck source before release'}
    sources[client.host]=info;atomic_json(path,sources)
    if not allowed:raise CollectionBlocked('Unknown source license')
    return info

def discover_pages(client,state):
    host=client.host;source=state['sources'].setdefault(host,{'prefix_index':0,'continue':{},'queue':[],'seen_pages':[],'seeded':False})
    if not source['seeded']:
        source['seeded']=True
        if host=='vi.wikipedia.org':
            data,_=client.get({'action':'query','prop':'info','inprop':'url','titles':'|'.join('Thảo luận:'+t for t in TOPICS)})
            source['queue'] += [p for p in data.get('query',{}).get('pages',[]) if not p.get('missing') and p.get('lastrevid')]
    while not source['queue'] and source['prefix_index']<len(PREFIXES[host]):
        prefix=PREFIXES[host][source['prefix_index']]
        data,_=client.get({'action':'query','generator':'allpages','gapnamespace':4,'gapprefix':prefix,'gaplimit':50,'prop':'info','inprop':'url',**source['continue']})
        source['queue'] += [p for p in data.get('query',{}).get('pages',[]) if p.get('lastrevid') and not p.get('missing')]
        source['continue']=data.get('continue',{})
        if not source['continue']:source['prefix_index']+=1
    while source['queue']:
        page=source['queue'].pop(0)
        if page['pageid'] in source['seen_pages']:continue
        return page
    if source['prefix_index']<len(PREFIXES[host]):return discover_pages(client,state)
    return None

def load_threads(data_root=DATA):
    return [load_json(p) for p in sorted((Path(data_root)/'threads').glob('*.json'))]

def write_progress(data_root,state,reason=None):
    root=Path(data_root);threads=load_threads(root);sources=load_json(root/'manifests/sources.json',{})
    complete=sum(len(threads)>=t for t in TARGETS)
    previous=load_json(root/'manifests/progress.json',{})
    value={'task':'T028','target_threads':200,'collected_threads':len(threads),'allowed_threads':len(threads),
     'comments':sum(len(t['comments']) for t in threads),'annotated_comments':previous.get('annotated_comments',0),'unlabeled_comments':max(0,sum(len(t['comments']) for t in threads)-previous.get('annotated_comments',0)),'uncertain_comments':previous.get('uncertain_comments',0),'batches_complete':complete,
     'current_batch':min(complete+1,4),'sources_allowed':[h for h,v in sources.items() if v['status']=='ALLOWED'],
     'sources_represented':dict(collections.Counter(t['source_platform'] for t in threads)),
     'sources_audited':len(sources),'invalid_candidates':state.get('invalid_candidates',0),'duplicates':state.get('duplicates',0),'pages_processed':state.get('pages_processed',0),
     'subtasks':{'A':'DONE','B':'COLLECTED_AWAITING_HUMAN_QUALITY' if len(threads)>=200 else 'BLOCKED' if reason else 'IN_PROGRESS',
       'C':'IMPLEMENTED_HUMAN_PRIVACY_REVIEW_REQUIRED','D':'IMPLEMENTED' if (Path(__file__).parent/'review_ui/index.html').exists() else 'IN_PROGRESS','E':'IMPLEMENTED' if (Path(__file__).parent/'store.py').exists() else 'IN_PROGRESS','F':'BLOCKED_HUMAN_LABELS_AND_PRIVACY_REVIEW'},
     'collection_blocker':reason,'training_performed':False,'evaluation_locked':False,'resume_state':'raw/collector_state.json'}
    atomic_json(root/'manifests/progress.json',value)
    return value

def recover_batch_manifests(root):
    # Recovery after interruption between an atomic thread write and manifest write.
    root=Path(root);found={t['thread_id']:t for t in load_threads(root)}
    state=load_json(root/'raw/collector_state.json',{});order=state.get('accepted_order',[])
    order += [tid for tid in sorted(found) if tid not in order]
    for index,total in enumerate(TARGETS):
        path=root/'batches'/('batch_'+str(index+1).zfill(2))/'manifest.json'
        if len(found)<total or path.exists():continue
        start=0 if index==0 else TARGETS[index-1];ids=[tid for tid in order if tid in found][start:total]
        atomic_json(path,{'batch':index+1,'target_total':total,'new_threads':len(ids),'thread_ids':ids,
          'checksums':{tid:sha_file(root/'threads'/(tid+'.json')) for tid in ids},
          'data_origin':'real','labels':'UNLABELED','status':'COLLECTED_NOT_EVALUATION_LOCKED','recovered_after_interruption':True})
        from .validation import write_quality
        write_quality(root,report_path=path.parent/'QUALITY_REPORT.md')

def collect(data_root=DATA,contact=None,through_batch=4,max_pages=120,max_requests=300,max_seconds=900,interval=1.0,client_factory=ApiClient):
    root=Path(data_root);root.mkdir(parents=True,exist_ok=True)
    policy=load_json(root/'manifests/collection_policy.json',{})
    if policy.get('collection_enabled') is False:
        return {'status':'BLOCKED','reason':policy.get('reason','Collection paused by user'),'threads':len(load_threads(root)),
                'collection_paused':True,'network_requests':0}
    if (root/'manifests/evaluation_lock.json').exists():return {'status':'EVALUATION_LOCKED','threads':len(load_threads(root))}
    if len(load_threads(root))>=TARGETS[through_batch-1]:
        recover_batch_manifests(root)
        return {'status':'COLLECTED','threads':len(load_threads(root)),'resume':'target already present; no network request'}
    recover_batch_manifests(root)
    state_path=root/'raw/collector_state.json';state=load_json(state_path,{'sources':{},'pending':[],'pages_processed':0,'invalid_candidates':0,'duplicates':0,'errors':[]})
    try:contact=validate_contact(contact or os.environ.get('SHIELDVI_COLLECTOR_CONTACT',''))
    except CollectionBlocked as exc:
        state['collection_blocker']=str(exc);atomic_json(state_path,state);write_progress(root,state,str(exc));atomic_json(root/'batches/batch_01/blocked_attempt.json',{'status':'BLOCKED','new_threads':0,'target_new_threads':20,'reason':str(exc),'attempted_at':now()});return {'status':'BLOCKED','reason':str(exc),'threads':len(load_threads(root))}
    ua='ShieldVIResearchBot/0.2 ('+contact+') Python-urllib'
    clients={h:client_factory(h,root/'raw/cache',ua,interval=interval,max_requests=max_requests) for h in HOSTS}
    active=[]
    for h,c in clients.items():
        try:audited_source(c,root);active.append(h)
        except CollectionBlocked as exc:state['errors'].append({'source':h,'kind':str(exc),'at':now()})
    if not active:
        atomic_json(state_path,state);write_progress(root,state,'No audited ALLOWED source accessible');return {'status':'BLOCKED','threads':len(load_threads(root))}
    anon=Pseudonymizer(root);found={t['thread_id']:t for t in load_threads(root)};order=state.get('accepted_order',[]);order += [tid for tid in sorted(found) if tid not in order];threads=[found[tid] for tid in order if tid in found];state['accepted_order']=[t['thread_id'] for t in threads];byid={t['thread_id'] for t in threads};fingerprints={comparison(thread_text(t)) for t in threads}
    limit=TARGETS[through_batch-1];started=time.monotonic();pages_this_run=0;pointer=0;blocked=None;exhausted=set()
    while len(threads)<limit:
        if pages_this_run>=max_pages or time.monotonic()-started>=max_seconds or sum(c.requests for c in clients.values())>=max_requests:
            blocked='Bounded page/request/time budget reached; resume checkpoint retained';break
        if not state['pending']:
            available=[h for h in active if h not in exhausted]
            if not available:blocked='Audited source page queues exhausted';break
            h=available[pointer%len(available)];pointer+=1;page=None
            try:
                page=discover_pages(clients[h],state)
                if page is None:exhausted.add(h);continue
                # Never visit personal User/User-talk namespaces or invent comments from edit summaries.
                if page.get('ns') in (2,3):continue
                response,response_hash=clients[h].get({'action':'discussiontoolspageinfo','page':page['title'],'oldid':page['lastrevid'],'prop':'threaditemshtml','threaditemsflags':'excludesignatures'})
                candidates=extract_threads(response,page,h,anon,response_hash)
                accepted_on_page=0
                for candidate in candidates:
                    q=structural_quality(candidate)
                    reason=None
                    if q['errors']:reason='schema_or_pii'
                    elif not 10<=len(candidate['comments'])<=30:reason='outside_preferred_length'
                    elif any(len(c['text'])>8000 for c in candidate['comments']):reason='oversized_comment_for_ShieldVI_no_truncation'
                    elif not vietnamese_candidate(candidate):reason='vietnamese_sampling_heuristic_not_met'
                    elif accepted_on_page>=15:reason='page_cap_for_sampling_diversity'
                    if reason:
                        state['invalid_candidates']+=1;state.setdefault('rejection_reasons',{}).setdefault(reason,0);state['rejection_reasons'][reason]+=1;continue
                    path=root/'anonymized/candidates'/(candidate['thread_id']+'.json');atomic_json(path,candidate)
                    state['pending'].append(candidate['thread_id']);accepted_on_page+=1
                pages_this_run+=1;state['pages_processed']+=1;state['sources'][h]['seen_pages'].append(page['pageid'])
            except (CollectionBlocked,ValueError,KeyError,TypeError) as exc:
                state['errors'].append({'source':h,'kind':type(exc).__name__,'reason_code':str(exc).split('\n')[0][:120] if isinstance(exc,CollectionBlocked) else 'source_schema_rejected','at':now()})
                if isinstance(exc,CollectionBlocked):
                    if page is not None:state['sources'][h]['queue'].insert(0,page)
                    exhausted.add(h)
            atomic_json(state_path,state)
        while state['pending'] and len(threads)<limit:
            tid=state['pending'].pop(0);path=root/'anonymized/candidates'/(tid+'.json');t=load_json(path)
            if not t or tid in byid:continue
            key=comparison(thread_text(t))
            if key in fingerprints or any(near_similarity(thread_text(t),thread_text(old))>=.9 for old in threads):state['duplicates']+=1;continue
            # Stable IDs and atomic files make resume safe even after interrupted state writes.
            atomic_json(root/'threads'/(tid+'.json'),t);threads.append(t);byid.add(tid);fingerprints.add(key)
            state['accepted_order']=[x['thread_id'] for x in threads]
            atomic_json(state_path,state);write_progress(root,state)
            if len(threads) in TARGETS:
                batch=TARGETS.index(len(threads))+1;start=0 if batch==1 else TARGETS[batch-2]
                manifest={'batch':batch,'target_total':len(threads),'new_threads':len(threads)-start,'thread_ids':[x['thread_id'] for x in threads[start:]],
                  'checksums':{x['thread_id']:sha_file(root/'threads'/(x['thread_id']+'.json')) for x in threads[start:]},'data_origin':'real','labels':'UNLABELED','status':'COLLECTED_NOT_EVALUATION_LOCKED'}
                atomic_json(root/'batches'/('batch_'+str(batch).zfill(2))/'manifest.json',manifest)
                from .validation import write_quality
                write_quality(root,report_path=root/'batches'/('batch_'+str(batch).zfill(2))/'QUALITY_REPORT.md')
                print('BATCH',batch,'threads',len(threads),'comments',sum(len(x['comments']) for x in threads),flush=True)
    state['collection_blocker']=blocked;atomic_json(state_path,state);progress=write_progress(root,state,blocked)
    from .validation import write_quality
    write_quality(root)
    return {'status':'COLLECTED' if len(threads)>=limit else 'PARTIAL_BLOCKED','threads':len(threads),'comments':progress['comments'],'blocker':blocked}

def main():
    p=argparse.ArgumentParser(description='T028 permitted real Wikimedia discussions only; requires operator contact.')
    p.add_argument('--through-batch',type=int,choices=range(1,5),default=4);p.add_argument('--max-pages',type=int,default=120);p.add_argument('--max-requests',type=int,default=300);p.add_argument('--max-seconds',type=int,default=900);p.add_argument('--interval',type=float,default=1.0)
    args=p.parse_args()
    if not 1<=args.max_pages<=500 or not 1<=args.max_requests<=1000 or not 1<=args.max_seconds<=3600 or args.interval<.5:p.error('Bounded budgets required; interval >=0.5s')
    result=collect(through_batch=args.through_batch,max_pages=args.max_pages,max_requests=args.max_requests,max_seconds=args.max_seconds,interval=args.interval)
    print(json.dumps(result,ensure_ascii=True));return 0 if result['status']=='COLLECTED' else 2
