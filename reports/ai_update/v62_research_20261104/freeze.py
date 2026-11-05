import json,sys
from pathlib import Path
from datetime import datetime,timezone
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(P))
from synthetic_data.pipeline import atomic_json,file_sha
from verify_ai_readiness_lock import verify_lock
from progress import record

if __name__=='__main__':
    path=P/'V62_LOCK.json';assert not path.exists()
    ready_path=R/'reports/ai_update/stabilization_20261103/READINESS_LOCK_T028_v2.json'
    ready=verify_lock(ready_path);assert ready['status']=='PASS';atomic_json(P/'readiness_before_challenge.json',ready)
    results=json.loads((P/'frozen_development/summary.json').read_text())
    assert all(not r['new_label_errors'] for r in results.values())
    source=['services/moderation-ai/app/experiments/research_v62.py','services/moderation-ai/app/experiments/fresh10_v6.py',
        'services/moderation-ai/app/context_signals.py','services/moderation-ai/app/target_signals.py',
        'services/moderation-ai/app/signal_engine.py','services/moderation-ai/app/context_assessment.py',
        'tests/test_research_v62.py','tests/test_nov10_adjudication_export.py','scripts/evaluate_research_v62.py']
    atomic_json(path,{'frozen_at':datetime.now(timezone.utc).isoformat(),'version':'v6.2-research','status':'EXPERIMENTAL_NOT_PROMOTED',
        'files':{name:file_sha(R/name) for name in source},'readiness_lock_sha256':file_sha(ready_path),
        'r06_weights_sha256':file_sha(R/'models/candidates/T029_synthetic_only_head_cpu_20261103_r06/model.safetensors'),
        'development_summary_sha256':file_sha(P/'frozen_development/summary.json'),'post_inference_tuning_allowed':False,
        'new_challenge_authoring_after_this_lock':True,'training_allowed':False,'default_activation_allowed':False,'human_gold':False})
    record('INDIRECT_CONTROLS_VERIFIED_AND_V62_FROZEN','Separatev6.2 quote fixes/control expectationsPASS;45targeted tests incl43processor/2adjudicationPASS.7developmentcohorts no new labelerrors. NOV10 Macro.694160→.719137,target0→2/22,repeated0→1/8; Fresh10/old890 unchanged. Otherseen challenge gains retained; no reference edits. Initial nounmask/safe-cue and content-view failures fixed and archived before freeze. HTMLv1JS escape failure retained; adjudication_v2 parse/emptyexportPASS,24fullcontexts/blankownerdecisions/nohumanlabels. V62_LOCK now freezes code/tests/model/reference/readiness before authoring a new challenge. Default/runtime/V1/r06/0.41 unchanged; no training/deploy.')
    print('V62_FROZEN_BEFORE_NEW_CHALLENGE_AUTHORING')
