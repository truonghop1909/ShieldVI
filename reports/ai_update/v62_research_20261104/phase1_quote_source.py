"""Opt-in v6.2 research. Sealed v6.1 and default app are never mutated."""
import re,unicodedata
from collections import defaultdict
from datetime import timezone
from . import fresh10_v6 as old
from ..context_assessment import assess
from ..signal_engine import analyze_thread_v2
from ..target_signals import resolve_root_exchange
CONTEXT_VERSION='context-v6.2-research'
TARGET_VERSION='target-v6.2-research'
REPEATED_VERSION='repeated-v6.2-research'
NOUN_CAU=re.compile(r'\bcâu\b',re.I)
ASSIGN=re.compile(r'\b(?:may|m|b|ban|you|cau|ong|ba)\b.{0,24}\b(?:la|are)\s*$')
ATTRIBUTION=re.compile(r'\b(?:tac gia|nhan vat|nguoi (?:ay|do)|anh ay|chi ay|ho)\b.{0,24}\b(?:viet|noi|ghi|nhan|ke|goi|bao)\b|\b(?:trich|nguyen van|trong truyen|trong kich ban)\b')
NEGATED_ASSIGNMENT=re.compile(r'\b(?:khong|chang)(?: he)?(?: phai)?(?: la)?\s*$|\b(?:khong|chang) (?:phai|ai)\b.{0,35}$')

def views(text):
    nfc=unicodedata.normalize('NFC',text)
    noun_masked=NOUN_CAU.sub(lambda m:'z'*len(m.group()),nfc)
    masked=old.PLANTS.sub(lambda m:'z'*len(m.group()),noun_masked)
    masked=re.sub(r'(?iu)\b(?:ngủ|ngữ|ngự)\b','zzz',masked)
    # Trace positions share the exact normalized coordinate space used by
    # clause/target inference. Map expansions back to NFC, not UTF-8 bytes.
    offsets=[]
    for i,char in enumerate(masked):offsets.extend([[i,i+1]]*len(old.base.fold(char)))
    normalized=old.base.context_view(masked)
    assert len(offsets)==len(normalized)
    return nfc,noun_masked,normalized,offsets

def context_v62(text,participants=()):
    nfc,masked,s,offsets=views(text)
    ctx,trace=old.context_v6(masked,participants);ctx.version=CONTEXT_VERSION
    if masked!=nfc:
        # The noun is not an addressee, but remains meaningful in cues such as
        # "câu này ... xúc phạm". Keep those existing non-attack semantics.
        original,_=old.context_v6(nfc,participants)
        ctx.tags=list(dict.fromkeys(ctx.tags+[tag for tag in original.tags if tag in old.SAFE_TAGS]))
    trace.update(normalized_view=s,normalized_to_nfc=offsets,coordinate_system='NFC/accent-fold normalized; end-exclusive',
        noun_cau_masks=[{'nfc_span':[m.start(),m.end()],'source_form':m.group()} for m in NOUN_CAU.finditer(nfc)])
    quotes=list(old.base.QUOTED.finditer(s));accepted=[];suppressed_quote=False
    for item in trace['matches']:
        a,b=item['normalized_span'];q=next((q for q in quotes if q.start()<=a and b<=q.end()),None)
        if q is not None:
            left=item['clause_span'][0]
            # Breaks inside a quote cannot turn its subject into the narrator.
            before=s[left:q.start()] if left<=q.start() else s[:q.start()]
            outside_assignment=bool(ASSIGN.search(before))
            attributed=bool(ATTRIBUTION.search(before) or old.base.PAST_REPORT.search(before))
            stopping=bool(old.STOP.search(before));negated=bool(NEGATED_ASSIGNMENT.search(before))
            after=old.base.QUOTED.sub(' ',s[q.end():q.end()+55])
            endorsement=bool(old.base.ENDORSE.search(after)) and not re.search(r'\b(?:khong|chang).{0,16}\b(?:dung|chuan|xung dang)\b',after)
            item['quote_scope']={'quote_span':[q.start(),q.end()],'outside_assignment':outside_assignment,
                'attribution':attributed,'outside_endorsement':endorsement,'negated':negated,'stopping':stopping}
            if not negated and not stopping and (endorsement or (outside_assignment and not attributed)):
                item['decision']='new_personal_attack_candidate'
            else:
                item['decision']='suppressed_reported_quote_scope';suppressed_quote=True
        if item['decision']=='new_personal_attack_candidate':accepted.append(item)
    finalize_context(ctx,trace,accepted,suppressed_quote)
    return ctx,trace

