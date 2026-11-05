"""24 individual control/coverage comments authored after challenge_lock.json."""
import json,sys
from pathlib import Path
from collections import Counter
from datetime import datetime,timedelta,timezone
from difflib import SequenceMatcher
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent;D=R/'datasets/fixtures/nov10_audit_challenge_v1'
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha,normalized
SCENES=[('volunteer_inventory',[
('N01',None,'Mình nhập xong bảng kho áo quyên góp, còn ba kiện chưa có số lượng.','CLEAN',None),
('N02',1,'Bạn là một gánh nặng biết đi, lúc nào cũng bắt cả đội gánh hộ.','TOXIC','N01'),
('N01',2,'Ba kiện đó chưa mở niêm phong nên mình để trống thay vì đoán số.','CLEAN',None),
('N03',2,'Nói người ta như vậy có giúp kiểm kho nhanh hơn không nhỉ?','UNCERTAIN',None),
('N02',3,'Nhóm có bạn cũng chỉ thêm một miệng ăn bám, chẳng được tích sự nào.','TOXIC','N01'),
('N03',5,'Đừng hạ nhục người đang kiểm hàng. Chiều mình tới đếm ba kiện còn lại.','CLEAN',None)]),
('book_club_quotes',[
('N01',None,'Mình đọc truyện thấy nhân vật luôn bị người quản đốc gọi bằng biệt danh.','CLEAN',None),
('N02',1,'Tác giả viết câu “mày đúng là đồ ngu” để cho thấy cách quản đốc đối xử với thợ.','CLEAN',None),
('N03',2,'Đoạn này làm mình khó chịu vì quyền lực của người quản đốc chứ không phải vì người thợ.','CLEAN',None),
('N01',3,'Nhận xét về nhịp kể của bạn hợp lý, chương sau chuyển cảnh khá gấp.','CLEAN',None),
('N03',4,'Nếu trích câu xúc phạm thì nên kèm nhân vật nói và hoàn cảnh, tránh hiểu nhầm người viết bình.','CLEAN',None),
('N02',5,'Mình thêm tên nhân vật vào ngoặc, rồi ghi số trang ngay sau câu trích.','CLEAN',None)]),
('map_editing',[
('N01',None,'Đây là sơ đồ các cửa thoát của phòng triển lãm, mọi người xem giúp hướng mũi tên.','CLEAN',None),
('N02',1,'Bạn đúng là đồ ngu khi đặt mũi tên quay vào vách.','TOXIC','N01'),
('N01',2,'Mũi tên đó chỉ cửa ở gian bên cạnh, mình sẽ thêm đường nét đứt cho rõ.','CLEAN',None),
('N02',3,'Mày vô dụng thật, giải thích cũng không làm bản vẽ đỡ rối.','TOXIC','N01'),
('N03',4,'Đừng công kích bạn ấy. Mình sẽ đối chiếu sơ đồ với ảnh chụp gian phòng.','CLEAN',None),
('N02',5,'Tôi xin lỗi vì đã gọi bạn là đồ ngu. Tôi sẽ gửi vị trí cần đổi bằng tọa độ.','CLEAN',None)]),
('separate_actors',[
('N01',None,'Mình vừa chia ca trực bàn đăng ký, ai bận giờ nào hãy ghi vào bảng.','CLEAN',None),
('N02',1,'Xin lỗi vì nóng, nhưng mày đúng là đồ ngu khi xếp ca thế này.','TOXIC','N01'),
('N01',2,'Mình có thể đổi ca, nhưng mình không chấp nhận bị xúc phạm trong nhóm.','CLEAN',None),
('N03',1,'Bạn vô dụng thật, việc chia vài ca cũng không làm nổi.','TOXIC','N01'),
('N01',4,'Mình đã gửi đường dẫn để mọi người chọn lại giờ có thể tham gia.','CLEAN',None),
('N03',5,'Tôi xin lỗi vì đã nói bạn vô dụng. Tôi đăng ký ca chiều và sẽ tới sớm.','CLEAN',None)])]

if __name__=='__main__':
    lock=P/'challenge_lock.json';frozen=json.loads(lock.read_text());assert not (D/'manifest.json').exists()
    assert file_sha(R/'services/moderation-ai/app/experiments/fresh10_v6.py')==frozen['experimental_module_sha256']
    existing=[]
    for folder in ('nov10_regression_v1/inputs','fresh10_regression_v1/inputs','fresh10_postfix_holdout_v1/threads','fresh10_postfix_holdout_v2/threads'):
        existing += [normalized(c['text']) for p in (R/'datasets/fixtures'/folder).glob('*.json') for c in json.loads(p.read_text(encoding='utf-8'))['comments']]
    threads=[];base=datetime(2026,11,4,13,tzinfo=timezone.utc)
    for i,(topic,rows) in enumerate(SCENES,1):
        comments=[]
        for j,(user,parent,text,label,target) in enumerate(rows,1):
            assert parent is None or 0<parent<j
            comments.append({'comment_id':f'c{j:02}','user_id':user,'parent_id':f'c{parent:02}' if parent else None,'text':text,
                'timestamp':(base+timedelta(hours=i,minutes=2*j)).isoformat(),
                'annotation':{'label':label,'directed_at_user_id':target,'is_directed_attack':label=='TOXIC',
                              'label_source':'synthetic_reference','human_gold':False}})
        threads.append({'thread_id':f'NOV10_AUDIT_CHALLENGE_{i:02}','topic':topic,'data_origin':'synthetic','comments':comments})
    texts=[normalized(c['text']) for t in threads for c in t['comments']]
    assert len(set(texts))==24 and not set(texts)&set(existing)
    near=[]
    for i,text in enumerate(texts):
        for other in existing+texts[:i]:
            if min(len(text),len(other))/max(len(text),len(other))>=.85:
                ratio=SequenceMatcher(None,text,other).ratio()
                if ratio>=.85:near.append({'index':i,'ratio':ratio})
    for thread in threads:atomic_json(D/'threads'/(thread['thread_id']+'.json'),thread)
    atomic_json(D/'manifest.json',{'threads':4,'comments':24,'origin':'synthetic','label_source':'synthetic_reference','human_gold':False,
        'training_forbidden':True,'author_blind':False,'new_before_first_scoring':True,'experiment_lock_sha256':file_sha(lock),
        'authoring':'Individual AI-authored scenes after audit/freeze, before first inference; same author, no independent evaluation claim',
        'labels':dict(Counter(c['annotation']['label'] for t in threads for c in t['comments'])),'exact_duplicate_comments':0,
        'near_duplicate_threshold':.85,'near_duplicate_warnings':near,'overlap_checked':'NOV10/Fresh10 and the two prior Fresh10 small challenges',
        'thread_sha256':{t['thread_id']:file_sha(D/'threads'/(t['thread_id']+'.json')) for t in threads}})
    print(json.dumps({'threads':4,'comments':24,'near_duplicate_warnings':near}))
