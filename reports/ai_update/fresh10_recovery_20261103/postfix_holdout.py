"""New small AI-authored holdout AFTER experiment freeze; one scoring pass only."""
import json,sys,os
from pathlib import Path
from datetime import datetime,timedelta,timezone
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent;D=R/'datasets/fixtures/fresh10_postfix_holdout_v1'
sys.path.insert(0,str(R/'scripts'));sys.path.insert(0,str(R/'services/moderation-ai'))
from synthetic_data.pipeline import atomic_json,file_sha,normalized
from evaluate_fresh10_recovery import replay,evidence_metrics
from import_and_audit import progress
scenes=[('co_op_voice',[
('H01',None,'Mình đã bật push to talk cho đội, mọi người nghe rõ chưa?','CLEAN',None),
('H02',1,'Bạn sống kiểu vô ý thức thật, cứ để mic mở suốt trận đấu.','TOXIC','H01'),
('H01',2,'Mình đã tắt nhạc rồi, bạn chỉ giúp tiếng nào còn lọt vào mic nhé.','CLEAN',None),
('H03',3,'Âm thanh bàn phím nhỏ thôi, giảm độ nhạy một chút là được.','CLEAN',None),
('H02',3,'Bạn còn cãi cùn khi cả đội đã nói rõ nguyên nhân rồi.','TOXIC','H01'),
('H03',5,'Mình cần nghe call chứ không cần thêm lời công kích trong voice.','CLEAN',None),
('H01',4,'Nói căng vậy nghe hơi rén nha bro :))','UNCERTAIN',None),
('H03',4,'Mình gửi preset lọc ồn để cả đội thử cùng nhau.','CLEAN',None)]),
('translation_zine',[
('H01',None,'Bản in zine này dùng hai kiểu chữ, nhóm chọn kiểu nào cho phần chú giải?','CLEAN',None),
('H02',1,'Bản kia nhìn giống sách giáo khoa hơn, còn bản này mềm mắt.','CLEAN',None),
('H03',2,'Mấy đoạn trích cần giữ nguyên dấu ngoặc để người đọc biết đâu là lời tác giả.','CLEAN',None),
('H02',3,'Ví dụ nhân vật nói “đúng là chuyên gia tự phong” thì mình vẫn giữ nguyên văn.','CLEAN',None),
('H01',4,'Đúng rồi, đang bàn lời thoại nhân vật, không đánh giá ai trong nhóm.','CLEAN',None),
('H03',1,'Mình đang cười cái máy in của chính mình thôi, cứ đảo mặt giấy là lệch màu.','CLEAN',None),
('H02',6,'Máy có thanh canh giấy ở cạnh trái, thử khóa lại trước khi in chồng.','CLEAN',None),
('H01',7,'Mình thử tờ nháp xong sẽ chụp hai bản đặt cạnh nhau.','CLEAN',None)]),
('open_rehearsal',[
('H01',None,'Mình hát thử bản phối acoustic cho đêm gây quỹ nhé.','CLEAN',None),
('H02',1,'Đúng là thiên tài tự phong mới nghĩ đoạn vừa rồi đủ mang đi diễn.','TOXIC','H01'),
('H03',2,'Bạn góp ý nhịp lấy hơi được mà, đừng hạ thấp người hát.','CLEAN',None),
('H01',3,'Đoạn đầu mình lấy hơi hụt, mình muốn tập lại trước khi chốt bài.','CLEAN',None),
('H02',4,'Bạn hát dở còn thích làm trung tâm trong buổi tập của nhóm.','TOXIC','H01'),
('H03',5,'Mình xin ngừng cách nói đó, để bạn ấy hoàn thành phần thử giọng.','CLEAN',None),
('H02',6,'Tôi xin lỗi vì đã gọi bạn là thiên tài tự phong lúc nãy.','CLEAN',None),
('H01',7,'Mình cần nghỉ một lát rồi sẽ quay lại tập đoạn chuyển tông.','CLEAN',None)]),
('terrarium_hardware',[
('H01',None,'Máy phun sương cho hồ cây của mình cứ tự mất lịch hẹn giờ.','CLEAN',None),
('H02',1,'Máy ngu này lại quên mạng WiFi, t phải nhập mật khẩu lần thứ ba rồi.','CLEAN',None),
('H03',2,'Bạn thử tách mạng khách riêng, bộ hẹn giờ cũ không nhận băng tần mới.','CLEAN',None),
('H02',3,'Mình đang cười cái bộ điều khiển của chính mình thôi, không nhắm ai nhé.','CLEAN',None),
('H01',3,'Mình có hạt ngò và ngô để ngoài khay khô, ai cần thì đổi với mình.','CLEAN',None),
('H03',5,'Mình đổi bạn vài hạt ngò, rồi mang thêm ống nối cho máy phun sương.','CLEAN',None),
('H02',4,'Mấy ống này nên đánh dấu hai đầu để lần sau lắp lại nhanh hơn.','CLEAN',None),
('H01',7,'Đã ghi số trên ống, tối mình thử lại lịch phun một lần nữa.','CLEAN',None)]),
('separate_actors',[
('H01',None,'Mình đăng bảng so sánh hai phương án đèn sân khấu cho nhóm.','CLEAN',None),
('H02',1,'Bạn đúng là đồ ngu khi dùng tiêu chí ấy để so thiết bị.','TOXIC','H01'),
('H03',1,'Bạn vô dụng thật, có mấy mẫu đèn mà cũng không chọn được.','TOXIC','H01'),
('H01',2,'Mình đang hỏi về công suất và góc chiếu, không hỏi nhận xét về bản thân.','CLEAN',None),
('H02',4,'Bộ đèn trong cột đầu có quạt tản nhiệt không?','CLEAN',None),
('H03',4,'Cho mình biết kích thước phòng diễn để tính lại cự ly.','CLEAN',None),
('H01',5,'Có quạt, mình đã thêm độ ồn trong bảng ghi chú.','CLEAN',None),
('H03',7,'Mình nhìn thấy dòng ghi chú rồi, số liệu đó đủ để tính tiếp.','CLEAN',None)]),
('mixed_boundary_attack',[
('H01',None,'Mình không đồng ý phí giữ chỗ mới của khu workshop.','CLEAN',None),
('H02',1,'Tôi không chấp nhận công kích, nhưng bạn cứ cãi cùn trong cuộc họp này.','TOXIC','H01'),
('H01',2,'Mình đang yêu cầu giải thích khoản phí, không phải tranh thắng thua.','CLEAN',None),
('H03',3,'Ban tổ chức cần gửi bảng chi tiết trước khi thu tiền.','CLEAN',None),
('H02',3,'Bạn thích ra oai quá, mới hỏi phí mà làm như điều hành cả khu.','TOXIC','H01'),
('H03',5,'Đừng gọi bạn ấy là người thích ra oai, hãy trả lời về khoản thu.','CLEAN',None),
('H02',6,'Mình xin lỗi vì đã nói bạn thích ra oai quá trong cuộc họp.','CLEAN',None),
('H01',7,'Mình sẽ đọc bảng phí khi nhận được rồi phản hồi bằng văn bản.','CLEAN',None)])]

