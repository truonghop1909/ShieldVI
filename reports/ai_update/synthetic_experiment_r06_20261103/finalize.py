"""Seal completed r06 evidence; never runs training, inference or promotion."""
import hashlib,json,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.experiment import verify_view,verify_prepared

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,value):Path(p).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def text(p,value):Path(p).write_text(value,encoding='utf-8')

cfg=read(R/'configs/t029_synthetic_only_cpu_r06.json');model=Path(cfg['output_dir'])
training=read(model/'training_report.json');comparison=read(P/'evaluation/comparison.json')
protocol=read(P/'predeclared_protocol.json');prepared=read(P/'prepared/manifest.json')
dataset,threads,quality=verify_view(R/'datasets/synthetic_genz',R/cfg['synthetic_export'])
verify_prepared(cfg,P/'prepared',R)
checked={}
def check(p,expected):
    p=Path(p);actual=sha(p)
    if actual!=expected:raise ValueError('Protected/hash-bound artifact changed: '+str(p))
    checked[str(p)]=actual
for p,expected in read(R/'reports/ai_update/final/session_verification.json')['protected_hashes_unchanged'].items():check(p,expected)
for key,p in [('config_sha256',R/'configs/t029_synthetic_only_cpu_r06.json'),('dataset_manifest_sha256',R/'datasets/synthetic_genz/dataset_manifest.json'),('split_manifest_sha256',R/'datasets/synthetic_genz/split_manifest.json'),('prepared_manifest_sha256',P/'prepared/manifest.json'),('training_implementation_sha256',R/'scripts/t029_cpu_head.py')]:check(p,protocol[key])
check(Path(protocol['baseline_path'])/'model.safetensors',protocol['baseline_sha256'])
check(model/'model.safetensors',training['candidate_sha256'])
check(model/'training_report.json',comparison['training_report_sha256'])
check(P/'source_request.txt',read(P/'cpu_authorization.json')['source_attachment_sha256'])
check(P/'evaluation/predictions.json',read(P/'evaluation/teencode_reporting_v2.json')['source_predictions_sha256'])
canonical=R/cfg['synthetic_export'];lock=read(canonical/'development_lock.json')
check(canonical/'dataset_manifest.json',lock['dataset_manifest_sha256']);check(canonical/'development_threads.jsonl',lock['development_sha256'])
legacy=R/'datasets/synthetic_conversations';lm=read(legacy/'manifest.json')
for tid,h in lm['thread_checksums'].items():check(legacy/'threads'/(tid+'.json'),h)
for name,h in lm['csv_checksums'].items():check(legacy/name,h)
context=R/'datasets/fixtures/context_recovery_v1'
for name,h in read(context/'manifest.json')['file_sha256'].items():check(context/name,h)
for p in (R/'models/candidates').glob('*/training_report.json'):
    tr=read(p)
    if tr.get('candidate_sha256'):check(p.parent/'model.safetensors',tr['candidate_sha256'])
history=read(R/'reports/ai_update/independent_readiness_20261103/historical_task_states.json')
for row in history:
    content=(R/row['file']).read_text(encoding='utf-8')
    status=re.search(r'(?:Status|Trạng thái):\*\*\s*(DONE|IN_PROGRESS|TODO|BLOCKED|WAITING_APPROVAL)',content,re.I)
    if not status or status.group(1)!=row['historical_status']:raise ValueError('Historical task status changed: '+row['file'])
