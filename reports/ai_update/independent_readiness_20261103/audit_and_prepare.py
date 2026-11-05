"""Local inventory, permitted-source research record and preparation; never train."""
import json,re,shutil,sys
from collections import defaultdict
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from real_dataset.core import atomic_json,sha_file,now
from real_dataset.collector import collect
from real_dataset.validation import write_quality
from real_dataset.leakage import development_index
from prepare_t029_training import prepare
from train_t029_candidate import run

inventory=[];candidates=[];references=[];directories=defaultdict(list)
excluded=('synthetic_conversations','context_recovery_v1','genz_regression','raw','processed','prepared')
for name in ('datasets','fixtures','tests','docs'):
    root=R/name
    if not root.exists():continue
    for path in root.rglob('*'):
        if not path.is_file() or any(x in path.parts for x in ('node_modules','__pycache__')):continue
        rel=path.relative_to(R).as_posix()
        if path.suffix in ('.json','.jsonl','.csv'):inventory.append({'file':rel,'bytes':path.stat().st_size})
        if path.suffix=='.md' and path.stat().st_size<300000:
            text=path.read_text(encoding='utf-8-sig',errors='replace')
            if re.search(r'\b30\s*(?:thread|hội thoại)|\b313\s*(?:comment|bình luận)',text,re.I):references.append(rel)
        if path.suffix!='.json' or path.stat().st_size>3_000_000 or any(x in path.parts for x in excluded):continue
        # Inspect only candidate collection/manifest structures, not flat classification datasets.
        if not re.search(r'30|313|wiki|pilot|thread|conversation|manifest',rel,re.I):continue
        try:value=json.loads(path.read_text(encoding='utf-8-sig'))
        except (ValueError,OSError):continue
        if isinstance(value,dict) and isinstance(value.get('comments'),list):directories[path.parent].append(value)
        rows=value if isinstance(value,list) else value.get('threads',value.get('conversations')) if isinstance(value,dict) else None
        if isinstance(rows,list) and len(rows)==30 and all(isinstance(t,dict) and isinstance(t.get('comments'),list) for t in rows):
            candidates.append({'file':rel,'threads':30,'comments':sum(len(t['comments']) for t in rows),'source_status':'UNVERIFIED'})
for directory,rows in directories.items():
    if len(rows)==30:candidates.append({'directory':directory.relative_to(R).as_posix(),'threads':30,'comments':sum(len(t['comments']) for t in rows),'source_status':'UNVERIFIED'})
found=[c for c in candidates if c['comments']==313]
atomic_json(P/'dataset_inventory.json',{'roots':['datasets/','fixtures/ (if present)','tests/','docs/'],'files':inventory,'documentary_mentions':references,'candidate_collections':candidates})
atomic_json(P/'old_30_audit.json',{'old_30_threads_313_comments':'FOUND_UNVERIFIED' if found else 'NOT_FOUND',
 'eligible_real_old_threads':0,'matches':found,'searched_file_inventory':len(inventory),'documentary_mentions_are_not_corpus_evidence':True,
 'known_synthetic':[{'threads':100,'comments':1495,'path':'datasets/review/conversations_100'},
 {'threads':200,'comments':2048,'path':'datasets/synthetic_conversations'},
 {'threads':500,'comments':5115,'path':'datasets/synthetic_conversations/genz_v2'},
 {'threads':5,'comments':150,'path':'datasets/fixtures/genz_regression'}],
 'no_user_path_request_required':True,'no_candidate_reclassified_as_real':True})

source_candidates=[
 {'name':'Wikimedia vi talk','primary_urls':['https://www.mediawiki.org/wiki/API:Etiquette','https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy/en'],
  'observed_license':'Existing metadata: CC-BY-SA-4.0; collector still rechecks API rights receipt before content',
  'status':'PAUSED_BY_USER','reason':'No operator contact; user explicitly refuses further contact requests and browser impersonation. No collection attempted.'},
 {'name':'ViHOS','primary_urls':['https://github.com/phusroyal/ViHOS','https://raw.githubusercontent.com/phusroyal/ViHOS/master/LICENSE'],
  'observed_license':'MIT repository license; not assumed to establish every underlying source-comment right',
  'status':'NOT_ELIGIBLE_FOR_T028','reason':'Existing flat span/comment dataset, no verified multi-party thread graph/provenance; already in development inventory. No new download.'},
 {'name':'ViHSD','primary_urls':['https://github.com/sonlam1102/vihsd'],
  'observed_license':'No clear dataset-use grant located in inspected primary repository pages',
  'status':'HOLD_RIGHTS_AND_SCHEMA','reason':'Comment-level CLEAN/OFFENSIVE/HATE release, not verified complete threads with parent/user/time and current source permission.'},
 {'name':'ViCTSD','primary_urls':['https://github.com/tarudesu/ViCTSD'],
  'observed_license':'Local user copy explicitly not reverified in datasets/manifest.json',
  'status':'NOT_INDEPENDENT_T028','reason':'Already supervised train/validation/test classification data; cannot assemble comments into invented new real threads.'},
 {'name':'ViLexNorm','primary_urls':['https://github.com/ngxtnhi/ViLexNorm'],
  'observed_license':'CC-BY-NC-SA-4.0 recorded with primary README hash in local manifest',
  'status':'SCHEMA_UNSUITABLE','reason':'Normalization pairs, not source-verifiable multi-party threads; already a development source.'},
 {'name':'mDIA Vietnamese','primary_urls':['https://github.com/DoctorDream/mDIA','https://huggingface.co/datasets/SEACrowd/mdia/blob/main/README.md'],
  'observed_license':'SEACrowd wrapper declares CC-BY-4.0; original README citation has paper copyright, not a verified dataset grant',
  'status':'HOLD_UPSTREAM_RIGHTS_AND_PROVENANCE','reason':'Parent-response pairs do not establish full10–30comment threads, stable actors/timestamps/source URLs. No raw Reddit scrape or reconstruction attempted.'}]
