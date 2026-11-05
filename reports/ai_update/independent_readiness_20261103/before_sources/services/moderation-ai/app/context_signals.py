"""Clause-scoped context evidence. Raw model scores are never rewritten."""
from typing import Literal
import re
import unicodedata
from pydantic import BaseModel,Field
from .lexical import fold,detect,QUOTED
VERSION='context-v3'
Tag=Literal['APOLOGY','APOLOGY_ACCEPTANCE','QUOTE','DEFENSE','SET_BOUNDARY','INTERVENTION','ACKNOWLEDGEMENT','DIRECT_ATTACK','PROFANITY_NON_DIRECTED','UNCERTAIN']
class ContextSignals(BaseModel):
    version:str=VERSION
    tags:list[Tag]=Field(default_factory=list)
    attack_candidate:bool=False
    confidence:Literal['high','medium','low']='low'
    negated_attack:bool=False
    cues:list[str]=Field(default_factory=list)
    needs_human_review:bool=True
    non_attack_context_confirmed:bool=False
    unresolved_new_clause:bool=False

ATTACK=re.compile(r'\b(?:do ngu|ngu(?: ngoc)?|oc cho|thieu nao|vo dung|mat day|noob|n0ob|l[o0]ser|idiot|fake artist|do ham|ganh nang|cam di|sh1t player|choi nhu bot|ngo|nhay nhu (?:mot )?npc|nhin.{0,16}cringe|ich ky|an hai|khon nan|rac ruoi|trash|garbage|worthless)\b|\b(?:may|m|you|ban) (?:dung la |la )?dao duc gia\b|\b(?:tao|toi) se (?:danh|dap)\b|\b(?:f[*.\s]*[u*][*.\s]*c[*.\s]*k|fuck)\s+you\b')
DIRECT=re.compile(r'\b(?:may|m|ban|you|cau|ong|ba|thang|con|nhay nhu|ve nhu|cam di|thi nhan|bot.{0,24}di)\b|@?u\d+\b')
# Bounded disparaging constructions require an addressee below, not just a word.
DISPARAGEMENT=re.compile(r'\b(?:lam (?:an|viec) nhu hach|vung (?:ve )?nhu (?:may|m|ban|cau)|ganh (?:team|doi) nguoc|nao (?:de|cat|vat) (?:o )?dau)\b')
BLAME=re.compile(r'\b(?:thi|dang|xung dang) (?:phai )?(?:chiu )?bi (?:chui|ha nhuc|si nhuc)\b|\bchiu bi chui thoi\b')
NEGATED_BLAME=re.compile(r'\b(?:khong|chang) (?:phai cu|cu|ai (?:dang|xung dang)|(?:he )?(?:dang|xung dang))\b')
ACCEPTANCE=re.compile(r'\b(?:t|toi|minh|tui|to|em|anh) (?:(?:da|se|cung) )?(?:nhan|chap nhan) (?:loi )?xin loi\b')
APOLOGY=re.compile(r'(?:^|[.!?]\s*|@[\w]+\s+)(?:(?:t|toi|minh|tao|em|anh|tui|to|i|we)\s+)?(?:xin loi|sorry)\b')
CONTRAST=re.compile(r'\b(?:nhung|van|con (?:may|m|ban|you)|but|tuy nhien|chinh may)\b')
REPORT=re.compile(r'\b(?:da goi|da chui|vi (?:da )?goi|goi (?:m|ban) .{0,20}|trich dan|bi nhan|loi xuc pham|tu .{0,30} trong tin nhan)\b')
BOUNDARY=re.compile(r'\b(?:(?:dung|ngung) (?:dung loi |chui |xuc pham|cong kich|goi)|dung (?:chui|goi)|khong (?:muon|chap nhan).{0,30}(?:xuc pham|cong kich|loi de doa)|nho m dung)')
DEFENSE=re.compile(r'\b(?:cau|ve|loi) (?:sau|dau|do|ay).{0,30}(?:xuc pham|ha nhuc).{0,25}(?:khong chap nhan|minh|toi)|\b(?:ban|cau|ong|ba).{0,18}(?:dang )?xuc pham (?:minh|toi|tui)|\b(?:bi (?:chui|si nhuc|xuc pham|cong kich|nhan)|phai chiu bi|khong co nghia|cam on vi (?:da )?xin loi|cam on vi loi xin loi|loi do lam|may loi do|minh van buon|(?:ban|cau|ong|ba) (?:da )?chui (?:minh|toi))\b|\b(?:minh|toi|tui|to|t) (?:van |con |that su )?(?:buon|ton thuong|hut hang|khong thoai mai)\b|\b(?:nhung loi|loi do|loi ay).{0,45}(?:ton thuong|buon|tut mood)')
INTERVENTION=re.compile(r'\b(?:xuc pham|nhuc ma|cong kich).{0,30}(?:thi dung|thi ngung|khong phai (?:phe binh|gop y))|\bdo la cong kich (?:nguoi|ca nhan)|\b(?:dung chui ban ay|chui ca nhan|gop y (?:vao|ve) .{0,25}(?:thoi|dang hoang)|goi ban ay|mo combat ngoai doi|noi tiep lam chi|dung cong kich|ngung cong kich|dung chui nhau|hai ban binh tinh|che .{0,30}khac voi che con nguoi|thoi nhuc ma|khong ai duoc nhuc ma)\b|\b(?:dung|ngung|thoi).{0,24}(?:ha nhuc|xuc pham|chup mu)\b')
ACKNOWLEDGE=re.compile(r'\b(?:t|toi|minh|tui|tao|em) (?:(?:da|vua) )?(?:sai(?: ro roi)?|nhan loi(?!\s+xin loi)|nong qua|noi qua|qua loi|noi bay)\b|\bloi (?:la )?(?:cua|o) (?:toi|minh)\b|\b(?:t|toi|minh|tui|tao|em) (?:vua nong vua |(?:da|vua) )?(?:hieu sai|hieu nham|trach nham|do oan)\b')
# Reset reporting scope at sentence boundaries, contrasts and a new addressee after comma.
BREAK=re.compile(r'[!?;\n]|\.(?:\s|$)|\b(?:nhung|but|tuy nhien|chu)\b|,\s*(?=(?:may|m|ban|you|cau|ong|ba|tao|toi)\b)|\b(?:va|con|roi|bay gio)\s+(?=(?:may|m|ban|you|cau|ong|ba|tao|toi)\b)')
STOP_ABUSE=re.compile(r'\b(?:dung|ngung|thoi|khong nen|khong duoc).{0,28}(?:goi|chui|xuc pham|nhuc ma|cong kich|ha nhuc)\b')
PAST_REPORT=re.compile(r'\b(?:vi (?:da )?(?:goi|chui)|(?:da|vua|tung) (?:goi|chui)|bi (?:goi|chui|nhan)|trich dan|nhac lai|loi xuc pham)\b')
ENDORSE=re.compile(r'\b(?:la dung|la chuan|moi chinh xac|xung dang)\b')
NEW_PERSONAL_CLAUSE=re.compile(r'\b(?:nhung|but|tuy nhien|chu)\s+(?:chinh )?(?:may|m|ban|you|cau|ong|ba|tao|toi)\b')


