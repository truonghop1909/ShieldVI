"""Compile explicitly authored dialogue; no LLM calls or automatic text labeling.

Catalogue row: speaker|annotation-code|parent-number (0=null)|target or -|text[|reason]
Codes are AI-authored reference annotations, never predictions/human gold.
"""
from __future__ import annotations
import argparse,csv,hashlib,io,json,re,unicodedata
from collections import Counter,defaultdict
from datetime import datetime,timedelta,timezone
from pathlib import Path
from typing import Literal
from pydantic import AwareDatetime,BaseModel,ConfigDict,Field,model_validator
ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/'datasets/synthetic_conversations'
CATALOGUE=Path(__file__).parent
CODES={
 'N':('CLEAN','normal','Trao đổi thông tin/ý kiến, không có hành vi hạ nhục người.'),
 'C':('CLEAN','criticism','Phê bình sản phẩm/hành vi cụ thể, không phủ định giá trị con người.'),
 'P':('CLEAN','profanity_exclamation','Cảm thán có từ tục; không hướng công kích vào người.'),
 'D':('CLEAN','defense','Người bị nhắm đến đặt giới hạn hoặc tự bảo vệ, không đáp trả bằng xúc phạm.'),
 'I':('CLEAN','intervention','Can ngăn công kích, hướng trao đổi về vấn đề.'),
 'Q':('CLEAN','quote','Trích dẫn/thuật lại để phản đối hoặc làm rõ, không tán thành lời công kích.'),
 'A':('CLEAN','apology','Thừa nhận và xin lỗi hành vi trước; phát ngôn hiện tại không tiếp tục công kích.'),
 'R':('CLEAN','reconciliation','Đề nghị sửa sai/hòa giải mà không xúc phạm.'),
 'T':('TOXIC','directed_insult','Lời hạ nhục trực tiếp nhắm đến người, vượt khỏi góp ý nội dung.'),
 'H':('TOXIC','indirect_attack','Mỉa mai/hạ thấp năng lực hoặc phẩm giá người qua ngụ ý rõ trong ngữ cảnh.'),
 'M':('TOXIC','mixed_apology_attack','Có lời xin lỗi nhưng vẫn tiếp tục hạ nhục đối tượng trong cùng lượt.'),
 'V':('TOXIC','endorsed_quote','Dẫn lời xúc phạm để tán thành hoặc nối tiếp công kích, không phải trích dẫn phản đối.'),
 'U':('UNCERTAIN','ambiguous','Thiếu căn cứ để phân biệt đùa/khen với mỉa mai/công kích.'),
}

