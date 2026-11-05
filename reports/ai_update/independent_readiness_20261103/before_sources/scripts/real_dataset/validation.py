import collections,json,re,sqlite3
from pathlib import Path
from .core import DATA,RealThread,structural_quality,thread_text,near_similarity,comparison,load_json,atomic_json,sha_file,now

def validate_dataset(data_root=DATA):
    root=Path(data_root);files=sorted((root/'threads').glob('*.json'));threads=[];errors=[];warnings=[];ids=set();texts=collections.Counter();sources=load_json(root/'manifests/sources.json',{})
    receipts={sha_file(p) for p in (root/'raw/cache').glob('*.json')}
    for p in files:
        try:
            t=load_json(p);RealThread.model_validate(t)
            if t['thread_id'] in ids:raise ValueError('duplicate_thread_id')
            ids.add(t['thread_id']);q=structural_quality(t)
            if sources.get(t['source_platform'],{}).get('status')!='ALLOWED':q['errors'].append('source_not_audited_allowed')
            if t['source_response_sha256'] not in receipts:q['errors'].append('missing_source_response_receipt')
            for code in q['errors']:errors.append({'thread_id':t['thread_id'],'code':code})
            for code in q['warnings']:warnings.append({'thread_id':t['thread_id'],'code':code})
            threads.append(t);texts.update(comparison(c['text']) for c in t['comments'])
        except (ValueError,KeyError,TypeError):errors.append({'file':p.name,'code':'invalid_thread_schema'})
    near=[]
    for i,t in enumerate(threads):
        for other in threads[i+1:]:
            if near_similarity(thread_text(t),thread_text(other))>=.9:near.append([t['thread_id'],other['thread_id']])
    for pair in near:errors.append({'thread_ids':pair,'code':'near_duplicate_threads'})
    allcomments=[c for t in threads for c in t['comments']];whole='\n'.join(c['text'] for c in allcomments)
    style={'teencode_comment_count':sum(bool(re.search(r'(?i)\b(?:ko|khum|mik|đc|bt|vkl|n0ob|l0ser)\b',c['text'])) for c in allcomments),
      'emoji_comment_count':sum(bool(re.search('[\U0001F300-\U0001FAFF]',c['text'])) for c in allcomments),
      'english_slang_comment_count':sum(bool(re.search(r'(?i)\b(?:bro|cringe|noob|loser|npc|sorry|hello|thanks)\b',c['text'])) for c in allcomments),
      'method':'bounded lexical heuristics, not reliable language/topic/abuse labels'}
    annotations={'labeled':0,'unlabeled':len(allcomments),'uncertain':0,'round2_done':0,'label_distribution':{}}
    dbpath=root/'annotations/reviews.sqlite3'
    if dbpath.exists():
        from .store import ReviewStore
        store=ReviewStore(root);allrows=store.list_reviews();labels={}
        latest={}
        for r in allrows:
            key=(r['thread_id'],r['comment_id'])
            if key not in latest or r['updated_at']>latest[key]['updated_at']:latest[key]=r
        labels={key:r['label'] for key,r in latest.items() if r['label'] is not None}
        annotations={'labeled':len(labels),'unlabeled':len(allcomments)-len(labels),'uncertain':sum(v=='UNCERTAIN' for v in labels.values()),
          'round2_done':sum(r['annotation_status']=='ROUND2_DONE' for r in allrows),'label_distribution':dict(collections.Counter(labels.values()))}
        errors+=store.quality_errors()
    lock=load_json(root/'manifests/evaluation_lock.json',{})
    locked_ready=False
    if lock:
        export=root/'annotations/evaluation_export.jsonl'
        actual_checksums={t['thread_id']:sha_file(root/'threads'/(t['thread_id']+'.json')) for t in threads}
        locked_ready=bool(threads and not errors and lock.get('evaluation_eligible') and actual_checksums==lock.get('thread_checksums')
          and dbpath.exists() and sha_file(dbpath)==lock.get('annotations_sha256') and export.exists() and sha_file(export)==lock.get('export_sha256'))
        if not locked_ready:errors.append({'code':'evaluation_snapshot_missing_or_changed'})
    result={'generated_at':now(),'target_threads':200,'actual_threads':len(threads),'comments':len(allcomments),
      'users':len({c['user_id'] for c in allcomments if c['user_id']}),'source_counts':dict(collections.Counter(t['source_platform'] for t in threads)),
      'sources_audited_allowed':[s for s,v in sources.items() if v['status']=='ALLOWED'],'topic_count':len({t['topic'] for t in threads}),
      'length_distribution':dict(collections.Counter(len(t['comments']) for t in threads)),
      'duplicate_comment_texts':sum(v-1 for v in texts.values() if v>1),'near_duplicate_threads':len(near),
      'recognized_pii_remaining':sum(x['code']=='recognized_pii_remaining' for x in errors),
      'errors':errors,'warnings':warnings,'annotations':annotations,'style_heuristics':style,'evaluation_locked':(root/'manifests/evaluation_lock.json').exists(),
      'dataset_status':'EMPTY_DATASET' if not threads else 'LOCKED_VERIFIED_SOLO' if locked_ready else 'CANDIDATE_NOT_LOCKED','independent_evaluation_ready':locked_ready,'training_performed':False,'representativeness_warning':'Wikimedia community/talk discussions differ from general social media. No coverage/category/toxicity claims without human review.'}
    return result

def write_quality(data_root=DATA,report_path=None):
    root=Path(data_root);report=validate_dataset(root);atomic_json(root/'reports/quality.json',report)
    lines=['# QUALITY_REPORT — T028','','Generated: '+report['generated_at'],'',
      f"Real conversations: **{report['actual_threads']}/200**; comments: **{report['comments']}**; users: **{report['users']}**.",
      'Represented sources: '+json.dumps(report['source_counts'],ensure_ascii=False),
      'Audited ALLOWED sources: '+str(len(report['sources_audited_allowed'])),
      'Dataset status: '+report['dataset_status']+'; independent evaluation ready: '+str(report['independent_evaluation_ready']),
      'Errors: '+str(len(report['errors']))+'; warnings: '+str(len(report['warnings'])),
      'Duplicate comment text occurrences: '+str(report['duplicate_comment_texts'])+'; near-duplicate threads: '+str(report['near_duplicate_threads']),
      'Human labels: '+json.dumps(report['annotations'],ensure_ascii=False),
      'Style heuristics: '+json.dumps(report['style_heuristics'],ensure_ascii=False),'',
      'A successful structural check does not establish sufficient data or human labels. Evaluation becomes locked/ready only after manual labels, source/privacy/completeness checks and leakage validation pass. Unknown authors/times are never invented; relationships are explicitly source-parser-derived. Raw data and annotation DB are ignored by Git.',
      report['representativeness_warning'],'','Detailed machine report: reports/quality.json. No ViSoBERT predictions were requested or shown in first-pass labeling.','']
    path=Path(report_path) if report_path else root/'QUALITY_REPORT.md';path.parent.mkdir(parents=True,exist_ok=True);path.write_text('\n'.join(lines),encoding='utf-8');return report