def analyze_context(text:str)->ContextSignals:
    # Keep accented homographs distinct before folding context cues.
    normalized=unicodedata.normalize('NFC',text)
    s=fold(re.sub(r'(?iu)\b(?:ngủ|ngữ|ngự)\b','zzz',normalized));tags=[];cues=[]
    quotes=[(m.start(),m.end()) for m in QUOTED.finditer(s)]
    apology=bool(APOLOGY.search(s)) and not s.startswith('xin loi khong')
    boundary=bool(BOUNDARY.search(s) or re.search(r'\bdung dung tu.{0,25}voi (?:t|toi|minh|tui)\b',s))
    defense=bool(DEFENSE.search(s))
    intervention=bool(INTERVENTION.search(s) or re.search(r'\b(?:dung do (?:het |loi )?len|khong phai (?:de )?(?:cong kich|ha nhuc|xuc pham)|thoi (?:ong|ba|ban) oi)\b',s))
    ack=bool(ACKNOWLEDGE.search(s));acceptance=bool(ACCEPTANCE.search(s))
    if apology:tags.append('APOLOGY');cues.append('explicit_apology')
    if acceptance:tags.append('APOLOGY_ACCEPTANCE');cues.append('accepts_others_apology')
    if quotes or (apology and REPORT.search(s)):tags.append('QUOTE');cues.append('quoted_or_recalled_speech')
    if defense:tags.append('DEFENSE');cues.append('defense_or_recovery')
    if boundary:tags.append('SET_BOUNDARY');cues.append('boundary_request')
    if intervention:tags.append('INTERVENTION');cues.append('third_party_intervention')
    if ack:tags.append('ACKNOWLEDGEMENT');cues.append('self_responsibility')
    attack=False;negated=False;endorsed_blame=False;breaks=list(BREAK.finditer(s))
    matches=sorted([*ATTACK.finditer(s),*DISPARAGEMENT.finditer(s)],key=lambda m:m.start())
    for match in matches:
        left=max((m.end() for m in breaks if m.end()<=match.start()),default=0)
        end=min((m.start() for m in breaks if m.start()>=match.end()),default=len(s))
        prefix=s[left:match.start()];clause=s[left:end]
        in_quote=any(a<=match.start() and match.end()<=b for a,b in quotes)
        assigned_quote=bool(re.search(r'\b(?:may|m|ban|you)\b.{0,24}\b(?:la|are)\s*[“"\']?\s*$',prefix)) and not STOP_ABUSE.search(prefix)
        endorsed=bool(ENDORSE.search(s[match.end():min(len(s),match.end()+55)]))
        history=bool(PAST_REPORT.search(prefix)) or (in_quote and not assigned_quote)
        local_neg=bool(re.search(r'\bkhong(?: he)?(?: phai)?(?: la)?\s*$',prefix))
        stopping=bool(STOP_ABUSE.search(prefix))
        blame=bool(BLAME.search(clause))
        if blame and NEGATED_BLAME.search(clause):
            negated=True;continue
        if local_neg or ((history or stopping) and not (assigned_quote or endorsed)):
            negated=True;continue
        if DIRECT.search(clause) or blame or 'se danh' in match.group() or 'se dap' in match.group() or 'you' in match.group() or match.group()=='cam di' or (match.group()=='do ngu' and not prefix.strip()):
            attack=True;endorsed_blame|=blame
    if endorsed_blame:
        tags=[tag for tag in tags if tag!='DEFENSE'];cues=[cue for cue in cues if cue!='defense_or_recovery']
        cues.append('endorsed_abuse_of_addressee')
    if attack:tags.append('DIRECT_ATTACK');cues.append('new_directed_attack')
    lex=detect(text)
    if lex['profanity_detected'] and not attack and not (apology or quotes):tags.append('PROFANITY_NON_DIRECTED')
    # A new personal contrast that the bounded attack vocabulary cannot interpret is an abstention.
    unresolved=bool((apology or ack or acceptance) and NEW_PERSONAL_CLAUSE.search(s) and not attack and not STOP_ABUSE.search(s))
    if unresolved or (not tags and (ATTACK.search(s) or lex['directed_insult_candidate'])):tags.append('UNCERTAIN')
    safe=not endorsed_blame and bool(set(tags)&{'APOLOGY','APOLOGY_ACCEPTANCE','QUOTE','DEFENSE','SET_BOUNDARY','INTERVENTION','ACKNOWLEDGEMENT'}) and not attack and not unresolved
    return ContextSignals(tags=list(dict.fromkeys(tags)),attack_candidate=attack,
      confidence='medium' if tags else 'low',negated_attack=negated,cues=cues,
      needs_human_review=bool(tags),non_attack_context_confirmed=safe,unresolved_new_clause=unresolved)
