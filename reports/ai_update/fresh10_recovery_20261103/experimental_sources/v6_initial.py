"""Opt-in clause/lexical research processor, never imported by the default API.

Composes sealed v5 raw/legacy output with experimental context/target evidence.
No reference labels or test IDs are accepted by the processor.
"""
import re,unicodedata
from collections import defaultdict
from datetime import timezone
from .. import context_signals as base
from ..target_signals import infer_target,resolve_root_exchange,TargetSignals
from ..signal_engine import analyze_thread_v2
from ..context_assessment import assess
CONTEXT_VERSION='context-v6-research';TARGET_VERSION='target-v6-research';REPEATED_VERSION='repeated-v6-research'
PLANTS=re.compile(r'\b(?:ngò|ngô|máy|bàn|ống|cầu|mấy|bản)\b',re.I)
ADDRESS=re.compile(base.DIRECT.pattern+r'|\bb\b')
BREAK=re.compile(base.BREAK.pattern+r'|,\s*(?=(?:b|t)\b)')
STOP=re.compile(base.STOP_ABUSE.pattern+r'|\b(?:dung|ngung|thoi|khong nen|khong duoc).{0,24}(?:che|gan|quy ch?up)\b')
RULES={
    'personal_conduct':re.compile(r'\b(?:song kieu vo y thuc|cai cun|thich ra oai(?: qua)?|kieu nguoi thich bat nat|nguoi lam an chop giat)\b'),
    'personal_humiliation':re.compile(r'\b(?:lam tro cuoi|phong bat.{0,24}cringe|(?:hat|noi|viet|lam) do.{0,25}thich lam trung tam|dem khoe.{0,12}que)\b'),
    'english_personal_insult':re.compile(r'\b(?:f[*u.]*cking\s+clueless)\b'),
    'sarcastic_incompetence':re.compile(r'\b(?:chuyen gia|thien tai|cao thu) tu phong\b|\bkhong biet .{3,55}\b(?:cung tai|gioi ghe|qua gioi)\b'),
}
SAFE_TAGS={'APOLOGY','APOLOGY_ACCEPTANCE','QUOTE','DEFENSE','SET_BOUNDARY','INTERVENTION','ACKNOWLEDGEMENT'}

