from __future__ import annotations
import hashlib,hmac,ipaddress,json,re,secrets,unicodedata
from datetime import datetime,timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit
from pydantic import BaseModel,Field,AwareDatetime,model_validator
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'datasets/real_conversations'
HOSTS=('vi.wikipedia.org','vi.wiktionary.org','vi.wikibooks.org')
LICENSE='CC-BY-SA-4.0'
def now():return datetime.now(timezone.utc).isoformat()
def sha_bytes(value):return hashlib.sha256(value).hexdigest()
def sha_file(path):return sha_bytes(Path(path).read_bytes())
def stable_id(prefix,*parts):return prefix+'_'+sha_bytes('|'.join(map(str,parts)).encode())[:24]
def atomic_json(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(path)
def load_json(path,default=None):
    p=Path(path);return json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else default

def comparison(text):return re.sub(r'\s+',' ',unicodedata.normalize('NFC',text).casefold()).strip()
def text_grams(text):
    text=comparison(text);return {text[i:i+5] for i in range(max(1,len(text)-4))}
def near_similarity(a,b):
    x,y=text_grams(a),text_grams(b)
    return len(x&y)/len(x|y) if x or y else 1.0

class VisibleText(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style'):self.skip+=1;return
        if self.skip:return
        if tag in ('br','p','div','li','blockquote') and self.parts and not self.parts[-1].endswith('\n'):self.parts.append('\n')
        if tag=='img':
            alt=dict(attrs).get('alt')
            if alt:self.parts.append(alt)
    def handle_endtag(self,tag):
        if tag in ('script','style'):self.skip=max(0,self.skip-1);return
        if not self.skip and tag in ('p','div','li','blockquote') and self.parts and not self.parts[-1].endswith('\n'):self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)
def visible_text(value):
    p=VisibleText();p.feed(value);return ''.join(p.parts).strip()
EMAIL=re.compile(r'(?<![\w.+-])[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}(?!\w)')
PHONE=re.compile(r'(?<!\w)(?:\+84|0)(?:[ .()-]*\d){8,10}(?!\d)')
IPV4=re.compile(r'(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?:/\d{1,2})?(?![\w.])')
IPV6=re.compile(r'(?<!\w)[A-Fa-f0-9]*:[A-Fa-f0-9:]+(?:/\d{1,3})?(?!\w)')
NATIONAL_ID=re.compile(r'(?<!\d)\d{12}(?!\d)')
ADDRESS=re.compile(r'(?i)(?:địa chỉ nhà|nhà (?:tôi|mình) ở|số nhà)\s*[:：]?\s*[^\n;]{5,140}')

def pii_hits(text):
    found=[]
    for kind,pattern in [('email',EMAIL),('phone',PHONE),('national_id',NATIONAL_ID),('address',ADDRESS)]:
        found += [(m.start(),m.end(),kind) for m in pattern.finditer(text)]
    for pattern in (IPV4,IPV6):
        for m in pattern.finditer(text):
            try:ipaddress.ip_network(m.group(),strict=False)
            except ValueError:continue
            found.append((m.start(),m.end(),'ip'))
    return sorted(found,key=lambda x:(x[0],-(x[1]-x[0])))
class Pseudonymizer:
    def __init__(self,data_root=DATA,key=None):
        self.root=Path(data_root)
        path=self.root/'raw/private_pseudonym_key.txt'
        if key is None:
            if not path.exists():
                if any((self.root/'threads').glob('*.json')) or any((self.root/'anonymized/manual_inbox').glob('*.json')):raise ValueError('Pseudonym key missing; restore the existing key before resuming')
                path.parent.mkdir(parents=True,exist_ok=True);path.write_text(secrets.token_hex(32),encoding='ascii')
            key=bytes.fromhex(path.read_text(encoding='ascii'))
        self.key=key
    def user(self,host,author):
        if not author:return None
        return 'U_'+hmac.new(self.key,(host+'|'+author).encode(),hashlib.sha256).hexdigest()[:16]
    def redact(self,text,host,authors=()):
        spans=pii_hits(text)
        # Exact source identities only; no accent/spelling normalization of authored prose.
        for author in set(authors):
            if not author:continue
            for m in re.finditer(r'(?<!\w)@?'+re.escape(author)+r'(?!\w)',text):spans.append((m.start(),m.end(),'author:'+self.user(host,author)))
        spans.sort(key=lambda x:(x[0],-(x[1]-x[0]),0 if x[2].startswith('author:') else 1))
        result=[];end=0;counts={}
        for a,b,kind in spans:
            if a<end:continue
            result.extend([text[end:a],kind.split(':',1)[1] if kind.startswith('author:') else '[REDACTED_'+kind.upper()+']'])
            end=b;name='source_identity' if kind.startswith('author:') else kind;counts[name]=counts.get(name,0)+1
        result.append(text[end:])
        return ''.join(result),counts

class RealComment(BaseModel):
    comment_id:str=Field(min_length=1,max_length=120)
    parent_id:str|None=None
    user_id:str|None=None
    timestamp:AwareDatetime|None=None
    text:str=Field(min_length=1,max_length=200000)
    source_item_hash:str
    parent_origin:Literal['source_discussiontools_tree','source_top_level','missing_from_source']
    timestamp_origin:Literal['source_signature_parser','missing_from_source']
    redactions:dict[str,int]=Field(default_factory=dict)
class RealThread(BaseModel):
    thread_id:str=Field(pattern=r'^T_[0-9a-f]{24}$')
    source_platform:Literal['vi.wikipedia.org','vi.wiktionary.org','vi.wikibooks.org']
    source_url:str
    source_license:Literal['CC-BY-SA-4.0']
    collected_at:AwareDatetime
    data_origin:Literal['real']
    topic:str
    source_page_id:int
    source_revision_id:int
    source_response_sha256:str=Field(pattern=r'^[0-9a-f]{64}$')
    source_heading_hash:str
    comments:list[RealComment]=Field(min_length=1,max_length=500)
    evaluation_eligible:Literal[False]=False
    evaluation_role:Literal['candidate_independent_evaluation']='candidate_independent_evaluation'
    training_eligible:Literal[False]=False
    completeness_status:Literal['source_parser_only_unsigned_content_may_be_missing']='source_parser_only_unsigned_content_may_be_missing'
    human_privacy_review_status:Literal['PENDING']='PENDING'
    extraction_method:str='Source DiscussionTools rendered HTML, signatures excluded; visible text only, no language cleanup'
    modification_notice:str='Source usernames pseudonymized; recognized contact/IP/address identifiers redacted. Other wording retained.'
    attribution_url:str
    @model_validator(mode='after')
    def structure(self):
        u=urlsplit(self.source_url)
        if u.scheme!='https' or u.hostname!=self.source_platform:raise ValueError('Source URL must match audited HTTPS project')
        if not self.attribution_url.startswith('https://'+self.source_platform+'/'):raise ValueError('Attribution URL required')
        ids=[c.comment_id for c in self.comments]
        if len(set(ids))!=len(ids):raise ValueError('Duplicate comment ID')
        lookup={c.comment_id:c for c in self.comments}
        for c in self.comments:
            if c.user_id is not None and not re.fullmatch(r'U_[0-9a-f]{16}',c.user_id):raise ValueError('Non-pseudonymous user ID')
            if c.timestamp and c.timestamp>self.collected_at:raise ValueError('Source signature is in the future')
            if c.parent_id and c.parent_id not in lookup:raise ValueError('Missing parent')
            seen={c.comment_id};parent=c.parent_id
            while parent:
                if parent in seen:raise ValueError('Parent cycle')
                seen.add(parent);parent=lookup[parent].parent_id
        return self

def extract_threads(response,page,host,pseudonymizer,response_hash):
    """Use source-provided heading/replies tree; no indentation or relationship invention."""
    roots=response.get('discussiontoolspageinfo',{}).get('threaditemshtml')
    if not isinstance(roots,list):raise ValueError('Unsupported DiscussionTools response schema')
    all_authors=set()
    def authors(node):
        if node.get('type')=='comment' and node.get('author'):all_authors.add(node['author'])
        for child in node.get('replies',[]):authors(child)
    for root in roots:authors(root)
    threads=[]
    for root in roots:
        if root.get('type')!='heading' or not root.get('id'):continue
        comments=[]
        def visit(node,parent_comment=None):
            current=parent_comment
            if node.get('type')=='comment':
                if not node.get('id') or not isinstance(node.get('html'),str):raise ValueError('Missing source comment identity/body')
                current=stable_id('C',host,page['pageid'],node['id'])
                body=visible_text(node['html']);body,redactions=pseudonymizer.redact(body,host,all_authors)
                comments.append({'comment_id':current,'parent_id':parent_comment,'user_id':pseudonymizer.user(host,node.get('author')),
                  'timestamp':node.get('timestamp'),'text':body,'source_item_hash':stable_id('I',host,node['id']),
                  'parent_origin':'source_discussiontools_tree' if parent_comment else 'source_top_level',
                  'timestamp_origin':'source_signature_parser' if node.get('timestamp') else 'missing_from_source','redactions':redactions})
            for child in node.get('replies',[]):visit(child,current)
        visit(root)
        if not comments:continue
        topic,_=pseudonymizer.redact(visible_text(root.get('html','')),host,all_authors)
        url='https://'+host+'/w/index.php?oldid='+str(page['lastrevid'])
        thread={'thread_id':stable_id('T',host,page['pageid'],root['id']),'source_platform':host,'source_url':url,'source_license':LICENSE,
          'collected_at':now(),'data_origin':'real','topic':topic or 'Nguồn không có tiêu đề hiển thị','source_page_id':page['pageid'],'source_revision_id':page['lastrevid'],
          'source_response_sha256':response_hash,'source_heading_hash':stable_id('H',host,root['id']),'comments':comments,'attribution_url':url}
        threads.append(RealThread.model_validate(thread).model_dump(mode='json'))
    return threads

def thread_text(thread):return '\n'.join(c['text'] for c in thread['comments'])
def structural_quality(thread):
    t=RealThread.model_validate(thread);issues=[];warnings=[]
    if any(pii_hits(c.text) for c in t.comments) or pii_hits(t.topic):issues.append('recognized_pii_remaining')
    if len(t.comments)<10 or len(t.comments)>30:warnings.append('outside_preferred_10_30_comments')
    users={c.user_id for c in t.comments if c.user_id}
    if len(users)<2:issues.append('fewer_than_two_known_participants')
    if any(c.user_id is None for c in t.comments):warnings.append('missing_source_author')
    if any(c.timestamp is None for c in t.comments):warnings.append('missing_source_timestamp')
    by_id={c.comment_id:c for c in t.comments}
    if any(c.parent_id and c.timestamp and by_id[c.parent_id].timestamp and c.timestamp<by_id[c.parent_id].timestamp for c in t.comments):warnings.append('source_signature_chronology_inconsistent')
    return {'errors':issues,'warnings':warnings,'comments':len(t.comments),'users':len(users),'redactions':sum(sum(c.redactions.values()) for c in t.comments)}
