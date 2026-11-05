"""Versioned exclusion overlay + pending owner adjudication; never edit labels."""
import csv,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent;D=R/'datasets/fixtures/nov10_regression_v1'
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
from check_development_exclusions import check

if __name__=='__main__':
    base=R/'datasets/real_conversations/manifests/development_exclusions.json';base_hash=file_sha(base)
    fresh=R/'reports/ai_update/fresh10_recovery_20261103/T028_EXCLUSION_EXTENSION.json'
    overlay=R/'datasets/real_conversations/manifests/development_exclusions.research_20261104.json'
    assert not overlay.exists()
    index=json.loads(base.read_text());extension=json.loads(fresh.read_text());records={x['path']:x for x in index['source_records']}
    for record in extension['source_records']:records[record['path']]=record
    thread_ids=set(index['thread_ids'])|set(extension['thread_ids'])
    for folder in (D/'inputs',R/'datasets/fixtures/nov10_audit_challenge_v1/threads'):
        for path in sorted(folder.glob('*.json')):
            t=json.loads(path.read_text());thread_ids.add(t['thread_id']);relative=str(path.relative_to(R)).replace('\\','/')
            records[relative]={'path':relative,'format':'thread_json','sha256':file_sha(path),'purpose':'Exclude exposed synthetic audit/development data from independent evaluation'}
    index.update(thread_ids=sorted(thread_ids),source_records=list(records.values()),
        version='research-exclusions-20261104',parent_manifest_sha256=base_hash,
        newly_exposed_sources=['Fresh10/regression/postfix','NOV10/regression','NOV10/audit_challenge'],
        frozen_default_modified=False,activation='Explicit overlay preflight; sealed default loader is unchanged')
    atomic_json(overlay,index)
    checks=[]
    for path in sorted((D/'inputs').glob('*.json')):
        result=check(overlay,json.loads(path.read_text()));assert result['status']=='EXCLUDED_DEVELOPMENT';checks.append(result)
    assert file_sha(base)==base_hash
    atomic_json(P/'exclusion_verification.json',{'status':'PASS','manifest':str(overlay.relative_to(R)).replace('\\','/'),
        'manifest_sha256':file_sha(overlay),'default_manifest_sha256':base_hash,'default_manifest_modified':False,
        'nov10_checks':checks,'registered_new_threads':len(thread_ids-set(json.loads(base.read_text())['thread_ids'])),
        'default_runtime_loader_changed':False,'required_for_future_evaluation':'Run explicit versioned-overlay preflight; no current independent cohort is available.'})
    refs=list(csv.DictReader((D/'expected_reference_labels.csv').open(encoding='utf-8-sig',newline='')))
    questions={
        '11':'Phàn nàn chất lượng dịch vụ có bằng chứng hay suy diễn hạ thấp người giao hàng? Xem cả lời giải thích về mưa và việc giao trễ.',
        '12':'Nhận xét trình độ/band mục tiêu hoặc học thuộc script là góp ý cụ thể hay chế giễu cá nhân trong ngữ cảnh này?',
        '14':'Khiếu nại mô tả hàng và độ trung thực có căn cứ trong thread không? Ranh giới với công kích người bán nằm ở đâu?',
        '15':'Cảnh báo thiếu kinh nghiệm chăm mèo hay quy chụp động cơ/năng lực cá nhân? Có công kích mới sau xin lỗi không?',
        '16':'Nhận xét chiều sâu review/vị giác là phê bình nội dung hay hạ thấp người review? So sánh c04/c09/c14.',
        '17':'Lời phàn nàn ứng xử còn mơ hồ; giữ UNCERTAIN hay đủ bằng chứng cho CLEAN/TOXIC?',
        '18':'Ẩn dụ bảng thông số và nhận xét trưng benchmark là chê lập luận hay công kích nhân cách/người nói?',
        '19':'Phê bình ý tưởng giống Pinterest có bằng chứng hay chế giễu thiếu sáng tạo? Lời yêu cầu ngừng bàn có hạ nhục không?',
        '20':'Góp ý trách nhiệm điều phối có bằng chứng hay công kích/quy chụp nhận công? Giữ riêng từng actor.',
    }
    fields=['thread_id','comment_id','text','original_label','original_target','label_source','human_gold','review_status',
            'adjudication_question','adjudicated_label','adjudicated_target','decision_reason','reviewer']
    with (P/'adjudication_candidates.csv').open('w',encoding='utf-8-sig',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields);writer.writeheader();count=0
        for row in refs:
            if row['expected_label']=='CLEAN' and not ('_16_' in row['thread_id'] and row['comment_id']=='c04'):continue
            number=row['thread_id'].split('_')[2]
            writer.writerow({'thread_id':row['thread_id'],'comment_id':row['comment_id'],'text':row['text'],
                'original_label':row['expected_label'],'original_target':row['directed_at_user_id'],'label_source':'synthetic_reference',
                'human_gold':False,'review_status':'PENDING_OWNER_ADJUDICATION','adjudication_question':questions[number]})
            count+=1
    print(json.dumps({'exclusion':'PASS','registered_new_threads':len(thread_ids-set(json.loads(base.read_text())['thread_ids'])),
                      'nov10_excluded':len(checks),'review_candidates':count,'reference_labels_changed':False}))