def normalized(text):return re.sub(r'\s+',' ',unicodedata.normalize('NFC',text).casefold()).strip()
def digest(value):return hashlib.sha256(value).hexdigest()
def file_sha(path):return digest(Path(path).read_bytes())
def atomic_json(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_suffix(path.suffix+'.tmp')
 temp.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');temp.replace(path)
def grams(text):
 text=normalized(text);return {text[i:i+5] for i in range(max(1,len(text)-4))}
def similarity(a,b):
 x,y=grams(a),grams(b);return len(x&y)/len(x|y) if x or y else 1.0

class Annotation(BaseModel):
 model_config=ConfigDict(extra='forbid')
 label:Literal['CLEAN','TOXIC','UNCERTAIN']
 category:str
 directed_at_user_id:str|None
 is_directed_attack:bool|None
 is_repeated_attack:bool
 is_apology:bool
 is_quote:bool
 label_reason:str=Field(min_length=12)
 label_source:Literal['synthetic']='synthetic'
 evidence_comment_ids:list[str]=Field(default_factory=list)
class Comment(BaseModel):
 model_config=ConfigDict(extra='forbid')
 comment_id:str
 parent_id:str|None
 user_id:str
 timestamp:AwareDatetime
 text:str=Field(min_length=2,max_length=8000)
 annotation:Annotation
class Thread(BaseModel):
 model_config=ConfigDict(extra='forbid')
 thread_id:str=Field(pattern=r'^SYN200_\d{4}$')
 topic:str
 title:str
 data_origin:Literal['synthetic']='synthetic'
 comments:list[Comment]=Field(min_length=10,max_length=30)
 participants:list[dict[str,str]]
 timestamp_origin:Literal['synthetic_schedule_not_real']='synthetic_schedule_not_real'
 evaluation_eligible:Literal[False]=False
 human_gold:Literal[False]=False
 source_catalogue_sha256:str
 @model_validator(mode='after')
 def consistent(self):
  ids=[c.comment_id for c in self.comments];users={c.user_id for c in self.comments}
  if len(ids)!=len(set(ids)) or not 3<=len(users)<=6:raise ValueError('Unique comments and 3..6 actual speakers required')
  if {p['user_id'] for p in self.participants}!=users:raise ValueError('Participant inventory mismatch')
  if any(not c.comment_id.startswith(self.thread_id+'_C') or not c.user_id.startswith(self.thread_id+'_U') for c in self.comments):raise ValueError('Comment/user IDs must belong to this fictional thread')
  seen={};previous=None
  for c in self.comments:
   if c.parent_id and c.parent_id not in seen:raise ValueError('Parent must be an earlier comment in this thread')
   if previous is not None and c.timestamp<=previous:raise ValueError('Strictly increasing timezone-aware synthetic timestamps required')
   previous=c.timestamp;a=c.annotation
   if a.directed_at_user_id and (a.directed_at_user_id not in users or a.directed_at_user_id==c.user_id):raise ValueError('Invalid attack target')
   if a.label=='CLEAN' and (a.is_directed_attack or a.is_repeated_attack):raise ValueError('Clean cannot assert an attack')
   if a.is_repeated_attack:
    if not a.is_directed_attack or not a.directed_at_user_id:raise ValueError('Repeated attack needs known target and directed attack')
    evidence=list(dict.fromkeys(a.evidence_comment_ids))
    if len(evidence)<2 or c.comment_id not in evidence:raise ValueError('Repeated evidence needs current + earlier turn')
    for eid in evidence:
     item=c if eid==c.comment_id else seen.get(eid)
     if not item or item.user_id!=c.user_id or not item.annotation.is_directed_attack or item.annotation.directed_at_user_id!=a.directed_at_user_id:raise ValueError('Repeated evidence must match actor and target across earlier turns')
   elif a.evidence_comment_ids:raise ValueError('Non-repeated comment cannot carry repeated evidence')
   seen[c.comment_id]=c
  return self

def read_catalogue(catalogue=CATALOGUE):
 result=[];current=None
 for path in sorted(Path(catalogue).glob('scenarios_*.txt')):
  for line in path.read_text(encoding='utf-8-sig').splitlines():
   if not line.strip() or line.startswith('#'):continue
   if line.startswith('@@'):
    parts=line[2:].split('|');current={'number':int(parts[0]),'topic':parts[1],'title':parts[2],'styles':parts[3] if len(parts)>3 else '', 'rows':[]};result.append(current)
   else:
    if current is None:raise ValueError('Dialogue without scenario header')
    parts=line.split('|',5)
    if len(parts)<5:
     match=re.fullmatch(r'([A-F])\.([A-Z]\+?)(\d+)([-A-F]) (.+)',line)
     if match:
      speaker,code,parent,target,body=match.groups();parts=[speaker,code,parent,target,*body.split('|',1)]
     else:
      neutral=re.fullmatch(r'([A-F])(\d+) (.+)',line)
      if not neutral:raise ValueError('Malformed authored row')
      speaker,parent,body=neutral.groups();parts=[speaker,'N',parent,'-',body]
    current['rows'].append(parts)
 numbers=[s['number'] for s in result]
 if len(numbers)!=len(set(numbers)) or numbers!=list(range(1,len(numbers)+1)):raise ValueError('Catalogue must be contiguous, unique and ordered')
 return result

def compile_thread(spec):
 number=spec['number'];tid=f'SYN200_{number:04d}';letters=sorted({row[0] for row in spec['rows']})
 if any(not re.fullmatch('[A-F]',s) for s in letters):raise ValueError('Only fictional A..F speakers')
 users={letter:f'{tid}_U{index+1:02d}' for index,letter in enumerate(letters)}
 styles={p.split('=',1)[0]:p.split('=',1)[1] for p in spec['styles'].split(';') if '=' in p}
 defaults=['rõ ý, dùng câu đầy đủ','ngắn, khẩu ngữ và viết tắt','lý giải, hỏi bằng chứng','đùa nhẹ, dùng emoji','điềm tĩnh, quan tâm cách ứng xử','nói thẳng, thiên về trải nghiệm']
 comments=[];start=datetime(2025,1,1,tzinfo=timezone.utc)+timedelta(days=number,hours=number%19)
 for index,row in enumerate(spec['rows'],1):
  speaker,code,parent,target,text=row[:5];extra=row[5] if len(row)>5 else '';repeated=code.endswith('+');code=code.rstrip('+')
  label,category,reason=CODES[code]
  if code=='U' and not extra.strip():raise ValueError('Ambiguous authored labels require a specific reason')
  cid=f'{tid}_C{index:02d}';parent_index=int(parent)
  if parent_index<0 or parent_index>=index:raise ValueError('Invalid authored parent reference')
  target_id=None if target=='-' else users[target]
  directed=True if label=='TOXIC' else None if label=='UNCERTAIN' else False
  if label=='TOXIC' and not target_id:raise ValueError('This catalogue requires grounded fictional target for toxic attacks')
  evidence=[]
  if repeated:
   evidence=[c['comment_id'] for c in comments if c['user_id']==users[speaker] and c['annotation']['is_directed_attack'] and c['annotation']['directed_at_user_id']==target_id]+[cid]
  annotation={'label':label,'category':category,'directed_at_user_id':target_id,'is_directed_attack':directed,'is_repeated_attack':repeated,
   'is_apology':code in ('A','M'),'is_quote':code in ('Q','V'),'label_reason':(extra or reason)+' Căn cứ: '+text,
   'label_source':'synthetic','evidence_comment_ids':evidence}
  comments.append({'comment_id':cid,'parent_id':None if not parent_index else f'{tid}_C{parent_index:02d}','user_id':users[speaker],
   'timestamp':(start+timedelta(seconds=index*43+(index*index)%23)).isoformat(),'text':text,'annotation':annotation})
 thread={'thread_id':tid,'topic':spec['topic'],'title':spec['title'],'data_origin':'synthetic','comments':comments,
  'participants':[{'user_id':users[letter],'fictional_speaker':letter,'style':styles.get(letter,defaults[index])} for index,letter in enumerate(letters)],
  'timestamp_origin':'synthetic_schedule_not_real','evaluation_eligible':False,'human_gold':False,
  'source_catalogue_sha256':digest(json.dumps(spec,ensure_ascii=False,sort_keys=True).encode())}
 return Thread.model_validate(thread).model_dump(mode='json')

def validate(threads):
 errors=[];comment_texts={};near_comments=[];parsed=[];all_ids=set()
 for item in threads:
  t=Thread.model_validate(item);parsed.append(t)
  if t.thread_id in all_ids:raise ValueError('Duplicate thread ID')
  all_ids.add(t.thread_id)
  for c in t.comments:
   key=normalized(c.text)
   if key in comment_texts:errors.append({'code':'duplicate_comment_text','comments':[comment_texts[key],c.comment_id]})
   comment_texts[key]=c.comment_id
 # Inverted character-gram index limits comparisons without skipping any eligible pair.
 postings=defaultdict(set);prior=[]
 for t in parsed:
  for c in t.comments:
   if len(normalized(c.text))<35:continue
   g=grams(c.text);hits=Counter(i for token in g for i in postings[token])
   for i,overlap in hits.items():
    other,og=prior[i];score=overlap/(len(g)+len(og)-overlap)
    if score>=.85:near_comments.append({'comments':[other,c.comment_id],'similarity':round(score,4)})
   index=len(prior);prior.append((c.comment_id,g))
   for token in g:postings[token].add(index)
 near_threads=[];thread_grams=[grams('\n'.join(c.text for c in t.comments)) for t in parsed]
 for i,t in enumerate(parsed):
  for j in range(i):
   a,b=thread_grams[i],thread_grams[j];score=len(a&b)/len(a|b)
   if score>=.60:near_threads.append({'threads':[parsed[j].thread_id,t.thread_id],'similarity':round(score,4)})
 if near_threads:errors.append({'code':'near_duplicate_threads','pairs':near_threads})
 if near_comments:errors.append({'code':'near_duplicate_comments','pairs':near_comments})
 comments=[c for t in parsed for c in t.comments];labels=Counter(c.annotation.label for c in comments)
 counts=Counter(len(t.comments) for t in parsed);participants=Counter(len({c.user_id for c in t.comments}) for t in parsed)
 return {'status':'PASS' if not errors else 'FAIL','threads':len(parsed),'comments':len(comments),'topics':dict(Counter(t.topic for t in parsed)),
  'labels':dict(labels),'categories':dict(Counter(c.annotation.category for c in comments)),
  'comment_count_distribution':dict(counts),'participant_count_distribution':dict(participants),
  'threads_without_toxic':sum(not any(c.annotation.label=='TOXIC' for c in t.comments) for t in parsed),
  'threads_ending_with_apology':sum(t.comments[-1].annotation.is_apology for t in parsed),
  'repeated_attack_comments':sum(c.annotation.is_repeated_attack for c in comments),
  'profanity_exclamation_clean':sum(c.annotation.category=='profanity_exclamation' for c in comments),
  'quote_comments':sum(c.annotation.is_quote for c in comments),'apology_comments':sum(c.annotation.is_apology for c in comments),
  'emoji_comments':sum(bool(re.search('[\U0001F300-\U0001FAFF]',c.text)) for c in comments),
  'teencode_comments':sum(bool(re.search(r'(?i)\b(?:ko|khum|mik|đc|bt|vcl|vkl|rep|ib|acc)\b',c.text)) for c in comments),
  'english_comments':sum(bool(re.search(r'(?i)\b(?:bro|sorry|game|lag|fan|anti|cringe|noob|loser|toxic|update|deadline|refund)\b',c.text)) for c in comments),
  'exact_duplicate_comments':sum(e['code']=='duplicate_comment_text' for e in errors),'near_duplicate_comments':len(near_comments),'near_duplicate_threads':len(near_threads),
  'thresholds':{'comment_char5_jaccard':.85,'comment_min_chars':35,'thread_char5_jaccard':.60},'errors':errors,
  'quality_limitations':['AI reference labels, not human gold.','Authored scenario catalogue, deterministic IDs/timestamps/annotation boilerplate; no population sampling.','Similarity checks cannot prove narrative variety or label correctness.','All timestamps/personas are fictional; human review required before training.']}

def export_csv(threads,data_root):
 comments=[];annotations=[]
 for t in threads:
  for c in t['comments']:
   comments.append({'thread_id':t['thread_id'],'topic':t['topic'],'data_origin':'synthetic',**{k:c[k] for k in ('comment_id','parent_id','user_id','timestamp','text')}})
   a={**c['annotation']};a['evidence_comment_ids']=json.dumps(a['evidence_comment_ids']);annotations.append({'thread_id':t['thread_id'],'comment_id':c['comment_id'],**a})
 for filename,rows in [('comments.csv',comments),('annotations.csv',annotations)]:
  path=Path(data_root)/filename;temp=path.with_suffix('.csv.tmp')
  with temp.open('w',encoding='utf-8-sig',newline='') as stream:
   writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
  temp.replace(path)

def write_report(root,report):
 atomic_json(root/'batches/validation_latest.json',report)
 lines=['# Synthetic conversations — quality report','',f"Threads: {report['threads']}/200; comments: {report['comments']}; status: {report['status']}",'',
 'Labels: '+json.dumps(report['labels'],ensure_ascii=False),'Topics: '+json.dumps(report['topics'],ensure_ascii=False),
 'Comments/thread: '+json.dumps(report['comment_count_distribution']),'Participants/thread: '+json.dumps(report['participant_count_distribution']),
 'No toxic comments in '+str(report['threads_without_toxic'])+' threads; final-turn apology in '+str(report['threads_ending_with_apology'])+' threads.',
 'Exact duplicate comments: '+str(report['exact_duplicate_comments'])+'; near duplicate comments: '+str(report['near_duplicate_comments'])+'; near duplicate threads: '+str(report['near_duplicate_threads']),
 'Similarity thresholds: '+json.dumps(report['thresholds']),'Categories: '+json.dumps(report['categories'],ensure_ascii=False),'',
 '## Limits','',*['- '+s for s in report['quality_limitations']],
 '- Utterances and microplots explicitly authored by Codex; no dialogue generated by swapping names into a shared template. Annotation reasons use shared category explanations plus the authored utterance.',
 '- This is research/training augmentation candidate data, NOT real-world T028 or an independent evaluation set. No training, auto-ingest, model inference, checkpoint or threshold changes.',
 '- UNCERTAIN must not be silently mapped to CLEAN/TOXIC. No train/validation/test split is created; keep complete threads together if splitting later.','']
 (root/'quality_report.md').write_text('\n'.join(lines),encoding='utf-8')

def update_progress(root,report,through):
 path=ROOT/'tasks/AUTO_PROGRESS.md';text=path.read_text(encoding='utf-8');marker='\n## Synthetic 200 — yêu cầu riêng'
 suffix=''
 if marker in text:
  text,old=text.split(marker,1)
  if '\n## ' in old:suffix=old[old.index('\n## '):]
 text+=marker+f"""\n\n- Trạng thái: {'DONE' if through==200 else 'IN_PROGRESS'}; dataset synthetic riêng, T028 vẫn BLOCKED và không được thay bằng dữ liệu này.
- Đã sinh và kiểm tra: {report['threads']}/200 hội thoại, {report['comments']} bình luận; {through//50}/4 batch hoàn thành. Nhãn tham khảo AI, không phải human gold.
- Nhãn: {json.dumps(report['labels'],ensure_ascii=False)}; exact duplicate={report['exact_duplicate_comments']}, near-comment={report['near_duplicate_comments']}, near-thread={report['near_duplicate_threads']}.
- File: scripts/synthetic_data/ (catalogue + compiler/validator), scripts/generate_synthetic_conversations.py, scripts/validate_synthetic_conversations.py; datasets/synthetic_conversations/ (JSON từng thread, 4 manifest batch, comments.csv, annotations.csv, manifest.json, README, quality_report); tests/test_synthetic_conversations.py.
- Checkpoint: datasets/synthetic_conversations/manifest.json; resume bằng `.venv/Scripts/python.exe -X utf8 scripts/generate_synthetic_conversations.py --through {min(200,((through//50)+1)*50)}`. Không ghi đè thread đã tồn tại nếu khác catalogue; không xóa dữ liệu người duyệt.
- Đã chạy compiler validation cấu trúc/parent/time/target/repeated và duplicate/near-duplicate cho {report['threads']} thread. Test pytest và audit cuối được bổ sung khi kết thúc.
- Việc kế tiếp: {'người dùng xem và rà nhãn; chưa train, UNCERTAIN giữ riêng' if through==200 else 'tiếp tục tự soạn catalogue và sinh batch tiếp theo'}. Không chạy T029–T033; không gọi API ngoài hay sửa model/0.41/test/DB.
"""
 path.write_text(text+suffix,encoding='utf-8')

def generate(through=200,data_root=DATA,catalogue=CATALOGUE,track_progress=True):
 if through not in (10,50,100,150,200):raise ValueError('Supported checkpoints: 10,50,100,150,200')
 root=Path(data_root);specs=read_catalogue(catalogue)
 if len(specs)<through:raise ValueError('Requested conversations have not been authored yet')
 threads=[compile_thread(s) for s in specs[:through]];report=validate(threads)
 if report['errors']:
  root.mkdir(parents=True,exist_ok=True);atomic_json(root/'batches/rejected_validation.json',report);raise ValueError('Quality gate rejected content; inspect rejected_validation.json and revise authored text, not thresholds')
 existing=sorted((root/'threads').glob('*.json'))
 if len(existing)>through:raise ValueError('Refuse to shrink an existing dataset')
 for t in threads:
  path=root/'threads'/(t['thread_id']+'.json')
  if path.exists():
   if json.loads(path.read_text(encoding='utf-8'))!=t:raise ValueError('Existing thread differs; refuse overwrite')
  else:atomic_json(path,t)
 export_csv(threads,root);write_report(root,report)
 for batch in range(1,through//50+1):
  group=threads[(batch-1)*50:batch*50];path=root/f'batches/batch_{batch:02d}.json'
  manifest={'batch':batch,'threads':50,'comments':sum(len(t['comments']) for t in group),'data_origin':'synthetic','label_source':'synthetic',
   'thread_ids':[t['thread_id'] for t in group],'checksums':{t['thread_id']:file_sha(root/'threads'/(t['thread_id']+'.json')) for t in group},'validation':validate(group)}
  manifest=json.loads(json.dumps(manifest,ensure_ascii=False))
  if path.exists() and json.loads(path.read_text(encoding='utf-8'))!=manifest:raise ValueError('Batch snapshot changed; do not overwrite')
  if not path.exists():atomic_json(path,manifest)
 manifest={'status':'GENERATED_REFERENCE_LABELS_NEED_HUMAN_REVIEW' if through==200 else 'IN_PROGRESS','target_threads':200,'actual_threads':through,'comments':report['comments'],
  'batches_complete':through//50,'next_thread':through+1 if through<200 else None,'data_origin':'synthetic','label_source':'synthetic','human_gold':False,
  'evaluation_eligible':False,'training_performed':False,'training_ready':False,'intended_use':'synthetic training augmentation candidate after review; not independent evaluation',
  'generation_method':'Codex-authored distinct scene catalogue; deterministic schema compiler; no network/paid API',
  'timestamp_origin':'fictional deterministic schedule, not collection/real publication times','labels':report['labels'],
  'thread_checksums':{t['thread_id']:file_sha(root/'threads'/(t['thread_id']+'.json')) for t in threads},
  'csv_checksums':{name:file_sha(root/name) for name in ('comments.csv','annotations.csv')},'validation_status':report['status']}
 atomic_json(root/'manifest.json',manifest)
 if track_progress:update_progress(root,report,through)
 return report

def main():
 p=argparse.ArgumentParser();p.add_argument('--through',type=int,choices=[10,50,100,150,200],default=200);a=p.parse_args();report=generate(a.through)
 print(json.dumps({k:report[k] for k in ('status','threads','comments','labels','exact_duplicate_comments','near_duplicate_comments','near_duplicate_threads')},ensure_ascii=False))