def finalize_context(ctx,trace,accepted,suppressed_quote=False):
    attack=bool(accepted);ctx.tags=[x for x in ctx.tags if x!='DIRECT_ATTACK']
    accepted_rules={item['rule'] for item in accepted}
    ctx.cues=[x for x in ctx.cues if x!='new_directed_attack' and (x not in old.RULES or x in accepted_rules)]
    if suppressed_quote and 'QUOTE' not in ctx.tags:ctx.tags.append('QUOTE')
    ctx.attack_candidate=attack
    spans=[tuple(item['clause_span']) for item in accepted]
    s=trace['normalized_view']
    for item in accepted:
        left,right=item['clause_span']
        if item['rule'] in old.RULES and not old.ADDRESS.search(old.base.QUOTED.sub(' ',s[left:right])) and old.ADDRESS.search(old.base.QUOTED.sub(' ',s[:left])):
            spans.append((0,right))
    ctx.attack_clause_spans=list(dict.fromkeys(spans))
    if attack:
        ctx.tags=[x for x in ctx.tags if x!='UNCERTAIN'];ctx.tags.append('DIRECT_ATTACK');ctx.cues.append('new_directed_attack')
        ctx.unresolved_new_clause=False
    ctx.non_attack_context_confirmed=bool(set(ctx.tags)&old.SAFE_TAGS) and not attack and not ctx.unresolved_new_clause
    ctx.confidence='medium' if ctx.tags else 'low';ctx.needs_human_review=bool(ctx.tags)
    ctx.tags=list(dict.fromkeys(ctx.tags));ctx.cues=list(dict.fromkeys(ctx.cues))

def target_v62(comment,by_id,ctx,past_targets,past_ids):
    target=old.target_v6(comment,by_id,ctx,past_targets,past_ids).model_copy(deep=True)
    target.version=TARGET_VERSION
    return target

def analyze_thread_v62(payload,predictor):
    # Reuse canonical raw/lexicon/legacy output; one model forward only.
    out=analyze_thread_v2(payload,predictor);by_id={c.comment_id:c for c in payload.comments}
    histories=defaultdict(list);history_ids=defaultdict(list);pairs=defaultdict(list);contexts={};grounded=[]
    for row in out['comments']:
        c=by_id[row['comment_id']];ctx,trace=context_v62(c.text,{x.user_id for x in by_id.values()}-{c.user_id})
        target=target_v62(c,by_id,ctx,histories[c.user_id],history_ids[c.user_id]);contexts[c.comment_id]=ctx
        qualified=bool(ctx.attack_candidate and ctx.confidence in ('medium','high') and target.candidate is not None and target.confidence in ('medium','high'))
        row['directed_at_user_id']=target.candidate if qualified else None
        assessment,risk=assess(ctx,row['toxic_for_moderation']);row['moderation_assessment']=assessment.model_dump();row['policy_risk']=risk.model_dump()
        row['analysis_signals']={**row['analysis_signals'],'context_tags':ctx.tags,'context':ctx.model_dump(),'directed_attack_candidate':ctx.attack_candidate,
            'attack_confidence':ctx.confidence,'target_candidate':target.candidate,'target_evidence':target.model_dump(),'attack_instance_candidate':qualified,
            'attack_instance_basis':'context_with_grounded_target' if qualified else 'insufficient_context_or_target','rule_version':REPEATED_VERSION,
            'needs_human_review':ctx.needs_human_review or row['lexical_review_recommended'],'research_trace':trace}
        row['review_recommended']=bool(ctx.needs_human_review or row['lexical_review_recommended'] or row['toxic_for_moderation'])
        if qualified:
            histories[c.user_id].append(target.candidate);history_ids[c.user_id].append(c.comment_id)
            pairs[(c.user_id,target.candidate)].append((c,target));grounded.append((c,target))
    for row in out['comments']:
        if row['analysis_signals']['target_candidate'] is not None or not row['analysis_signals']['directed_attack_candidate']:continue
        c=by_id[row['comment_id']];target=resolve_root_exchange(c,by_id,contexts[c.comment_id],grounded,contexts);target.version=TARGET_VERSION
        if target.candidate is None:continue
        row['directed_at_user_id']=target.candidate;row['analysis_signals'].update(target_candidate=target.candidate,target_evidence=target.model_dump(),
            attack_instance_candidate=True,attack_instance_basis='context_with_grounded_target')
        pairs[(c.user_id,target.candidate)].append((c,target))
    evidence=[]
    for (actor,target),rows in sorted(pairs.items()):
        rows.sort(key=lambda item:(item[0].timestamp,item[0].comment_id));times={c.timestamp.astimezone(timezone.utc).isoformat() for c,_ in rows}
        if len(rows)>=2 and len(times)>=2:evidence.append({'actor_user_id':actor,'target_user_id':target,'evidence_comment_ids':[c.comment_id for c,_ in rows],
            'n_distinct_timestamps':len(times),'target_confidence':'medium' if any(t.confidence=='medium' for _,t in rows) else 'high'})
    out['evidence']=evidence;out['suspected_repeated_harassment']=bool(evidence)
    out['risk_level']='suspected_repeated' if evidence else 'needs_review' if any(r['review_recommended'] for r in out['comments']) else 'none'
    out['risk_score_heuristic']=min(95,65+5*max(len(e['evidence_comment_ids']) for e in evidence)) if evidence else 35 if out['risk_level']=='needs_review' else 0
    out['rule_versions'].update(context=CONTEXT_VERSION,target=TARGET_VERSION,repeated=REPEATED_VERSION)
    out['warnings'].append('Opt-in v6.2 research only; default and sealed v6.1 unchanged; no human-gold claim.')
    return out
