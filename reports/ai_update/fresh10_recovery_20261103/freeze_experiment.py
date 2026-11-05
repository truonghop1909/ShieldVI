import csv,json,sys
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
from import_and_audit import progress
lock=P/'experiment_lock.json'
if lock.exists():raise FileExistsError('Experiment already frozen')
refs=list(csv.DictReader((R/'datasets/fixtures/fresh10_regression_v1/expected_reference_labels.csv').open(encoding='utf-8-sig',newline='')))
audit={1:['c06','c11','c15'],6:['c07','c11','c15'],3:['c07'],5:['c09'],8:['c13']}
with (P/'reference_review_notes.csv').open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=['thread_id','comment_id','original_reference','reference_changed','review_status','note']);w.writeheader()
    for number,ids in audit.items():
        for row in refs:
            if row['thread_id'].startswith('SHIELDVI_FRESH10_'+str(number).zfill(2)+'_') and row['comment_id'] in ids:
                w.writerow({'thread_id':row['thread_id'],'comment_id':row['comment_id'],'original_reference':row['expected_label'],'reference_changed':False,
                    'review_status':'SYNTHETIC_REFERENCE_PENDING_OWNER_ADJUDICATION','note':'Sarcasm/competence, conduct criticism or personal humiliation depend on context. Keep reference fixed and include every error; no human gold. No new broad rule for coaching/cho_phep_mau or group accountability.'})
atomic_json(lock,{'frozen_at':datetime.now(timezone.utc).isoformat(),
    'experimental_module_sha256':file_sha(R/'services/moderation-ai/app/experiments/fresh10_v6.py'),
    'import_manifest_sha256':file_sha(R/'datasets/fixtures/fresh10_regression_v1/manifest.json'),
    'existing_readiness_lock_sha256':file_sha(R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json'),
    'promotion_allowed':False,'training_allowed':False,'new_holdout_authored_after_lock':True,
    'post_holdout_rule_tuning_allowed':False,'reference_labels_changed':False})
progress('DEVELOPMENT_VALIDATED_AND_EXPERIMENT_FROZEN','Opt-inv6: Fresh10TP18/FP1/FN4/TN172,MacroF1.931861,target16/22,repeated6/7,P1/R.8571,evidence15/15precision and15/19coverage; Test03/Test08full evidence. New-label-errors0. Old890regression metrics/target/repeated exactly unchanged. Initial development regressions retained in development_v1, fixed generally before freeze. Nine reference-review notes preserve originallabels. v5/default/readiness unchanged; experiment now frozen before new holdout authoring.')
print('Experiment frozen; reference labels unchanged')