def context_v6(text,participants=()):
    nfc=unicodedata.normalize('NFC',text);masked=PLANTS.sub(lambda m:'z'*len(m.group()),nfc)
    ctx=base.analyze_context(masked,participants).model_copy(deep=True);ctx.version=CONTEXT_VERSION
    s=base.context_view(masked);original=base.context_view(nfc);trace={'v5_tags':list(ctx.tags),'normalization':[
        {'source_form':m.group(),'nfc_span':[m.start(),m.end()],'reason':'accented non-personal homograph; never a whole-message CLEAN rule'} for m in PLANTS.finditer(nfc)],'matches':[]}
    defense_matches=list(base.DEFENSE.finditer(s))
    if defense_matches and all(m.group()=='khong co nghia' for m in defense_matches):
        ctx.tags=[x for x in ctx.tags if x!='DEFENSE'];ctx.cues=[x for x in ctx.cues if x!='defense_or_recovery']
        trace['removed_defense_reason']='bare_causal_connector_is_not_self_defense'
    breaks=list(BREAK.finditer(s));quotes=[(m.start(),m.end()) for m in base.QUOTED.finditer(s)]
    attack=False;spans=[];blame_endorsed=False;accepted=[]
    patterns={'v5_attack':base.ATTACK,'v5_disparagement':base.DISPARAGEMENT,'v5_indirect':base.INDIRECT,**RULES}
    for name,pattern in patterns.items():
        for match in pattern.finditer(s):
            left=max((m.end() for m in breaks if m.end()<=match.start()),default=0)
            right=min((m.start() for m in breaks if m.start()>=match.end()),default=len(s));clause=s[left:right];prefix=s[left:match.start()]
            item={'rule':name,'normalized_match':match.group(),'normalized_span':[match.start(),match.end()],'clause_span':[left,right]}
            quoted=any(a<=match.start() and match.end()<=b for a,b in quotes)
            assigned=bool(re.search(r'\b(?:may|m|b|ban|you)\b.{0,24}\b(?:la|are)\s*[“"\']?\s*$',prefix)) and not STOP.search(prefix)
            endorsed=bool(base.ENDORSE.search(s[match.end():match.end()+55]));blame=bool(base.BLAME.search(clause))
            history=bool(base.PAST_REPORT.search(prefix)) or (quoted and not assigned)
            negation=bool(re.search(r'\bkhong(?: he)?(?: phai)?(?: la)?\s*$',prefix))
            external=bool(ADDRESS.search(base.QUOTED.sub(' ',clause))) or any(re.search(r'(?<!\w)@?'+re.escape(base.context_view(uid))+r'(?!\w)',base.QUOTED.sub(' ',original[left:right])) for uid in participants)
            self_subject=bool(re.match(r'\s*(?:t|toi|minh|tui|tao)\s+(?:tu |dang |qua |that )?',clause)) and not external
            if negation or (blame and base.NEGATED_BLAME.search(clause)) or ((history or STOP.search(prefix)) and not (assigned or endorsed)):
                item['decision']='suppressed_report_quote_negation_or_intervention';ctx.negated_attack=True
            elif self_subject:
                item['decision']='self_reference_without_external_addressee'
            elif external or name in RULES or blame or match.group()=='cam di' or 'se danh' in match.group() or 'se dap' in match.group() or 'you' in match.group() or (match.group()=='do ngu' and not prefix.strip()):
                item['decision']='new_personal_attack_candidate';attack=True;accepted.append(name);blame_endorsed|=blame
                if (left,right) not in spans:spans.append((left,right))
                # A named/addressed framing sentence may govern an elliptical
                # derogatory continuation; preserve it as target evidence.
                if name in RULES and not external and (ADDRESS.search(base.QUOTED.sub(' ',s[:left]))):
                    if (0,right) not in spans:spans.append((0,right))
            else:item['decision']='no_personal_addressee'
            trace['matches'].append(item)
    ctx.tags=[x for x in ctx.tags if x not in ('DIRECT_ATTACK','PROFANITY_NON_DIRECTED') or (x=='PROFANITY_NON_DIRECTED' and not attack)]
    if blame_endorsed:
        ctx.tags=[x for x in ctx.tags if x!='DEFENSE'];ctx.cues.append('endorsed_abuse_of_addressee')
    if attack:
        ctx.tags=[x for x in ctx.tags if x!='UNCERTAIN'];ctx.tags.append('DIRECT_ATTACK');ctx.cues.append('new_directed_attack')
    else:
        if re.search(r'\b(?:khia|che|cuoi).{0,60}\bcua chinh (?:t|toi|minh|tui)\b',s):
            ctx.tags.append('ACKNOWLEDGEMENT');ctx.cues.append('self_deprecating_object')
        if re.search(r'\bdung che con nguoi (?:minh|toi|tui)\b|\b(?:minh|toi|tui) khong tiep kieu do\b',s):
            ctx.tags.append('SET_BOUNDARY');ctx.cues.append('personal_boundary_not_new_attack')
        if re.search(r'\bsao quay sang cong kich (?:chu bai|nguoi khac)\b|\bnoi thang khac voi ha nhuc\b',s):
            ctx.tags.append('INTERVENTION');ctx.cues.append('distinguishes_criticism_from_abuse')
        if re.search(r'\bkhong co nghia (?:la )?(?:(?:minh|toi|t|tui) )?(?:phai )?(?:nhan|chap nhan|chiu) (?:loi )?(?:xuc pham|cong kich|ha nhuc)\b',s):
            ctx.tags.append('DEFENSE');ctx.cues.append('explicit_refusal_of_abuse_not_bare_connector')
    # Do not let a known safe fragment clear an unhandled new personal contrast.
    unresolved=bool(not attack and ctx.unresolved_new_clause)
    if not attack and set(ctx.tags)&SAFE_TAGS and re.search(r'\b(?:nhung|but|chu|con)\s+(?:b|may|m|ban|you|cau|ong|ba)\b',s):
        if not STOP.search(s):unresolved=True
    ctx.attack_candidate=attack;ctx.attack_clause_spans=spans;ctx.unresolved_new_clause=unresolved
    if unresolved and 'UNCERTAIN' not in ctx.tags:ctx.tags.append('UNCERTAIN')
    ctx.non_attack_context_confirmed=bool(set(ctx.tags)&SAFE_TAGS) and not attack and not unresolved and not blame_endorsed
    ctx.tags=list(dict.fromkeys(ctx.tags));ctx.cues=list(dict.fromkeys(ctx.cues+[name for name in accepted if name in RULES]))
    ctx.confidence='medium' if ctx.tags else 'low';ctx.needs_human_review=bool(ctx.tags)
    return ctx,trace