atomic_json(P/'source_candidates.json',{'checked_at':now(),'method':'Primary documentation/repository/license metadata browsing only; no comment corpus downloaded',
 'sources':source_candidates,'accepted_new_threads':0,'accepted_new_comments':0,'source_rights_not_inferred_from_public_visibility':True})
real=R/'datasets/real_conversations'
exclusions=real/'manifests/development_exclusions.json'
shutil.copy2(exclusions,P/'development_exclusions.before.json')
known=json.loads(exclusions.read_text(encoding='utf-8'));refs=known['source_records'];paths={r['path'] for r in refs}
new_refs=[(R/'datasets/synthetic_conversations/genz_v2'/name,'threads_jsonl') for name in ('train_threads.jsonl','development_threads.jsonl')]
new_refs += [(path,'thread_json') for path in (R/'datasets/fixtures/context_recovery_v1/dashboard_threads').glob('*.json')]
for path,fmt in new_refs:
    rel=path.relative_to(R).as_posix()
    if rel not in paths:refs.append({'path':rel,'sha256':sha_file(path),'format':fmt,'purpose':'Exclude all synthetic development/training text from future independent cohort'});paths.add(rel)
known['updated_at']=now();known['scope_note']='Includes GenZ500 train/development and12context fixtures; no label/source text changed.'
atomic_json(exclusions,known)
ids,texts,groups=development_index(real)
atomic_json(P/'leakage_audit.json',{'status':'PASS','source_records':len(refs),'blocked_thread_ids':len(ids),'blocked_long_text_hashes':len(texts),
 'whole_thread_comparison_groups':len(groups),'manifest_sha256':sha_file(exclusions),'actual_real_threads_checked':0,
 'new_real_leakage_result':'NOT_APPLICABLE_EMPTY_DATASET','short_common_utterance_limitation':'Exact comment hashes apply only to>=80chars; whole-thread near comparison also applies.'})
paused=collect(real);assert paused['status']=='BLOCKED' and paused['network_requests']==0
atomic_json(P/'collector_guard.json',paused)
quality=write_quality(real);atomic_json(P/'real_quality.json',quality)
progress=json.loads((real/'manifests/progress.json').read_text(encoding='utf-8'))
progress.update(task='T028',current_real_acceptance_status='BLOCKED',collection_blocker=paused['reason'],collected_threads=quality['actual_threads'],
 comments=quality['comments'],annotation_rounds_required=2,independent_evaluation_ready=False,t028_real_acceptance_ready=False)
atomic_json(real/'manifests/progress.json',progress)

# T029 preparation only: real independent conditions and explicit resource approval remain required.
cfg=json.loads((R/'configs/t029_genz500_cpu_head_r05.json').read_text(encoding='utf-8'))
base=Path(json.loads((R/'reports/ai_update/T029/genz500_cpu_prepared/manifest.json').read_text(encoding='utf-8'))['base_model_path'])
for key in ('cpu_threads','feature_batch_size','distillation_weight','maximum_external_cost','base_reference_id'):cfg.pop(key,None)
cfg.update(run_id='T029_real200_preparation_not_authorized',base_model=str(base),original_v1=True,
 output_dir=str(R/'models/candidates/T029_real200_future_not_authorized'),training_strategy='full_finetune_gpu',
 evaluation_protocol='real_independent',resource='GPU_PENDING_EXPLICIT_APPROVAL',max_training_seconds=3600,
 approved_for_execution=False,approval_status='BLOCKED_REAL200_AND_NEW_EXPLICIT_APPROVAL',estimated_cost='UNKNOWN_NOT_APPROVED',
 test_scoring='No evaluation/train execution in this preparation; independent real test remains unavailable')
config=R/'configs/t029_real_independent_preparation.json';atomic_json(config,cfg)
info=prepare(config,P/'prepared',base)
preflight=run(config,P/'prepared',base,execute=False)
assert preflight['status']=='BLOCKED' and not preflight['training_performed'] and not Path(cfg['output_dir']).exists()
atomic_json(P/'T029_preflight.json',preflight)
state=json.loads((P/'progress.json').read_text(encoding='utf-8'));state['completed']=['PartA implementation/focused tests; paired metrics pending final regression','old30 audit','source metadata audit','collector pause guard','manual intake/review readiness','leakage index expansion','T029 preparation only'];state['next']='Full tests, isolated integration E2E, registry smoke, reviewer startup and technical report'
atomic_json(P/'progress.json',state)
with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as f:
 f.write('\n\nCurrent independent-readiness progress: old30/313 '+('FOUND_UNVERIFIED' if found else 'NOT_FOUND')+'; real valid0, collector paused/no network.6source options audited, none admitted as T028. Manual quarantine/UI and same-reviewer Round2 freshness tests pass; leakage boundary expanded toGenZ500+context12. T029 config/data preparation actual'+str(info['total_train_rows'])+'rows, preflightBLOCKED(real/approval/GPU), no training. Evidence reports/ai_update/independent_readiness_20261103/.\n')
print(json.dumps({'old30':'FOUND_UNVERIFIED' if found else 'NOT_FOUND','inventory_files':len(inventory),'real_threads':quality['actual_threads'],
 'collector_network_requests':paused['network_requests'],'sources_audited':len(source_candidates),'leakage_sources':len(refs),
 'prepared_rows':info['total_train_rows'],'T029':preflight['status'],'training_performed':False}))
