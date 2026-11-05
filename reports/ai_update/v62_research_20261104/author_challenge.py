"""Six individually authored scenes after V62_LOCK, before first scoring."""
import json,sys
from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import Counter
from difflib import SequenceMatcher
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent;D=R/'datasets/fixtures/v62_postfreeze_challenge_v1'
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha,normalized
from evaluate_context_recovery import load_inputs
SCENES=[('club_radio',[
('N01',None,'Mình gửi kịch bản cho buổi phát thanh của câu lạc bộ, còn thiếu phần dẫn giữa hai bài hát.','CLEAN',None),
('N02',1,'@N01 đúng là loại người chỉ biết đổ lỗi, từ đầu tới giờ ai cũng làm hộ.','TOXIC','N01'),
('N01',2,'Phần dẫn mình nhận viết, mình đang hỏi thứ tự bài hát để nối cho khớp.','CLEAN',None),
('N03',2,'Góp ý việc còn thiếu thôi, đừng kết luận về con người bạn ấy.','CLEAN',None),
('N02',3,'@N01 nói nhiều mà tự làm không ra cái gì, thế mà vẫn muốn chỉ huy.','TOXIC','N01'),
('N03',5,'Tối mình rảnh nửa tiếng, mình với bạn N01 sẽ đọc lại đoạn chuyển cùng nhau.','CLEAN',None)]),
('novel_translation',[
('N01',None,'Bản dịch chương ba có nhiều lời mắng của người bảo vệ, mọi người đọc thấy hợp giọng chưa?','CLEAN',None),
('N02',1,'Người bảo vệ quát “cậu đúng là đồ vô dụng” rồi đuổi nhân vật ra khỏi phòng, giọng này hơi nặng.','CLEAN',None),
('N03',2,'Mình nghĩ nên giữ mức khó chịu của nhân vật, nhưng chú thích hoàn cảnh ngay sau đó.','CLEAN',None),
('N01',3,'Mình sẽ sửa lời dẫn để người đọc phân biệt người kể chuyện với lời thoại.','CLEAN',None),
('N02',4,'Tác giả dùng câu “you are brainless” trong bản nháp, tớ nghĩ nên chú thích giọng nói của nhân vật.','CLEAN',None),
('N03',5,'Ừ, chú thích tên người nói ở đầu dòng sẽ rõ hơn chỉ dùng dấu ngoặc kép.','CLEAN',None)]),
('badminton_booking',[
('N01',None,'Lịch sân cầu lông tuần này đổi sang chiều thứ bảy, mình gửi lại mã đặt sân nhé.','CLEAN',None),
('N02',1,'bro @N01 you are a pathetic loser, cái lịch sân bé tí cũng xếp lộn hoài.','TOXIC','N01'),
('N01',2,'Mình đã đổi vì sân cũ bị sửa mái, lịch xác nhận mới nằm ở ảnh bên dưới.','CLEAN',None),
('N03',1,'@N01, mày chỉ là máy nhai lại, chẳng có suy nghĩ riêng.','TOXIC','N01'),
('N01',4,'Mình có thể nhận lỗi ghi thiếu thông tin, nhưng không chấp nhận những lời hạ thấp như vậy.','CLEAN',None),
('N03',5,'Tôi xin lỗi vì lời vừa nói về bạn. Tôi sẽ đọc kỹ tin xác nhận trước khi hỏi tiếp.','CLEAN',None)]),
('bus_schedule',[
('N01',None,'Ngày hội có thêm chuyến xe đưa đón, cần một người cập nhật bảng giờ ở cổng.','CLEAN',None),
('N03',1,'Mình nhận cập nhật, nhưng chờ nhà xe xác nhận giờ về rồi mới in bảng được.','CLEAN',None),
('N02',2,'@N03 chỉ là cục đá buộc vào chân cả đội, có bạn là mọi thứ chậm lại.','TOXIC','N03'),
('N03',3,'Mình đang chờ thông tin để tránh in sai, ai có số điều phối nhà xe thì gửi giúp.','CLEAN',None),
('N02',4,'@N03 ngồi đó chỉ tổ chật chỗ, không ai cần phần góp mặt của bạn ở đây.','TOXIC','N03'),
('N01',5,'Dừng hạ thấp người đang phụ trách đi. Mình gọi nhà xe để lấy giờ rồi cùng sửa bảng.','CLEAN',None)]),
('hackathon_retry',[
('N01',None,'Nhánh thử nghiệm hiện retry ba lần khi máy chủ đóng kết nối, mình muốn nghe góp ý về cách ghi log.','CLEAN',None),
('N02',1,'Đoạn mã bạn tự làm không ra cái gì cả, mình góp ý đổi cách xử lý timeout.','CLEAN',None),
('N03',2,'Nhận xét cụ thể chỗ nào mất trace ID nhé, mình mở pull request bổ sung phần đó.','CLEAN',None),
('N01',3,'Tôi tự làm chẳng ra gì ở phần retry, đang đọc lại tài liệu rồi thử tiếp.','CLEAN',None),
('N02',4,'Mình thử thư viện tên brainless trong nhánh sandbox, tên kỳ nhưng phần parse log khá gọn.','CLEAN',None),
('N03',5,'Nhớ đo số request trước và sau, đừng để mỗi retry lại tạo thêm một vòng retry nữa.','CLEAN',None)]),
('fanclub_event',[
('N01',None,'Mình vừa chia thứ tự tiết mục fanclub, ai cần đổi giờ lên sân khấu thì báo trước tối nay.','CLEAN',None),
('N02',1,'Trong tin trước người ta gọi bạn “đồ ngu”. Nhưng @N01 mày ngồi im cho đỡ phí oxy của mọi người.','TOXIC','N01'),
('N03',2,'Trích lời người khác không làm phần công kích sau đó thành ổn đâu, nói về giờ diễn thôi.','CLEAN',None),
('N01',2,'Bạn muốn đổi tiết mục nào thì gửi tên bài, mình sẽ đối chiếu lịch tổng.','CLEAN',None),
('N02',4,'@N01 bạn đúng là loại người chỉ biết nhận công, việc khó thì để cả nhóm chịu.','TOXIC','N01'),
('N03',5,'Thôi bạn N02, ghi đúng phần việc rồi dừng gọi nhau bằng mấy từ đó.','CLEAN',None)])]