def target_v6(comment,by_id,ctx,past_targets,past_ids):
    result=infer_target(comment,by_id,ctx,past_targets,past_ids).model_copy(deep=True);result.version=TARGET_VERSION
    if not ctx.attack_candidate or result.confidence in ('medium','high'):return result
    if result.method in ('ambiguous_mentions','history_reply_conflict'):return result
    s=base.QUOTED.sub(' ',base.context_view(comment.text));parent=by_id.get(comment.parent_id);history=set(past_targets)
    personal=bool(set(ctx.cues)&set(RULES))
    if parent and parent.user_id!=comment.user_id and (not history or history=={parent.user_id}):
        if re.search(r'\bb\b',s) or personal:
            return TargetSignals(version=TARGET_VERSION,candidate=parent.user_id,method='addressed_teencode_reply' if re.search(r'\bb\b',s) else 'personal_ellipsis_reply',
                confidence='medium',evidence_comment_ids=list(dict.fromkeys([comment.comment_id,parent.comment_id]+list(past_ids[-2:]))))
    if parent and parent.user_id==comment.user_id and len(history)==1 and ADDRESS.search(s):
        parent_text=base.QUOTED.sub(' ',base.context_view(parent.text))
        mentioned={uid for uid in {c.user_id for c in by_id.values()}-{comment.user_id} if re.search(r'(?<!\w)@?'+re.escape(base.context_view(uid))+r'(?!\w)',parent_text)}
        if mentioned==history:
            return TargetSignals(version=TARGET_VERSION,candidate=next(iter(history)),method='self_reply_named_addressee_with_attack_history',confidence='medium',
                evidence_comment_ids=list(dict.fromkeys([comment.comment_id,parent.comment_id]+list(past_ids[-2:]))))
    if parent and parent.user_id==comment.user_id and personal:
        ancestor=by_id.get(parent.parent_id)
        if ancestor and ancestor.user_id!=comment.user_id and (not history or history=={ancestor.user_id}):
            parent_mentions={uid for uid in {c.user_id for c in by_id.values()}-{comment.user_id} if re.search(r'(?<!\w)@?'+re.escape(base.context_view(uid))+r'(?!\w)',base.QUOTED.sub(' ',base.context_view(parent.text)))}
            if not parent_mentions or parent_mentions=={ancestor.user_id}:
                return TargetSignals(version=TARGET_VERSION,candidate=ancestor.user_id,method='self_reply_to_addressed_exchange',confidence='medium',
                    evidence_comment_ids=[comment.comment_id,parent.comment_id,ancestor.comment_id])
    return result

def analyze_thread_v6(payload,predictor):
    out=analyze_thread_v2(payload,predictor);by_id={c.comment_id:c for c in payload.comments}
    histories=defaultdict(list);history_ids=defaultdict(list);pairs=defaultdict(list);contexts={};grounded=[]
    for row in out['comments']:
        c=by_id[row['comment_id']];ctx,trace=context_v6(c.text,{x.user_id for x in by_id.values()}-{c.user_id})
        target=target_v6(c,by_id,ctx,histories[c.user_id],history_ids[c.user_id]);contexts[c.comment_id]=ctx
        qualified=ctx.attack_candidate and ctx.confidence in ('medium','high') and target.candidate is not None and target.confidence in ('medium','high')
        row['directed_at_user_id']=target.candidate if qualified else None
        assessment,risk=assess(ctx,row['toxic_for_moderation']);row['moderation_assessment']=assessment.model_dump();row['policy_risk']=risk.model_dump()
        row['analysis_signals']={**row['analysis_signals'],'context_tags':ctx.tags,'context':ctx.model_dump(),'directed_attack_candidate':ctx.attack_candidate,
            'attack_confidence':ctx.confidence,'target_candidate':target.candidate,'target_evidence':target.model_dump(),'attack_instance_candidate':bool(qualified),
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
        row['directed_at_user_id']=target.candidate;row['analysis_signals'].update(target_candidate=target.candidate,target_evidence=target.model_dump(),attack_instance_candidate=True,attack_instance_basis='context_with_grounded_target')
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
    out['warnings'].append('Opt-in v6 research only; default v5/readiness lock unchanged, synthetic references are not human gold.')
    return out
