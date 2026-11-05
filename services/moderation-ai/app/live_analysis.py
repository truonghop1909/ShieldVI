"""Default-v5 incremental neural cache with bounded deterministic re-analysis."""
import hashlib,math,re,threading,time
from collections import OrderedDict
from datetime import datetime,timezone
from pathlib import Path
from .schemas import AnalyzeRequest
from .signal_engine import analyze_thread_v2
from .live_analysis_contract import LiveModerationResponse
from .moderation_adapter import LEXICON_VERSION
from . import context_signals as context_rules

def reported_predicates_only(text):
    """Subtractive instance gate, not a CLEAN/TOXIC or raw-score rewrite.

    A known v5 predicate must have an unreported occurrence before it can
    support a new attack instance. Unknown predicates remain with v5.
    """
    s=context_rules.context_view(text);quotes=list(context_rules.QUOTED.finditer(s));breaks=list(context_rules.BREAK.finditer(s));found=False
    patterns=(context_rules.ATTACK,context_rules.DISPARAGEMENT,context_rules.INDIRECT)
    for pattern in patterns:
        for match in pattern.finditer(s):
            found=True;left=max((b.end() for b in breaks if b.end()<=match.start()),default=0)
            prefix=s[left:match.start()];q=next((q for q in quotes if q.start()<=match.start() and match.end()<=q.end()),None)
            after=s[q.end():q.end()+55] if q else s[match.end():match.end()+55]
            endorsed=bool(context_rules.ENDORSE.search(after)) and not re.search(r'\b(?:khong|chang).{0,16}\b(?:dung|chuan|xung dang)\b',after)
            if context_rules.PAST_REPORT.search(prefix) and not endorsed:continue
            if q is not None:
                before=s[left:q.start()] if left<=q.start() else s[:q.start()]
                assigned=bool(re.search(r'\b(?:may|m|ban|b|you|cau)\b.{0,24}\b(?:la|are)\s*$',before))
                if not assigned and not endorsed:continue
            return False
    return found

def model_fingerprint(predictor):
    config=getattr(getattr(predictor,'model',None),'config',None)
    path=Path(getattr(config,'_name_or_path',''))
    if not path.is_dir():raise ValueError('Loaded checkpoint identity unavailable')
    digest=hashlib.sha256()
    for name in ('model.safetensors','config.json','tokenizer.json','threshold_config.json'):
        file=path/name
        if not file.is_file():raise ValueError('Checkpoint identity incomplete')
        digest.update(name.encode())
        with file.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''):digest.update(chunk)
    return digest.hexdigest()