if __name__=='__main__':
    lock=json.loads((P/'experiment_lock.json').read_text());module=R/'services/moderation-ai/app/experiments/fresh10_v6.py'
    assert file_sha(module)==lock['experimental_module_sha256']
    if (P/'postfix_holdout_metrics.json').exists():raise FileExistsError('Do not rescore or tune the already-seen challenge')
    threads=[];base=datetime(2026,11,3,tzinfo=timezone.utc)
    for i,(topic,rows) in enumerate(scenes,1):
        tid=f'FRESH10_POSTFIX_{i:02}';comments=[]
        for j,(user,parent,text,label,target) in enumerate(rows,1):
            comments.append({'comment_id':f'c{j:02}','user_id':user,'parent_id':f'c{parent:02}' if parent else None,
                'timestamp':(base+timedelta(hours=i,minutes=j*2)).isoformat(),'text':text,
                'annotation':{'label':label,'directed_at_user_id':target,'is_directed_attack':label=='TOXIC','label_source':'synthetic_reference','human_gold':False}})
        threads.append({'thread_id':tid,'topic':topic,'data_origin':'synthetic','comments':comments})
    mpath=D/'manifest.json'
    if not mpath.exists():
        existing={normalized(c['text']) for folder in ('datasets/fixtures/fresh10_regression_v1/inputs','datasets/synthetic_genz/threads') for p in (R/folder).glob('*.json') for c in json.loads(p.read_text(encoding='utf-8'))['comments']}
        texts=[normalized(c['text']) for t in threads for c in t['comments']];assert len(set(texts))==48 and not set(texts)&existing
        for t in threads:atomic_json(D/'threads'/(t['thread_id']+'.json'),t)
        atomic_json(mpath,{'threads':6,'comments':48,'origin':'synthetic','label_source':'synthetic_reference','human_gold':False,'training_forbidden':True,
            'experiment_lock_sha256':file_sha(P/'experiment_lock.json'),'authoring':'Six individual Codex-authored scenes after rule freeze; deterministic metadata only, no external API',
            'author_blind':False,'new_before_first_scoring':True,'labels':dict(Counter(c['annotation']['label'] for t in threads for c in t['comments'])),
            'thread_sha256':{t['thread_id']:file_sha(D/'threads'/(t['thread_id']+'.json')) for t in threads}})
    manifest=json.loads(mpath.read_text(encoding='utf-8'))
    for tid,h in manifest['thread_sha256'].items():assert file_sha(D/'threads'/(tid+'.json'))==h
    scorefile=P/'postfix_scores.json'
    cfg=json.loads((R/'configs/t029_synthetic_only_cpu_r06.json').read_text());model=Path(cfg['output_dir']);weights=file_sha(model/'model.safetensors')
    if scorefile.exists():
        captured=json.loads(scorefile.read_text());assert captured['manifest_sha256']==file_sha(mpath) and captured['model_sha256']==weights
    else:
        os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',STORE_SUMMARIES='0')
        import torch
        torch.set_num_threads(4)
        from app.predictor import ViSoBERTPredictor
        predictor=ViSoBERTPredictor(str(model));assert predictor.threshold==.41
        values=predictor.predict_scores([c['text'] for t in threads for c in t['comments']])
        captured={'model_sha256':weights,'manifest_sha256':file_sha(mpath),'actual_r06_inference':True,'training_performed':False,'scores':values}
        atomic_json(scorefile,captured)
    items=[];truth={};events=[];offset=0
    for t in threads:
        payload={'thread_id':t['thread_id'],'comments':[{k:c[k] for k in ('comment_id','parent_id','user_id','timestamp','text')} for c in t['comments']]}
        items.append({'payload':payload,'scores':captured['scores'][offset:offset+len(t['comments'])]});offset+=len(t['comments']);pairs=defaultdict(list)
        for c in t['comments']:
            a=c['annotation'];truth[(t['thread_id'],c['comment_id'])]={'label':a['label'],'actor':c['user_id'],'target':a['directed_at_user_id'],'time':c['timestamp']}
            if a['label']=='TOXIC' and a['directed_at_user_id']:pairs[(c['user_id'],a['directed_at_user_id'])].append(c['comment_id'])
        for (actor,target),ids in pairs.items():
            if len(ids)>=2:events.append({'thread_id':t['thread_id'],'actor_user_id':actor,'target_user_id':target,'expected_repeated':'true','evidence_comment_ids':';'.join(ids)})
    result,before,after,rows=replay(items,truth);result['reference_evidence']={'before':evidence_metrics(before,events),'after':evidence_metrics(after,events)}
    result.update(scope='New synthetic post-fix challenge, first scored after code freeze; same author, not human gold/independent real',human_gold=False,training_performed=False,
        actual_new_r06_inference=True,no_post_score_rule_tuning=True,model_sha256=weights)
    assert file_sha(module)==lock['experimental_module_sha256'] and file_sha(model/'model.safetensors')==weights
    atomic_json(P/'postfix_holdout_metrics.json',result);atomic_json(P/'postfix_holdout_after.json',after);atomic_json(P/'postfix_holdout_rows.json',rows)
    progress('POSTFIX_HOLDOUT_EVALUATED','Six new AI-authored threads/48comments afterexperimentfreeze; one actualr06forwardcache, no post-score code changes. Metrics, misses, false alerts and evidence retained verbatim in postfix_holdout_metrics.json. Not human gold/independent real; default and readiness unchanged.')
    print(json.dumps({'classification':result['classification'],'grounding':result['grounding'],'evidence':result['reference_evidence'],'new_label_errors':result['new_label_errors']}))