logbytes=(P/'final_tests.log').read_bytes();log=logbytes.decode('utf-16' if logbytes[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
assert '591 passed, 1 warning' in log and 'failed' not in log.lower()
postbytes=(P/'post_scope_tests.log').read_bytes();postlog=postbytes.decode('utf-16' if postbytes[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
assert '45 passed, 1 warning' in postlog
postflight=read(P/'post_scope_preflight.json')
assert postflight['status']=='BLOCKED' and postflight['training_performed'] is False
assert any('not authorized' in reason for reason in postflight['blockers'])
assert training['encoder_unchanged'] and training['source_hashes_unchanged'] and not training['activated']
assert not comparison['promotion_allowed'] and not comparison['historical_original_test_scored']
scope=read(R/'tasks/CURRENT_AI_SCOPE.json')
assert scope['T028']['current_status']=='BLOCKED' and scope['T028']['actual_valid_real_threads']==0
assert scope['training_allowed_this_session'] is False
write(P/'integrity.json',{'status':'PASS','protected_hashes':checked,'hashes_verified':len(checked),'canonical_threads_verified':500,
    'legacy_threads_verified':200,'derived_threads_verified':500,'historical_task_states_preserved':len(history),
    'original_threshold':.41,'original_test_scored':False,'default_changed':False,'T028_valid_real_threads':0,'T028_status':'BLOCKED',
    'post_scope_related_tests_passed':45,'consumed_training_preflight':'EXPECTED_BLOCKED_NO_TRAINING'})

text(model/'README.md',f'''# EXPERIMENTAL r06 — synthetic-only classifier head

Actual CPU training: 4,398 AI-labelled synthetic comments; 207 AdamW steps, three epochs, 79.75 seconds. Original V1 encoder frozen; only classifier.dense and classifier.out_proj trained. This is not full encoder fine-tuning. Selected epoch3 using 306 synthetic validation comments, threshold0.41. No ViCTSD training or validation rows were used in this run.

All labels are synthetic references, not human gold. The 30-thread challenge and 30-thread validation were already seen in rule development; no independent or real-world performance claim. Existing default remains unchanged. Model status EXPERIMENTAL_NOT_ACTIVATED. T028 real criteria and formal T029/T030 real acceptance remain BLOCKED.

Weights SHA256: {training['candidate_sha256']}

Exact optimizer/data/config/checkpoint provenance: training_report.json and checkpoint_manifest.json. Comparison and remaining errors: [experiment report](../../../docs/ai-update/final-report/SYNTHETIC_R06_EXPERIMENT.md). The generic trainer README was corrected here because its inherited ViCTSD wording does not apply to the synthetic-only recipe; the training report and checkpoint were not modified.
''')
write(model/'checkpoint_manifest.json',{'status':'EXPERIMENTAL_NOT_ACTIVATED','run_id':cfg['run_id'],
    'weights':{'file':'model.safetensors','sha256':sha(model/'model.safetensors')},'training_report_sha256':sha(model/'training_report.json'),
    'config_sha256':protocol['config_sha256'],'dataset_manifest_sha256':protocol['dataset_manifest_sha256'],
    'split_manifest_sha256':protocol['split_manifest_sha256'],'prepared_manifest_sha256':protocol['prepared_manifest_sha256'],
    'base':{'identity':'original_ViSoBERT_V1','sha256':protocol['baseline_sha256'],'encoder_sha256':training['encoder_sha_after']},
    'method':'frozen_encoder_full_classifier_head_CPU','optimizer':'AdamW','learning_rate':cfg['learning_rate'],
    'weight_decay':cfg['weight_decay'],'distillation_weight':cfg['distillation_weight'],'teacher_temperature':2,
    'positive_sample_weight':prepared['positive_sample_weight'],'class_weight_policy':prepared['class_weight_policy'],
    'train_rows':training['train_rows'],'human_gold_rows':0,'seed':cfg['seed'],'epochs':3,'selected_epoch':3,
    'batch_size':cfg['batch_size'],'optimizer_steps':training['optimizer_steps'],'elapsed_seconds':training['elapsed_seconds'],
    'max_seconds':900,'cpu_threads':4,'external_cost':0,'threshold':.41,'production_activation_allowed':False,
    'independent_real_metrics':False,'T028_real':'BLOCKED'})

lines=['# Thực nghiệm synthetic r06 — EXPERIMENTAL',
    '', 'Đã thực sự train và đánh giá candidate riêng; không thay mô hình mặc định. Kết quả dưới đây chỉ dùng nhãn AI synthetic, không phải human gold hay real-world evaluation.',
    '', '## Dữ liệu và kiểm tra',
    '', 'Tái sử dụng nguyên văn 500 hội thoại/5.115 bình luận từ `datasets/synthetic_conversations/genz_v2`; không sinh mới câu chữ trong lượt này. Nguồn có 200 hội thoại legacy và 300 hội thoại Codex đã viết trước đó. Xuất view mới tại `datasets/synthetic_genz`, giữ nguyên nguồn, nhãn và split gốc. Schema mới làm phẳng annotation nhưng không thay nội dung. Compiler và lịch timestamp là deterministic; không chứng minh hội thoại là dữ liệu thật.',
    '', 'Nhãn CLEAN4.667/TOXIC369/UNCERTAIN79; 102 cờ cần rà soát, chưa có human review. 3–6 người, 10–18 bình luận/thread. 20 nhóm tình huống; 272 thread không có TOXIC, 396 cấu trúc vai trò, cấu trúc phổ biến nhất xuất hiện12lần. Pilot20 rồi batch50, cuối30; checkpoint đủ500. JSON/schema/parent/timestamp/participant/target/repeated evidence PASS theo validator. Exact duplicate0, near-duplicate comment0/thread0 tại ngưỡng char5Jaccard0.85(min35ký tự)/0.60; không khẳng định hết trùng nghĩa hoặc diễn đạt tự nhiên.',
    '', 'View mới: train440/validation30/challenge30 theo scenario family và strata nhãn, seed20261103, không dựa score. Toàn bộ60family development cũ vẫn ngoài training. Train4.398binary (CLEAN4.085/TOXIC313), loại UNCERTAIN/cờ review và kiểm chống trùng heldout/regression. Validation306binary+2UNCERTAIN; challenge311binary+1UNCERTAIN. Không ép UNCERTAIN sang nhị phân. Nhãn đánh giá tách khỏi predictions/API input.',
    '', 'Validation/challenge đã được dùng trong nghiên cứu rule trước đây, không blind. Việc chia view mới không biến chúng thành test độc lập. Audit tập train r05 cho exact/near overlap với cả60heldout=0. Không đọc nhãn/chạy đánh giá tập test ViCTSD gốc. Không dùng ViCTSD để train r06 vì quyền sử dụng bản local chưa được xác minh lại.',
    '', '## Huấn luyện thực tế',
    '', 'CPU4threads, một run, giới hạn900giây, chi phí ngoài0. CUDA không sẵn. AdamW LR1e-5,wd0.01,batch64,maxlen128,seed20261103; distillation V1 weight0.25,T2; positive weight sqrt(4085/313)=3.612633(cap4), áp dụng CE và distillation. Encoder96.975.360tham số đóng băng; classifier592.130tham số được train. 207steps/3epochs/79.75giây, chọn epoch3 bằng validation Macro-F1 ở0.41, reload sai số0. Encoder/baseline/source hashes giữ nguyên.',
    '', 'Khác r05: r05 dùng6.942ViCTSD+4.398synthetic, khởi tạo V1.1, early stopping trên ViCTSD validation, LR5e-6, distillation1.0 và synthetic weight0.1. r06 khởi tạo originalV1, chỉ synthetic, có class balancing và chọn bằng synthetic validation. Đây là so sánh các recipe, không phải ablation cô lập một biến. Checkpoint cũ không ghi đè.',
    '', 'Full/partial encoder fine-tuning chưa chạy. Notebook `notebooks/T029_Synthetic_Experimental_R06.ipynb` có5codecells, syntax PASS, tất cả unexecuted; mặc định chỉ preparation, ZIP bootstrap kiểm traversal/symlink, không upload/download/mount tự động. GPU/config/resource receipt mới phải phù hợp; không dùng lại quyền r06 để chạy full fine-tune.',
    '', '## So sánh raw classifier, threshold0.41',
    '', '| Split | Model | N | Accuracy | Macro-F1 | Toxic P | Toxic R | Toxic F1 | TP | FP | TN | FN |',
    '|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
for split in ('synthetic_validation','synthetic_challenge'):
    for name,results in comparison['metrics'].items():
        m=results[split]['raw'];lines.append('| '+' | '.join([split,name,str(m['n'])]+[f'{m[k]:.6f}' for k in ('accuracy','macro_f1','toxic_precision','toxic_recall','toxic_f1')]+[str(m[k]) for k in ('tp','fp','tn','fn')])+' |')
lines+=['','Mỗi hàng dùng cùng tập bình luận. Encoder/tokenization ba model bằng nhau được kiểm hash; shared-encoder inference dùng ba head thật, đối chiếu full-forward probes sai số tối đa <4e-8, không có score trong1e-5 quanh0.41. R06 được chọn trước challenge; chỉ một lượt challenge sau chọn, không train/tune lại sau khi xem kết quả.',
    '', '## Hybrid advisory tách riêng', '', '| Split | Model | Macro-F1 | P | R | TP | FP | TN | FN |','|---|---|---:|---:|---:|---:|---:|---:|---:|']
for split in ('synthetic_validation','synthetic_challenge'):
    for name,results in comparison['metrics'].items():
        m=results[split]['hybrid'];lines.append('| '+' | '.join([split,name]+[f'{m[k]:.6f}' for k in ('macro_f1','toxic_precision','toxic_recall')]+[str(m[k]) for k in ('tp','fp','tn','fn')])+' |')
lines+=['','Context-v4/lexicon/target-v4/repeated-v4 giữ nguyên. Raw score, context_tags, lexical_signals, reply_to_user_id, directed_at_user_id, policy risk và advisory lưu riêng trong prediction/hybrid outputs. Policy không thực thi visibility; không tự ẩn. Hybrid gains không phải classifier gains và không có nhãn tham khảo trong request phân tích.',
    '', '## Phân nhóm và lỗi còn lại','', 'Toàn bộ Accuracy/Macro-F1/P/R/confusion theo nhóm nằm trong comparison.json; dưới đây giữ số lượng sai raw/hybrid của r06 để thấy giới hạn. Sarcasm chỉ là proxy nhóm indirect_attack do tác giả gán, chưa có nhãn sarcasm riêng. Nhóm chỉ có một lớp dùng fixed two-class Macro-F1 nên không diễn giải như benchmark cân bằng; n=0 là thiếu bằng chứng, không phải điểm0.',
    '', '| Split | Group | N | Raw FP/FN | Hybrid FP/FN |','|---|---|---:|---:|---:|']
overlay=read(P/'evaluation/teencode_reporting_v2.json')
for split in ('synthetic_validation','synthetic_challenge'):
    for group,gm in comparison['metrics']['r06'][split]['groups'].items():
        if group=='teencode':gm=overlay['metrics']['r06'][split]
        raw,hybrid=gm['raw'],gm['hybrid'];n=raw['n']
        lines.append(f"| {split} | {group} | {n} | {str(raw.get('fp'))+'/'+str(raw.get('fn')) if n else 'N/A'} | {str(hybrid.get('fp'))+'/'+str(hybrid.get('fn')) if n else 'N/A'} |")
lines+=['','Teencode mask bản đầu bỏ sót t/m/k/đm/vl. `teencode_reporting_v2.json` sửa riêng bộ lọc báo cáo từ predictions đã lưu, không inference/train mới, không đổi nhãn/score/global metrics. Validation13mẫu phù hợp; challenge0theo bộ lọc này nên chưa có bằng chứng challenge teencode. Giữ nguyên comparison ban đầu để truy vết. Bộ dữ liệu tổng thể có57comment teencode theo heuristic nguồn khác; hai mask không đồng nhất.',
    '', '| Split | Target đúng/reference | Target P/R | Repeated TP/FP/FN | Repeated F1 |','|---|---:|---:|---:|---:|']
for split in ('synthetic_validation','synthetic_challenge'):
    g=comparison['metrics']['r06'][split]['target_repeated'];rep=g['repeated']
    lines.append(f"| {split} | {g['target_correct']}/{g['reference_attacks']} | {g['target_precision']:.4f}/{g['target_recall']:.4f} | {rep['tp']}/{rep['fp']}/{rep['fn']} | {rep['f1']:.4f} |")
lines+=['','Target/repeated giống nhau ở ba model vì rule engine không đổi: validation abstain7/15attack, challenge abstain11/20attack. Repeated challenge bỏ sót cả5event (TP0/FN5); không được tuyên bố đã giải quyết harassment. Ngưỡng/rule target yêu cầu chứng cứ nên nhiều câu công kích vẫn thiếu target; câu có actor-target nhưng không đủ nhiều attack có chứng cứ không tạo repeated event. Head-only training không sửa được dependency này.',
    '', '### Paired wins/losses và ví dụ', '']
predictions=read(P/'evaluation/predictions.json');byname={name:{} for name in comparison['metrics']}
for row in predictions:
    if row['synthetic_reference']!='UNCERTAIN':byname[row['model']][(row['thread_id'],row['comment_id'])]=row
paired={}
for baseline in ('V1','r05'):
    paired[baseline]={}
    for split in ('synthetic_validation','synthetic_challenge'):
        wins=[];losses=[]
        for key,new in byname['r06'].items():
            if new['split']!=split:continue
            old=byname[baseline][key];good=new['raw_label']==new['synthetic_reference'];prior=old['raw_label']==old['synthetic_reference']
            if good and not prior:wins.append(new)
            if prior and not good:losses.append(new)
        paired[baseline][split]={'wins':len(wins),'losses':len(losses),'win_ids':[x['comment_id'] for x in wins],'loss_ids':[x['comment_id'] for x in losses]}
        lines.append(f"- So {baseline}, {split}: sửa đúng {len(wins)}, mới sai {len(losses)} bình luận.")
        for row in losses[:2]:lines.append(f"  - Mới sai: `{row['comment_id']}` reference{row['synthetic_reference']}, score{row['raw_score']:.4f}: “{row['text']}”")
lines+=['','Ví dụ r06 còn sai (không sửa reference):']
remaining=[x for x in byname['r06'].values() if x['raw_label']!=x['synthetic_reference']]
for label in ('CLEAN','TOXIC'):
    for row in [x for x in remaining if x['synthetic_reference']==label][:3]:
        lines.append(f"- `{row['comment_id']}` reference{label}, raw{row['raw_label']}({row['raw_score']:.4f}), advisory{row['advisory']}: “{row['text']}”")
write(P/'evaluation/paired_errors.json',paired)
lines+=['','## Kiểm thử và toàn vẹn','', 'Pretrain60PASS. Full root lần đầu586PASS/1FAIL do notebook thiếu bootstrap/path theo migration convention; đã sửa notebook, kiểm liên quan17PASS; root587PASS. Bổ sung4test mask teencode, full root cuối591PASS/0FAIL trong52.93giây, một Starlette/httpx deprecation warning. Không sửa nhãn kỳ vọng để PASS; không train lại. Frontend/backend runtime không sửa trong lượt này nên không chạy npm build hay giả nhận test Social cũ là test mới.',
    '', f'Hash audit PASS: {len(checked)} file bảo vệ/hash-bound,500canonical+500derived+200legacy thread kiểm tra,27trạng thái task lịch sử giữ nguyên. V1/default/checkpoints r03/r04/r05/testsplit/SQLite giữ nguyên. Xem integrity.json. Khóa quyền r06 sau một run; general training vẫn false. Sau khi khóa,45test liên quan PASS; dry preflight thực tế BLOCKED vì hết quyền và output đã tồn tại, không chạy optimizer. Checkpoint manifest riêng, artifact index kèm SHA. Không deploy/push, không tự chuyển demo sang r06.',
    '', '## Trạng thái và tiếp tục','', '5mốc thực nghiệm hoàn tất: dataset reuse/validation, chuẩn bị train, train thật, comparison/error analysis, tài liệu/checkpoint/progress. T028 independent real vẫn BLOCKED:0/200thread hợp lệ,0human labels, bộ30thread/313comment cũ NOT_FOUND theo audit trước. Collector Wikimedia tiếp tục PAUSED. Không đánh dấu mới T028 DONE hoặc xóa trạng thái DONE lịch sử. Formal T029/T030 real acceptance và kết luận real-world T033 chưa đạt; r06 chỉ EXPERIMENTAL. Không promotion dựa synthetic.',
    '', 'Tiếp theo: human review synthetic nếu cần nâng chất lượng nhãn; regression riêng cho target/repeated còn bỏ sót trước khi thay rule. Real evaluation cần dữ liệu có quyền nguồn, provenance/privacy/leakage kiểm chứng, cùng một người Round1/Round2 và khóa bộ đánh giá. Full GPU fine-tune chỉ sau receipt/resource/config mới được duyệt; notebook hiện chưa chạy. Hướng dẫn tái kiểm và provenance: reports/ai_update/synthetic_experiment_r06_20261103/README.md.', '']
text(R/'docs/ai-update/final-report/SYNTHETIC_R06_EXPERIMENT.md','\n'.join(lines))

text(P/'README.md','''# Completed r06 experiment — reproduction and evidence

Start at repository root with the existing .venv. No dataset/model download or paid API is required for the completed local experiment. Dataset: datasets/synthetic_genz (500 reused JSONs, unchanged synthetic references). Full comparison/error analysis: [report](../../../docs/ai-update/final-report/SYNTHETIC_R06_EXPERIMENT.md). Checkpoint: models/candidates/T029_synthetic_only_head_cpu_20261103_r06; never activated.

## Safe revalidation

```powershell
.\\.venv\\Scripts\\python.exe -X utf8 -c "import sys;sys.path.insert(0,'scripts');from synthetic_data.experiment import verify_view; m,t,q=verify_view('datasets/synthetic_genz');print(m['threads'],m['comments'],q['status'])"
.\\.venv\\Scripts\\python.exe -m pytest -q tests/test_synthetic_experiment.py
```

Use a fresh --basetemp under reports/ai_update/test_tmp if Windows temporary-directory permissions require it. final_tests.log records actual full root591PASS/0FAIL. Training_execution.json records actual207optimizersteps/79.75seconds. evaluation/ contains saved same-input three-model predictions, metrics, hybrid outputs, errors and paired wins/losses. teencode_reporting_v2.json only recomputes the corrected slice mask from saved predictions, never model inference. Integrity audit is integrity.json; output checksums are ARTIFACTS.json.

## Dataset resume

scripts/synthetic_data/experiment.py export_dataset uses the existing canonical export, not a template text generator. It validates complete canonical content first, processes pilot20/batches50/final30, writes checkpoints and resumes only identical existing files. A completed export is revalidated, never silently replaced. Its original source style/content limitations still apply. Do not run prepare_run.py again: it is the initial exact-request/config/data authorization orchestration, refuses an existing run, and the one-run authorization is now consumed.

## Training/evaluation provenance

The actual command was scripts/train_t029_candidate.py --config configs/t029_synthetic_only_cpu_r06.json --prepared reports/ai_update/synthetic_experiment_r06_20261103/prepared --base-model <original-local-V1-directory> --approval reports/ai_update/synthetic_experiment_r06_20261103/cpu_authorization.json --run --report reports/ai_update/synthetic_experiment_r06_20261103/training_execution.json, executed using the repo Python. Protocol/config/data hashes were fixed before training. Existing candidate output and consumed scope block reruns. No production registry changes were made.

The comparison was scripts/evaluate_synthetic_candidate.py --config configs/t029_synthetic_only_cpu_r06.json --prepared reports/ai_update/synthetic_experiment_r06_20261103/prepared --output reports/ai_update/synthetic_experiment_r06_20261103/evaluation. Use the saved results for review; repeating research inference does not produce independent evidence and must never be used to tune against challenge labels.

For a genuinely new authorized experiment choose new run ID, output directory, config, prepared manifest and matching resource receipt. Never overwrite r06 or reuse its one-run receipt. Full encoder GPU fine-tune is only prepared in notebooks/T029_Synthetic_Experimental_R06.ipynb (unexecuted, approval false by default). No implicit API/upload/download/mount occurs. GPU approval must match actual resource/config; changing a notebook boolean alone does not grant it. Optimizer-state resume is not implemented; incomplete training is not a completed model.

T028 real200 remains BLOCKED; no real/human-gold metrics, no release/promotion approval. Original V1, threshold0.41, canonical datasets/test split and SQLite remain unchanged.
''')

scope['authority']='Latest attached request permits one bounded r06 synthetic experiment only; now completed and authorization consumed. Real criteria unchanged.'
scope['synthetic_experiment'].update({'authorized':False,'status':'COMPLETE_TRAINED_EVALUATED_EXPERIMENTAL','training_performed':True,
    'optimizer_steps':207,'elapsed_seconds':79.75,'candidate_sha256':training['candidate_sha256'],'completed_candidate_runs':1,
    'validation_macro_f1':comparison['metrics']['r06']['synthetic_validation']['raw']['macro_f1'],
    'challenge_macro_f1':comparison['metrics']['r06']['synthetic_challenge']['raw']['macro_f1'],'root_tests_passed':591,
    'post_scope_related_tests_passed':45,'new_training_guard':'EXPECTED_BLOCKED'})
scope['current_tasks']['T029']['scope']='Formal training/acceptance tied to real T028; completed experimental r06 tracked separately'
scope['current_tasks']['T029']['blockers'][0]='New formal training not authorized; completed one-run synthetic r06 exception consumed'
scope['remaining_ready_work']='Requested synthetic experiment complete; real T028/formal T029/T030 human-gold acceptance still BLOCKED. No automatic new training/promotion.'
write(R/'tasks/CURRENT_AI_SCOPE.json',scope)
progress=read(P/'progress.json');progress.update({'status':'COMPLETE_EXPERIMENTAL_NOT_ACTIVATED','evaluation_performed':True,'root_tests_passed':591,
    'milestones_done':5,'post_scope_related_tests_passed':45,'consumed_training_preflight':'EXPECTED_BLOCKED',
    'formal_T028_real':'BLOCKED','formal_T029_T030_real_acceptance':'BLOCKED','human_gold':False,
    'next':'Review saved synthetic results; provide permitted real material/human rounds for independent criteria, or explicitly authorize a new bounded experiment',
    'blockers':['Independent real0/200 and human labels0','Formal T029/T030 real acceptance not met','Challenge repeated events TP0/FN5; target recall0.45','Full GPU fine-tuning not executed']})
write(P/'progress.json',progress)
note='''
## r06 completed — EXPERIMENTAL, not independent acceptance

5experimental milestonesDONE: reuse/validate500threads(5115comments;CLEAN4667/TOXIC369/UNCERTAIN79), prepare4398synthetic-only rows, actual CPUhead training207steps/3epochs/79.75s, actual V1/r05/r06 comparison, checkpoint/report/progress. No new utterances generated. Encoder frozen; threshold0.41/V1/default/oldcheckpoints/test/SQLite preserved; one-run scope consumed.

Raw MacroF1 validation V1.688581/r05.670259/r06.823834; challenge V1.779884/r05.787645/r06.828798. Validation/challenge already viewed in rule research, synthetic_reference only, not human gold/real-world evidence. R06 challenge FP9/FN5; target9/20correct(P1,R.45), repeatedTP0/FP0/FN5. No claim these errors are solved; no production activation.

Tests: actual full root `python -m pytest -q --basetemp reports/ai_update/test_tmp/r06_final` →591PASS/0FAIL/one deprecation warning. Earlier notebook migration failure fixed and rerun; final_tests.log retains evidence. No changed expected labels. No frontend edits/build. Hash audit integrity.json preserves27historical task statuses and source/model/test hashes.

Files changed: scripts/prepare_t029_training.py, scripts/train_t029_candidate.py, new scripts/synthetic_data/experiment.py, scripts/evaluate_synthetic_candidate.py, tests/test_synthetic_experiment.py, configs/t029_synthetic_only_cpu_r06.json, notebooks/T029_Synthetic_Experimental_R06.ipynb; new datasets/synthetic_genz/ and models/candidates/T029_synthetic_only_head_cpu_20261103_r06/; reports/ai_update/synthetic_experiment_r06_20261103/; task/scope progress and docs/ai-update/final-report/SYNTHETIC_R06_EXPERIMENT.md. Existing runtime AI/backend/frontend unchanged in this experiment.

T028realBLOCKED0/200,humanlabels0; old30/313NOT_FOUND (previous audit). Formal T029/T030 real criteria still BLOCKED; historical DONE preserved. FullGPU notebook prepared/unexecuted. WikimediaPAUSED. Next: review saved results / target-repeated regression or permitted real data plus same-human Round1/Round2; no automatic new train or promotion. Resume context and safe validation commands: reports/ai_update/synthetic_experiment_r06_20261103/README.md; machine state progress.json; current authority tasks/CURRENT_AI_SCOPE.json.
'''
for name in ('tasks/AUTO_PROGRESS.md','tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md'):
    p=R/name;content=p.read_text(encoding='utf-8').replace('## CURRENT explicit synthetic experiment r06 — IN_PROGRESS','## Synthetic experiment r06 — historical execution timeline (completed below)')
    if '## r06 completed — EXPERIMENTAL, not independent acceptance' not in content:text(p,content+'\n'+note)
for prefix in ('T028-','T029-','T030-'):
    p=next((R/'tasks/moderation-ai').glob(prefix+'*.md'));content=p.read_text(encoding='utf-8')
    if '## r06 synthetic-only experiment evidence' not in content:text(p,content+'''

## r06 synthetic-only experiment evidence

Latest explicit request completed a separate EXPERIMENTAL synthetic-only CPU head run:4398rows/207steps/79.75s;500reused threads, no independent human gold. Raw validation MacroF1 .823834/challenge .828798;591root testsPASS. OriginalV1/0.41/source/test/default untouched, no promotion. T028real0/200 and formal T029/T030 real acceptance remain BLOCKED; historical status above is preserved, not new real acceptance. See [report](../../docs/ai-update/final-report/SYNTHETIC_R06_EXPERIMENT.md), tasks/CURRENT_AI_SCOPE.json and AUTO_PROGRESS.md. One-run authority consumed; no further train authorized.
''')
# Hash final outputs after all mutations; exclude this index's self-reference.
paths=list(P.rglob('*'))+list(model.iterdir())+[R/x for x in ('AGENTS.md','tasks/CURRENT_AI_SCOPE.json','tasks/AUTO_PROGRESS.md','tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md','configs/t029_synthetic_only_cpu_r06.json','scripts/prepare_t029_training.py','scripts/train_t029_candidate.py','scripts/synthetic_data/experiment.py','scripts/evaluate_synthetic_candidate.py','tests/test_synthetic_experiment.py','notebooks/T029_Synthetic_Experimental_R06.ipynb','docs/ai-update/final-report/SYNTHETIC_R06_EXPERIMENT.md')]
paths+=list((R/'datasets/synthetic_genz').rglob('*'))
paths+=[next((R/'tasks/moderation-ai').glob(prefix+'*.md')) for prefix in ('T028-','T029-','T030-')]
index={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in paths if p.is_file() and p!=P/'ARTIFACTS.json' and '__pycache__' not in str(p)}
write(P/'ARTIFACTS.json',{'status':'COMPLETE_EXPERIMENTAL','algorithm':'SHA256','file_count':len(index),'files':index,'self_excluded':True})
print(json.dumps({'status':progress['status'],'protected_hashes_verified':len(checked),'root_tests_passed':591,'post_scope_tests_passed':45,'artifacts':len(index),'T028_real':'BLOCKED','production_changed':False}))
