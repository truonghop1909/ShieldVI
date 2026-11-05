"""Small individual scenes authored after experiment_lock_v2, before any scoring."""
import json,sys
from pathlib import Path
from collections import Counter
from datetime import datetime,timedelta,timezone
from difflib import SequenceMatcher
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha,normalized
D=R/'datasets/fixtures/fresh10_postfix_holdout_v2'
SCENES=[('repair_board',[
('Q01',None,'Mình vừa thử bo nguồn sau khi thay tụ, đèn báo vẫn chớp hai lần.','CLEAN',None),
('Q02',1,'Bạn đúng là đồ ngu, chưa đo điện áp mà đã cắm nguồn vào rồi.','TOXIC','Q01'),
('Q01',2,'Mình có đo trước khi lắp, số đo nằm trong ảnh thứ ba.','CLEAN',None),
('Q03',2,'Đừng gọi người khác như vậy, hỏi lại phép đo là đủ rồi.','CLEAN',None),
('Q02',3,'Mày vô dụng thật, đọc số trên đồng hồ cũng không xong.','TOXIC','Q01'),
('Q02',5,'Tôi xin lỗi vì đã gọi bạn là “đồ ngu”; tôi sẽ xem lại ảnh đo mạch.','CLEAN',None)]),
('photo_book',[
('Q01',None,'Cuốn ảnh phóng sự này ghi cả lời phỏng vấn dưới mỗi tấm hình.','CLEAN',None),
('Q03',1,'Đoạn nhân vật kể bị gọi là “kẻ vô dụng” nên để trong ngoặc kép.','CLEAN',None),
('Q02',2,'Đúng, đó là lời người được phỏng vấn nhắc lại, không phải lời của biên tập viên.','CLEAN',None),
('Q01',2,'Mình sẽ thêm dòng phân biệt lời dẫn với phần trích nguyên văn.','CLEAN',None),
('Q02',4,'Tấm cuối hơi thiếu sáng, kéo vùng tối một chút là nhìn rõ nét mặt.','CLEAN',None),
('Q03',5,'Tớ thích giữ hạt phim, tăng sáng vừa phải thôi để ảnh khỏi phẳng.','CLEAN',None)]),
('football_water',[
('Q01',None,'Mai đá sân số ba, mình mang bình nước lớn cho cả đội nhé.','CLEAN',None),
('Q02',1,'Mày ngu thật, sân có vòi nước rồi còn vác cái bình đi làm gì.','TOXIC','Q01'),
('Q03',1,'Bạn đúng là đồ vô dụng, chia việc nhỏ như thế cũng không biết tính.','TOXIC','Q01'),
('Q01',2,'Vòi nước sân bị khóa, anh quản lý đã nhắn trong nhóm sáng nay.','CLEAN',None),
('Q03',4,'Ờ mình chưa đọc tin đó. Mình nhận lỗi vì đã chửi bạn trước khi hỏi rõ.','CLEAN',None),
('Q02',4,'Vậy mình mang thêm cốc giấy, đỡ phải uống chung một vòi.','CLEAN',None)]),
('refund_meeting',[
('Q01',None,'Mình đề nghị trả lại phần phí vật liệu chưa dùng sau buổi workshop.','CLEAN',None),
('Q02',1,'Tôi hiểu chuyện hoàn tiền, nhưng bạn cãi cùn làm cả phòng phải ngồi đợi.','TOXIC','Q01'),
('Q01',2,'Mình chỉ cần biết số tiền đã chi và số dư để mọi người đối chiếu.','CLEAN',None),
('Q03',3,'Kế toán gửi hóa đơn lên bảng chung rồi mình chốt khoản trả lại.','CLEAN',None),
('Q02',3,'Mày ngồi im cho đỡ phí oxy của cả phòng.','TOXIC','Q01'),
('Q01',5,'Nghe câu đó mình rất mệt. Mình sẽ gửi yêu cầu bằng văn bản thay vì ngồi đây tiếp.','CLEAN',None)])]

if __name__=='__main__':
    lock=P/'experiment_lock_v2.json';frozen=json.loads(lock.read_text())
    assert file_sha(R/'services/moderation-ai/app/experiments/fresh10_v6.py')==frozen['experimental_module_sha256']
    assert not (D/'manifest.json').exists() and not (P/'final_challenge').exists()
    base=datetime(2026,11,4,tzinfo=timezone.utc);threads=[]
    for i,(topic,rows) in enumerate(SCENES,1):
        tid=f'FRESH10_FINAL_{i:02}';comments=[]
        for j,(user,parent,text,label,target) in enumerate(rows,1):
            assert parent is None or 0<parent<j
            comments.append({'comment_id':f'c{j:02}','user_id':user,'parent_id':f'c{parent:02}' if parent else None,
                'timestamp':(base+timedelta(hours=i,minutes=j*3)).isoformat(),'text':text,
                'annotation':{'label':label,'directed_at_user_id':target,'is_directed_attack':label=='TOXIC',
                              'label_source':'synthetic_reference','human_gold':False}})
        assert len({c['user_id'] for c in comments})==3
        threads.append({'thread_id':tid,'topic':topic,'data_origin':'synthetic','comments':comments})
    corpus=[]
    for folder in ('datasets/fixtures/fresh10_regression_v1/inputs','datasets/fixtures/fresh10_postfix_holdout_v1/threads','datasets/synthetic_genz/threads'):
        corpus += [normalized(c['text']) for p in (R/folder).glob('*.json') for c in json.loads(p.read_text(encoding='utf-8'))['comments']]
    texts=[normalized(c['text']) for t in threads for c in t['comments']]
    assert len(set(texts))==24 and not set(texts)&set(corpus)
    near=[]
    for i,text in enumerate(texts):
        for other in corpus+texts[:i]:
            if min(len(text),len(other))/max(len(text),len(other))<.85:continue
            ratio=SequenceMatcher(None,text,other).ratio()
            if ratio>=.85:near.append({'comment_index':i,'ratio':ratio,'other_text':other})
    for t in threads:atomic_json(D/'threads'/(t['thread_id']+'.json'),t)
    atomic_json(D/'manifest.json',{'threads':4,'comments':24,'origin':'synthetic','label_source':'synthetic_reference',
        'human_gold':False,'training_forbidden':True,'author_blind':False,'new_before_first_scoring':True,
        'authoring':'Individual Codex-authored scenes after v6.1 freeze; no template substitution or paid API',
        'experiment_lock_sha256':file_sha(lock),'exact_duplicates':0,'near_duplicate_threshold':.85,'near_duplicate_warnings':near,
        'labels':dict(Counter(c['annotation']['label'] for t in threads for c in t['comments'])),
        'thread_sha256':{t['thread_id']:file_sha(D/'threads'/(t['thread_id']+'.json')) for t in threads}})
    print(json.dumps({'threads':4,'comments':24,'near_duplicate_warnings':near}))
