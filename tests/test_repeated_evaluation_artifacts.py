"""Integrity and metric accounting checks, never impose performance on AI labels."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'reports/ai_update/repeated_recovery_20261103'

def test_challenge_labels_locked_before_scoring_and_rules_remain_frozen():
    lock=json.loads((P/'frozen_rule_lock.json').read_text(encoding='utf-8'));manifest=R/'datasets/fixtures/repeated_holdout_20261103/manifest.json'
    evaluated=json.loads((P/'evaluation/evaluation_lock.json').read_text(encoding='utf-8'))
    assert evaluated['fresh_manifest_sha256']==hashlib.sha256(manifest.read_bytes()).hexdigest()
    for name,h in lock['rule_sha256'].items():assert hashlib.sha256((R/'services/moderation-ai/app'/name).read_bytes()).hexdigest()==h
    assert evaluated['human_gold'] is False and evaluated['training_performed'] is False

def test_three_models_ablation_metrics_share_population_and_count_every_error():
    data=json.loads((P/'evaluation/evaluation.json').read_text(encoding='utf-8'));assert data['raw_invariant'] and not data['training_performed']
    for model in data['metrics'].values():
        for variant in ('before','context_only','target_repeated_only','after'):
            for split,n in [('synthetic_validation',306),('synthetic_challenge',311),('fresh_synthetic_challenge',74)]:
                result=model[variant][split];c=result['classification']
                assert c['n']==n and sum(c[k] for k in ('tp','fp','tn','fn','abstained_clean','abstained_toxic'))==n
                assert c['confusion_matrix']==[[c['tn'],c['fp']],[c['fn'],c['tp']]]
                g=result['grounding']['repeated'];assert g['tp']+g['fn']==(2 if split=='synthetic_validation' else 5 if split=='synthetic_challenge' else 6)

def test_evidence_correctness_checks_full_actor_target_and_time_not_keyword_presence():
    data=json.loads((P/'evaluation/outputs.json').read_text(encoding='utf-8'));truth={}
    for p in (R/'datasets/fixtures/repeated_holdout_20261103').glob('REP_FRESH_*.json'):
        t=json.loads(p.read_text(encoding='utf-8'))
        for c in t['comments']:truth[(t['thread_id'],c['comment_id'])]=c
    for variants in data.values():
        for item in variants['after']:
            if item['split']!='fresh_synthetic_challenge':continue
            for e in item['output']['evidence']:
                refs=[truth[(item['output']['thread_id'],cid)] for cid in e['evidence_comment_ids']]
                assert len({c['timestamp'] for c in refs})>=2
                assert all(c['annotation']['label']=='TOXIC' and c['user_id']==e['actor_user_id'] and c['annotation']['directed_at_user_id']==e['target_user_id'] for c in refs)