class IncrementalAnalyzer:
    def __init__(self,predictor,fingerprint=None,capacity=2048,horizon_seconds=1800,processor='default-v5',allow_experimental=False):
        if predictor.threshold!=.41:raise ValueError('Incompatible threshold')
        if not 51<=capacity<=10000 or not 60<=horizon_seconds<=86400:raise ValueError('Invalid analysis bounds')
        if processor not in {'default-v5','experimental-v6.2'} or (processor!='default-v5' and not allow_experimental):
            raise ValueError('Experimental processor requires explicit isolated shadow authorization')
        self.predictor=predictor;self.threshold=.41;self.name=predictor.name
        self.fingerprint=fingerprint or model_fingerprint(predictor)
        self.capacity=capacity;self.horizon_seconds=horizon_seconds;self.processor=processor
        self.cache=OrderedDict();self.lock=threading.RLock();self.hits=0;self.misses=0

    def predict_scores(self,texts):
        keys=[hashlib.sha256(t.encode('utf-8')).hexdigest() for t in texts]
        missing={key:text for key,text in zip(keys,texts) if key not in self.cache}
        values=self.predictor.predict_scores(list(missing.values())) if missing else []
        if len(values)!=len(missing) or any(not math.isfinite(v) or not 0<=v<=1 for v in values):raise ValueError('Invalid raw model scores')
        for key,value in zip(missing,values):self.cache[key]=float(value)
        result=[self.cache[key] for key in keys]
        for key in keys:self.cache.move_to_end(key)
        while len(self.cache)>self.capacity:self.cache.popitem(last=False)
        self.misses+=len(missing);self.hits+=len(texts)-len(missing)
        return result

    def analyze(self,payload):
        with self.lock:
            start=time.perf_counter();hits,misses=self.hits,self.misses
            comments=[c.model_dump() for c in payload.context.recent_comments]+[{'comment_id':payload.content_id,'user_id':payload.user_id,
                'text':payload.text,'timestamp':payload.timestamp,'parent_id':payload.parent_id,'mentioned_user_ids':payload.mentioned_user_ids}]
            thread=AnalyzeRequest(thread_id=payload.context.post_id,profile='conservative',comments=comments)
            if self.processor=='default-v5':out=analyze_thread_v2(thread,self)
            else:
                from .experiments.research_v62 import analyze_thread_v62
                out=analyze_thread_v62(thread,self)
            by_id={c.comment_id:c for c in thread.comments};current=next(c for c in out['comments'] if c['comment_id']==payload.content_id)
            instances=[];report_gates={}
            for row in out['comments']:
                source=by_id[row['comment_id']];sig=row['analysis_signals'];target=sig['target_evidence']
                age=(payload.timestamp-source.timestamp).total_seconds()
                report_gates[source.comment_id]=reported_predicates_only(source.text)
                if sig['attack_instance_candidate'] and not report_gates[source.comment_id] and 0<=age<=self.horizon_seconds:
                    instances.append({'comment_id':source.comment_id,'actor_user_id':source.user_id,'target_user_id':row['directed_at_user_id'],
                        'timestamp':source.timestamp,'context_confidence':sig['attack_confidence'],'target_confidence':target['confidence'],
                        'target_method':target['method'],'target_evidence_ids':target['evidence_comment_ids']})
            valid={i['comment_id']:i for i in instances};evidence=[]
            for event in out['evidence']:
                ids=[cid for cid in event['evidence_comment_ids'] if cid in valid]
                times={by_id[cid].timestamp for cid in ids}
                if event['actor_user_id']==payload.user_id and payload.content_id in ids and len(ids)>=2 and len(times)>=2:
                    evidence.append({**event,'evidence_comment_ids':ids,'n_distinct_timestamps':len(times)})
            sig=current['analysis_signals'];target=sig['target_evidence']
            qualified=payload.content_id in valid
            directed=current['directed_at_user_id'] if qualified else None
            advisory={'reply_to_user_id':current['reply_to_user_id'],'directed_at_user_id':directed,
                'directed_attack_candidate':sig['directed_attack_candidate'],'base_attack_instance_candidate':sig['attack_instance_candidate'],
                'attack_instance_candidate':qualified,'instance_gate_reason':'v5_grounded' if qualified else 'reported_predicate_only' if report_gates[payload.content_id] else 'insufficient_context_or_target',
                'context_tags':sig['context_tags'],'context_cues':sig['context']['cues'],
                'assessment_label':current['moderation_assessment']['label'],'assessment_basis':current['moderation_assessment']['basis'],
                'policy_risk':current['policy_risk']['band'],'policy_executed':False}
            return LiveModerationResponse(schema_version='1.0',request_id=payload.request_id,content_id=payload.content_id,
                content_revision=payload.content_revision,model_name=out['model_name'],model_version=self.name,lexicon_version=LEXICON_VERSION,
                analyzed_at=datetime.now(timezone.utc),model_threshold=.41,toxicity_score=current['toxicity_score'],
                ai_label='TOXIC' if current['toxic_for_moderation'] else 'CLEAN',lexical_review_recommended=current['lexical_review_recommended'],
                directed_insult_candidate=current['directed_insult_candidate'],reported_or_apology_context=current['reported_or_apology_context'],
                lexical_signals=current['lexical_signals'],target_evidence={'target_user_id':directed,
                    'method':target['method'] if directed else 'live_instance_unconfirmed','confidence':target['confidence'] if directed else 'none'},
                suspected_repeated_harassment=bool(evidence),evidence=evidence,
                suggested_action='needs_review' if current['review_recommended'] or evidence else 'approve',decision_authority='advisory',
                limitations=['Bounded snapshot; outside-window evidence unavailable. Raw cache is per immutable loaded checkpoint.','Default-v5 advisory only, never executes visibility policy.'],
                conversation_signals={'processor':self.processor,'rules_version':out['rule_versions'],'model_fingerprint':self.fingerprint,
                    'current':advisory,'attack_instances':instances,'context_complete':payload.context.complete,
                    'horizon_seconds':self.horizon_seconds,'cached_texts':self.hits-hits,'neural_texts':self.misses-misses,
                    'analysis_ms':(time.perf_counter()-start)*1000})
