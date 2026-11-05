"""Bounded, explainable context heuristics; never changes model scores or labels."""
from typing import Literal
import re
from pydantic import BaseModel,Field
from .lexical import fold,detect,QUOTED
VERSION='context-v1'
Tag=Literal['APOLOGY','QUOTE','DEFENSE','SET_BOUNDARY','INTERVENTION','DIRECT_ATTACK','PROFANITY_NON_DIRECTED','UNCERTAIN']
class ContextSignals(BaseModel):
    version:str=VERSION
    tags:list[Tag]=Field(default_factory=list)
    attack_candidate:bool=False
    confidence:Literal['high','medium','low']='low'
    negated_attack:bool=False
    cues:list[str]=Field(default_factory=list)
    needs_human_review:bool=True

ATTACK=re.compile(r'\b(?:do ngu|ngu(?: ngoc)?|oc cho|thieu nao|vo dung|mat day|noob|n0ob|l[o0]ser|idiot|fake artist|do ham|ganh nang|cam di|sh1t player|choi nhu bot|ngo|nhay nhu (?:mot )?npc|nhin.{0,16}cringe)\b|\b(?:tao|toi) se danh\b|\b(?:f[*.\s]*[u*][*.\s]*c[*.\s]*k|fuck)\s+you\b')
DIRECT=re.compile(r'\b(?:may|m|ban|you|cau|ong|ba|thang|con|nhay nhu|ve nhu|cam di|thi nhan|bot.{0,24}di)\b|@?u\d+\b')
APOLOGY=re.compile(r'(?:^|[.!?]\s*|@u\d+\s+)(?:(?:t|toi|minh|tao|em|anh)\s+)?(?:xin loi|sorry)\b')
CONTRAST=re.compile(r'\b(?:nhung|van|con (?:may|m|ban|you)|but|tuy nhien|chinh may)\b')
REPORT=re.compile(r'\b(?:da goi|da chui|vi (?:da )?goi|goi (?:m|ban) .{0,20}|trich dan|bi nhan|loi xuc pham|tu .{0,30} trong tin nhan)\b')
BOUNDARY=re.compile(r'\b(?:(?:dung|ngung) (?:dung loi |chui |xuc pham|goi)|dung (?:chui|goi)|khong (?:muon|chap nhan).{0,30}(?:xuc pham|cong kich)|nho m dung)')
DEFENSE=re.compile(r'\b(?:bi (?:chui|si nhuc|xuc pham|cong kich|nhan)|phai chiu bi|khong co nghia|cam on vi xin loi|cam on vi loi xin loi|loi do lam|may loi do|minh van buon|(?:ban|cau|ong|ba) (?:da )?chui (?:minh|toi))\b')
INTERVENTION=re.compile(r'\b(?:dung chui ban ay|chui ca nhan|gop y (?:vao|ve) .{0,25}(?:thoi|dang hoang)|goi ban ay|mo combat ngoai doi|noi tiep lam chi|dung cong kich|dung chui nhau|hai ban binh tinh|che .{0,30}khac voi che con nguoi)\b')

def analyze_context(text:str)->ContextSignals:
    s=fold(text);tags=[];cues=[]
    quotes=[(m.start(),m.end()) for m in QUOTED.finditer(s)]
    apology=bool(APOLOGY.search(s)) and not s.startswith('xin loi khong')
    boundary=bool(BOUNDARY.search(s));defense=bool(DEFENSE.search(s));intervention=bool(INTERVENTION.search(s))
    if apology:tags.append('APOLOGY');cues.append('explicit_apology')
    if quotes or (apology and REPORT.search(s)):tags.append('QUOTE');cues.append('quoted_or_recalled_speech')
    if defense:tags.append('DEFENSE');cues.append('defense_or_recovery')
    if boundary:tags.append('SET_BOUNDARY');cues.append('boundary_request')
    if intervention:tags.append('INTERVENTION');cues.append('third_party_intervention')
    attack=False;negated=False
    for match in ATTACK.finditer(s):
        left=max(s.rfind('.',0,match.start()),s.rfind('!',0,match.start()),s.rfind('?',0,match.start()),s.rfind(';',0,match.start()))+1
        right=re.search(r'[.!?;]',s[match.end():]);end=match.end()+right.start() if right else len(s)
        prefix=s[left:match.start()];clause=s[left:end]
        in_quote=any(a<=match.start() and match.end()<=b for a,b in quotes)
        fresh=bool(CONTRAST.search(prefix))
        assigned_quote=bool(re.search(r'\b(?:may|m|ban|you)\b.{0,20}\b(?:la|are)\s*[“"\']?\s*$',prefix))
        history=(apology and bool(REPORT.search(s[:match.start()]))) or (in_quote and not assigned_quote)
        local_neg=bool(re.search(r'\bkhong(?: he)?(?: phai)?(?: la)?\s*$',prefix))
        stopping=(boundary or intervention) and not fresh
        if local_neg or ((history or stopping) and not fresh):negated=True;continue
        if DIRECT.search(clause) or 'se danh' in match.group() or 'you' in match.group() or match.group()=='cam di':attack=True
    if attack:tags.append('DIRECT_ATTACK');cues.append('new_directed_attack')
    lex=detect(text)
    if lex['profanity_detected'] and not attack and not (apology or quotes):tags.append('PROFANITY_NON_DIRECTED')
    # Absence of a high-precision attack cue is not proof of harmlessness.
    if not tags and (ATTACK.search(s) or lex['directed_insult_candidate']):tags.append('UNCERTAIN')
    return ContextSignals(tags=list(dict.fromkeys(tags)),attack_candidate=attack,
      confidence='medium' if tags else 'low',negated_attack=negated,cues=cues,
      needs_human_review=bool(tags))
