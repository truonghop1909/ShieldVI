"""Twelve newly authored scenes after rule freeze; loops compile metadata only."""
import json,hashlib
from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import Counter
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent;D=R/'datasets/fixtures/repeated_holdout_20261103'
lock=json.loads((P/'frozen_rule_lock.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert all(sha(R/'services/moderation-ai/app'/name)==h for name,h in lock['rule_sha256'].items())
# (author, one-based parent index, exact authored prose, reference, attack target)
scenes=[('audio_equipment',[
('Nhi',None,'Con DAC này có tiếng nền khi cắm cổng trước, mọi người thử chưa?','CLEAN',None),
('Long',1,'Cậu chẳng có chút giá trị gì trong nhóm thu âm này.','TOXIC','Nhi'),
('Nhi',2,'Mình đang hỏi cách nối dây, không hỏi đánh giá về bản thân.','CLEAN',None),
('My',2,'Nhi mô tả lỗi có ích mà, mình cũng gặp tiếng xì đó.','CLEAN',None),
('Long',3,'Sự tồn tại của cậu chỉ gây phiền cho mấy buổi test âm thanh.','TOXIC','Nhi'),
('My',5,'Đừng biến việc sửa nhiễu thành màn hạ nhục thành viên.','CLEAN',None),
('Nhi',4,'Tối mình đổi dây USB rồi gửi đoạn thu so sánh nhé.','CLEAN',None)]),
('volleyball',[
('Vy',None,'Tụi mình thử đổi người chuyền hai ở set tới được không?','CLEAN',None),
('Khoa',1,'Cậu đúng là cục chì cả đội phải kéo theo suốt trận.','TOXIC','Vy'),
('Vy',2,'Nếu bóng một chưa ổn thì nói vị trí để mình tập.','CLEAN',None),
('An',3,'Vy đỡ bước một được, đội đang thiếu người gọi bóng thôi.','CLEAN',None),
('Khoa',3,'Có cậu hay không cũng chẳng ai cần trong đội hình của tụi này.','TOXIC','Vy'),
('An',5,'Đội trưởng quyết định chiến thuật, không ai được đuổi người bằng lời miệt thị.','CLEAN',None)]),
('group_research',[
('Bao',None,'Bản tổng hợp tài liệu đã thêm cột DOI ở cuối bảng.','CLEAN',None),
('Lam',1,'Xin lỗi vì đã gọi bạn ngu trước cuộc họp, nhưng bạn vô dụng trong việc tổng hợp tài liệu.','TOXIC','Bao'),
('Bao',2,'Có chữ xin lỗi rồi mà bạn vẫn tiếp tục hạ thấp mình.','CLEAN',None),
('Hue',2,'Mình kiểm được ba DOI bị thiếu, để mình bổ sung cùng Bảo.','CLEAN',None),
('Lam',3,'Đầu bạn chắc chỉ đủ để đội cái mũ chống nắng chứ nhớ lịch gì.','TOXIC','Bao'),
('Lam',4,'Mình xin lỗi vì đã gọi bạn ngu ở cuộc họp vừa rồi.','CLEAN',None),
('Hue',6,'Ghi nhận lời xin lỗi, nhóm vẫn cần thống nhất cách góp ý.','CLEAN',None)]),
('map_video',[
('Quang',None,'Mày nói ngu thế thì ai dám tin video bản đồ tuyến xe này?','TOXIC','Linh'),
('Linh',1,'Mình sẽ bổ sung mốc đổi tuyến và ghi chú ngay dưới video.','CLEAN',None),
('Tam',1,'Có thể dẫn lịch tuyến chính thức, đừng xúc phạm người dựng clip.','CLEAN',None),
('Linh',2,'Mình đã đặt liên kết thông báo của bến xe vào phần mô tả.','CLEAN',None),
('Quang',4,'Bạn đúng là đồ ngu khi nghĩ thêm một link là xong chuyện.','TOXIC','Linh'),
('Tam',5,'Thông tin sửa được rồi, việc hạ nhục bạn ấy không giúp ích gì.','CLEAN',None)]),
('quoted_support_ticket',[
('Mai',None,'Mình cần chép nguyên văn lời lẽ khách gửi để báo quản trị.','CLEAN',None),
('Dung',1,'Phiếu trước có câu “có mày hay không cũng chẳng ai cần” nên mình lưu ảnh làm chứng.','CLEAN',None),
('Nga',2,'Nhớ che tên và số đơn trước khi gửi nhé.','CLEAN',None),
('Dung',1,'Mình trích dẫn “sự tồn tại của mày chỉ gây phiền” để giải thích vì sao ticket bị báo cáo.','CLEAN',None),
('Mai',4,'Đã rõ đây là trích dẫn, không phải Dũng đang nói với mình.','CLEAN',None),
('Nga',5,'Bản đã che thông tin cá nhân nằm trong phiếu nội bộ rồi.','CLEAN',None)]),
('intervention',[
('Ha',None,'Clip đọc truyện của mình có chỗ bị mất tiếng.','CLEAN',None),
('Son',1,'Bạn đừng bảo người ta ngậm miệng đi, góp ý đoạn mic mất tín hiệu thôi.','CLEAN',None),
('Le',2,'Mình gửi mốc 02:18 để Hà kiểm lại.','CLEAN',None),
('Son',1,'Đừng nói có bạn ấy hay không cũng chẳng ai cần; nhóm này cho phép người mới tập đọc.','CLEAN',None),
('Ha',3,'Mình thay được track từ phút đó, cảm ơn mọi người.','CLEAN',None),
('Le',5,'Bản mới nghe rõ chữ hơn rồi, đăng lịch đọc tiếp nha.','CLEAN',None)]),
('mutual_single_attacks',[
('Lan',None,'Có nên chọn màu cam cho bìa fanzine không?','CLEAN',None),
('Dat',1,'Mày ngu thật khi phối cái màu đó với logo xanh.','TOXIC','Lan'),
('Lan',2,'Còn bạn đúng là đồ vô dụng trong nhóm phối màu này.','TOXIC','Dat'),
('Thu',3,'Hai người đều đang xúc phạm nhau, quay lại bảng màu đi.','CLEAN',None),
('Dat',4,'Mình tạm dừng nói chuyện để nhóm làm nốt.','CLEAN',None),
('Lan',4,'Mình sẽ gửi một phương án khác cho Thu xem.','CLEAN',None)]),
('two_actors_one_target',[
('Truc',None,'Mình rao chiếc máy đọc sách bị xước viền, đã ghi trong mô tả.','CLEAN',None),
('Huy',1,'Mày đúng là đồ ngu mà cũng đòi bán đồ công nghệ.','TOXIC','Truc'),
('Phuc',1,'Bạn vô dụng thật, đăng một món cũng không ra hồn.','TOXIC','Truc'),
('Truc',2,'Mình có ảnh lỗi và giá rõ ràng, các bạn có thể hỏi về máy.','CLEAN',None),
('Huy',4,'Dung lượng bộ nhớ còn bao nhiêu vậy?','CLEAN',None),
('Phuc',4,'Cho mình xem cổng sạc dưới ánh sáng được không.','CLEAN',None)]),
('ambiguous_root_targets',[
('Vu',None,'Mày ngu thật, đọc có mấy dòng cũng không hiểu ý.','TOXIC',None),
('Chau',None,'Mọi người đang nói bài nào vậy, mình mới vào nhóm.','CLEAN',None),
('Nam',2,'Mình cũng chưa có đường dẫn, chờ chủ bài gửi nhé.','CLEAN',None),
('Vu',None,'Mày vô dụng trong mấy việc đơn giản thế này.','TOXIC',None),
('Chau',3,'Chưa biết đang nói với ai thì mình không kết luận target.','CLEAN',None),
('Nam',5,'Mình xin link gốc để đọc cho đủ ngữ cảnh.','CLEAN',None)]),
('explicit_target_not_reply_recipient',[
('Ha',None,'Lịch workshop in risograph mới có thêm ca chiều.','CLEAN',None),
('Tuan',1,'Mình nhận gửi thông báo vào nhóm thiết kế.','CLEAN',None),
('Minh',2,'Ha mày ngu thật, xếp lịch kiểu đó ai đi nổi.','TOXIC','Ha'),
('Ha',3,'Mình có thể đổi ca nếu mọi người báo trùng lịch.','CLEAN',None),
('Minh',2,'Ha bạn vô dụng trong cả việc lên lịch cho vài người.','TOXIC','Ha'),
('Tuan',5,'Bạn đang trả lời mình nhưng lời hạ nhục lại nhắm Hà, mình sẽ báo quản trị.','CLEAN',None)]),
('long_gap_exchange',[
('Tien',None,'Mày ngu thật khi diễn giải số liệu về đường chạy thế này.','TOXIC','Phuong'),
('Phuong',1,'Mình sẽ kiểm lại biểu đồ và chú thích từng nhóm tuổi.','CLEAN',None),
('Duy',2,'Tớ tìm bản khảo sát gốc cho mọi người đọc chung.','CLEAN',None),
('Phuong',2,'Bảng cập nhật có cả cỡ mẫu, mình gửi sau buổi tập.','CLEAN',None),
('Tien',4,'Bạn vô dụng khi đến giờ vẫn chưa giải thích rõ con số đó.','TOXIC','Phuong'),
('Duy',5,'Khoảng nghỉ hơn một tiếng không làm lời xúc phạm mới trở nên chấp nhận được.','CLEAN',None)]),
('benign_speech_exercises',[
('Binh',None,'Mình quay thử bài hướng dẫn thở bằng mũi cho lớp diễn xuất.','CLEAN',None),
('Kien',1,'Đến lượt này mày ngậm miệng lại để hơi đi qua mũi, rồi thả lỏng vai nhé.','CLEAN',None),
('Hoa',2,'Đúng rồi, phần chú thích nhớ ghi đây là bài tập giọng.','CLEAN',None),
('Kien',1,'Ở nhịp tiếp theo mày ngậm miệng lại và đếm thầm bốn giây, đừng gồng cổ.','CLEAN',None),
('Binh',4,'Mình thử được rồi, câu hướng dẫn cần đọc chậm thêm một chút.','CLEAN',None),
('Hoa',5,'Clip tập thở không cần nhạc nền, giữ tiếng đếm rõ là được.','CLEAN',None)])]
if (D/'manifest.json').exists():raise FileExistsError('Never regenerate a scored challenge')
threads=[];base=datetime(2026,11,3,0,tzinfo=timezone.utc)
for i,(topic,rows) in enumerate(scenes,1):
    tid=f'REP_FRESH_{i:02}';comments=[];seen=Counter()
    for j,(user,parent,prose,label,target) in enumerate(rows,1):
        minute=j-1 if i!=11 or j<5 else 61+j
        repeated=bool(target and seen[(user,target)])
        if target:seen[(user,target)]+=1
        comments.append({'comment_id':f'{tid}_c{j:02}','user_id':user,'parent_id':f'{tid}_c{parent:02}' if parent else None,
            'timestamp':(base+timedelta(hours=i,minutes=minute)).isoformat(),'text':prose,
            'annotation':{'label':label,'category':'directed_attack' if label=='TOXIC' else 'non_attack',
                'directed_at_user_id':target,'is_directed_attack':label=='TOXIC','is_repeated_attack':repeated,
                'label_reason':'AI-authored scene reference; target requires this exchange, reply alone is not an attack.',
                'label_source':'synthetic','human_gold':False}})
    threads.append({'thread_id':tid,'topic':topic,'data_origin':'synthetic','human_gold':False,'comments':comments})
for t in threads:(D/(t['thread_id']+'.json')).write_text(json.dumps(t,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
texts=[c['text'] for t in threads for c in t['comments']]
assert len(set(texts))==len(texts)
source={c['text'] for p in (R/'datasets/synthetic_genz/threads').glob('*.json') for c in json.loads(p.read_text(encoding='utf-8'))['comments']}
assert not set(texts)&source
manifest={'status':'LOCKED_BEFORE_FIRST_SCORING','threads':len(threads),'comments':len(texts),'label_source':'synthetic_reference',
    'human_gold':False,'data_origin':'synthetic','generation':'12 Codex-authored distinct scenes; deterministic metadata compiler only; no API/template utterance generation',
    'use':'one-pass post-fix synthetic challenge, never training or independent human gold','training_forbidden':True,
    'rule_lock_sha256':sha(P/'frozen_rule_lock.json'),'thread_sha256':{t['thread_id']:sha(D/(t['thread_id']+'.json')) for t in threads},
    'exact_duplicate_comments':0,'exact_overlap_canonical500':0,'labels':dict(Counter(c['annotation']['label'] for t in threads for c in t['comments'])),
    'limits':'AI-authored by same assistant after rule freeze, not author-blind/human verified; no post-score rule tuning allowed.'}
(D/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:manifest[k] for k in ('threads','comments','labels','exact_duplicate_comments')}))