if __name__=='__main__':
    lock=P/'V62_LOCK.json';frozen=json.loads(lock.read_text());assert not (D/'manifest.json').exists()
    for name,digest in frozen['files'].items():assert file_sha(R/name)==digest
    prior=[normalized(c['text']) for item in load_inputs() for c in item['payload']['comments']]
    for name in ('fresh10_regression_v1/inputs','nov10_regression_v1/inputs','fresh10_postfix_holdout_v1/threads','fresh10_postfix_holdout_v2/threads','nov10_audit_challenge_v1/threads'):
        prior += [normalized(c['text']) for path in (R/'datasets/fixtures'/name).glob('*.json') for c in json.loads(path.read_text())['comments']]
    threads=[];base=datetime(2026,11,4,16,tzinfo=timezone.utc)
    for i,(topic,rows) in enumerate(SCENES,1):
        comments=[]
        for j,(user,parent,text,label,target) in enumerate(rows,1):
            assert parent is None or 0<parent<j
            comments.append({'comment_id':f'c{j:02}','user_id':user,'parent_id':f'c{parent:02}' if parent else None,
                'timestamp':(base+timedelta(hours=i,minutes=j*2)).isoformat(),'text':text,
                'annotation':{'label':label,'directed_at_user_id':target,'is_directed_attack':label=='TOXIC','label_source':'synthetic_reference','human_gold':False}})
        threads.append({'thread_id':f'V62_POSTFREEZE_{i:02}','topic':topic,'data_origin':'synthetic','comments':comments})
    texts=[normalized(c['text']) for t in threads for c in t['comments']];assert len(set(texts))==36 and not set(texts)&set(prior)
    near=[]
    for i,text in enumerate(texts):
        for other in prior+texts[:i]:
            if min(len(text),len(other))/max(len(text),len(other))>=.85:
                ratio=SequenceMatcher(None,text,other).ratio()
                if ratio>=.85:near.append({'comment_index':i,'ratio':ratio})
    for t in threads:atomic_json(D/'threads'/(t['thread_id']+'.json'),t)
    atomic_json(D/'manifest.json',{'threads':6,'comments':36,'origin':'synthetic','label_source':'synthetic_reference','human_gold':False,
        'training_forbidden':True,'author_blind':False,'new_before_first_scoring':True,'processor_lock_sha256':file_sha(lock),
        'authoring':'Individual same-AI-authored scenes after frozen v6.2, before inference; grammar controls and unseen coverage; not independent real evaluation',
        'labels':dict(Counter(c['annotation']['label'] for t in threads for c in t['comments'])),'exact_duplicates':0,
        'near_duplicate_threshold':.85,'near_duplicate_warnings':near,'overlap_checked':'old890 plus Fresh10/NOV10 and three previously viewed small challenges',
        'thread_sha256':{t['thread_id']:file_sha(D/'threads'/(t['thread_id']+'.json')) for t in threads}})
    print(json.dumps({'threads':6,'comments':36,'near_duplicate_warnings':near}))
