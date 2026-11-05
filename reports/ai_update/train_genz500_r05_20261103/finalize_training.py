"""Close requested training only after optimizer, validation and integrity evidence."""
import json,re,sys
from pathlib import Path
from urllib.parse import unquote
R=Path(__file__).resolve().parents[3];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from refine_model import file_hash
from synthetic_data.pipeline import atomic_json
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def unchanged(mapping):return all(Path(path).is_file() and file_hash(path)==sha for path,sha in mapping.items())
cfg=read(R/'configs/t029_genz500_cpu_head_r05.json');model=Path(cfg['output_dir'])
t=read(model/'training_report.json');v=read(P/'validation_review.json');decl=read(P/'predeclared_experiment.json')
assert t['status']=='COMPLETE_HEAD_TRAINED_NOT_ACTIVATED' and t['training_performed'] and t['optimizer_steps']>0
assert all(t[key] for key in ('encoder_unchanged','baseline_unchanged','source_hashes_unchanged'))
assert t['elapsed_seconds']<=900 and t['reload_probe_max_error']<=1e-5 and not t['full_encoder_finetune']
assert not t['test_scored_during_training'] and not t['activated'] and not v['promotion_allowed'] and not v['test_scored']
assert v['training_report_sha256']==file_hash(model/'training_report.json')
assert v['candidate_sha256']==file_hash(model/'model.safetensors')==t['candidate_sha256']
assert t['base_sha256_before']==decl['base_sha256']==file_hash(R/'models/visobert_head_refined/model.safetensors')
assert t['encoder_sha_after']==read(R/'models/candidates/T029_genz500_head_cpu_20261103_r04/training_report.json')['encoder_sha_before']
for key,path in {'config_sha256':R/'configs/t029_genz500_cpu_head_r05.json','prepared_manifest_sha256':P/'prepared/manifest.json',
  'original_protocol_sha256':R/'reports/ai_update/all_tasks_cpu_20261103/evaluation_protocol.json',
  'validation_references_sha256':P/'validation_references.json','training_code_sha256':R/'scripts/t029_cpu_head.py',
  'validation_code_sha256':R/'scripts/review_t029_validation.py'}.items():assert decl[key]==file_hash(path)
protected=read(R/'reports/ai_update/final/session_verification.json')['protected_hashes_unchanged'];assert unchanged(protected)
prepared=read(P/'prepared/manifest.json')
assert unchanged({s['path']:s['sha256'] for s in prepared['sources'].values()})
assert unchanged({P/'prepared'/name:sha for name,sha in prepared['output_sha256'].items()})
genz=R/'datasets/synthetic_conversations/genz_v2';manifest=read(genz/'dataset_manifest.json');lock=read(genz/'development_lock.json')
assert unchanged({genz/'threads'/(name+'.json'):sha for name,sha in manifest['thread_sha256'].items()})
assert unchanged({genz/name:sha for name,sha in manifest['output_sha256'].items()})
assert file_hash(genz/'dataset_manifest.json')==lock['dataset_manifest_sha256'] and file_hash(genz/'development_threads.jsonl')==lock['development_sha256']
legacy=R/'datasets/synthetic_conversations';lm=read(legacy/'manifest.json')
assert unchanged({legacy/'threads'/(name+'.json'):sha for name,sha in lm['thread_checksums'].items()})
assert unchanged({legacy/name:sha for name,sha in lm['csv_checksums'].items()})
recovery=R/'datasets/fixtures/context_recovery_v1';rm=read(recovery/'manifest.json')
assert unchanged({recovery/name:sha for name,sha in rm['file_sha256'].items()})
assert file_hash(recovery/'game_rank_30_reference.json')==rm['user_reference_sha256']
atomic_json(P/'integrity_audit.json',{'status':'PASS','protected_artifacts':len(protected),
  'original_V1_and_approved_V1_1_unchanged':True,'encoder_unchanged':True,'threshold':.41,
  'synthetic500_and_legacy200_unchanged':True,'development_lock_unchanged':True,
  'context_fixtures_and_user_reference_unchanged':True,'original_validation_test_SQLite_unchanged':True,
  'candidate_reload_error':t['reload_probe_max_error'],'production_changed':False})
b=(P/'preflight_tests.log').read_bytes();log=b.decode('utf-16' if b[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
assert '42 passed' in log and ' failed' not in log and ' errors' not in log
refs=v['reference_validation'];m=t['candidate_validation']
report=R/'docs/ai-update/final-report/GENZ500_TRAIN_R05.md'
lines=['# Dataset GenZ500 — requested training r05','',
 'Người dùng yêu cầu: “hãy nạp dataset mới để train mô hình đi”. Đã thực sự nạp dữ liệu và train một candidate riêng. Máy chỉ có CPU; đây là **train classifier head**, không phải fine-tune toàn encoder. Base là V1.1 đang được duyệt, khác với hai lần r03/r04 khởi tạo từ V1 gốc.',
 '', '## Dữ liệu và cấu hình','',
 '- Nguồn: datasets/synthetic_conversations/genz_v2 —500hội thoại/5115bình luận, nhãn AI tham khảo, không phải human gold. Giữ nguyên split440train/60development; không đưa development/reference vào train.',
 f"- Thực tế nạp {prepared['total_train_rows']}dòng = {prepared['gold_train_rows']}ViCTSD + {prepared['synthetic_train_rows']}synthetic đủ điều kiện nhị phân. Loại UNCERTAIN/review theo pipeline hiện có, không sửa nhãn để train. Validation2000dòng gốc giữ nguyên. Chỉ dùng text test để loại rò rỉ, không score hoặc chọn model trên test.",
 '- Max4CPUthreads/900seconds/cost0; LR5e-6,batch64,max3epochs,patience1,seed20261103,syntheticweight0.1,distillation1.0,maxlength128. Encoder giữ cố định; không tải dữ liệu/model, không gọi dịch vụ phí.',
 '', '## Kết quả train thực tế','',
 f"- {t['optimizer_steps']}optimizersteps/{len(t['epochs'])}epochs/{t['elapsed_seconds']:.2f}seconds. Chọn epoch{t['selected']['epoch']} chỉ bằng historical validation. Thay {len(t['changed_parameter_names'])}tensor classifier; encoder/source/base hash không đổi.",
 f"- Đã lưu và nạp lại checkpoint; sai số probe{t['reload_probe_max_error']}. Threshold0.41. Candidate chưa được kích hoạt hoặc đưa vào UI.",
 '', '| Model | MacroF1 validation | Toxic precision | Toxic recall | TP/FP/TN/FN |',
 '|---|---:|---:|---:|---|']
for name,value in [*refs.items(),('r05_candidate',m)]:
 lines.append(f"| {name} | {value['macro_f1']:.6f} | {value['toxic_precision']:.6f} | {value['toxic_recall']:.6f} | {value['tp']}/{value['fp']}/{value['tn']}/{value['fn']} |")
lines+=['',f"**Quyết định: {v['decision']}**. Giữ nguyên tiêu chí: MacroF1 tăng≥0.005, precision/recall không giảm so với cả V1 và V1.1. Một validation screen không tự cho phép promotion; regression/API/shadow của r05 chưa được chạy và không được suy ra từ r03. Không thay mô hình mặc định.",
 '', '## Kiểm chứng và giới hạn','',
 '-42regression liên quan PASS/1knownStarlettewarning trước train. Post-train: optimizer/source hash/reload/validation/integrity checks PASS.31protected artifacts +500GenZ/200legacy/contextfixtures/userreference/validation/test/SQLite không đổi.',
 '- Đây là exploratory reuse của historical validation; tập test đã từng xem ở các thí nghiệm trước, không được gọi là benchmark blind mới. Không có metric test hoặc kết luận cải thiện ngoài đời cho r05.',
 '- Các task DONE trước đây giữ nguyên; ghi thêm lần train được yêu cầu vào T029/TASK_ORDER_AI/TASK_ORDER/AUTO_PROGRESS. Việc hoàn tất train không đồng nghĩa candidate đạt chất lượng.',
 '', '## File để xem','',
 '- [Checkpoint](../../../models/candidates/T029_genz500_head_cpu_20261103_r05/) · [Training report](../../../models/candidates/T029_genz500_head_cpu_20261103_r05/training_report.json)',
 '- [Config](../../../configs/t029_genz500_cpu_head_r05.json) · [Dữ liệu đã nạp](../../../reports/ai_update/train_genz500_r05_20261103/prepared/manifest.json)',
 '- [Validation review](../../../reports/ai_update/train_genz500_r05_20261103/validation_review.json) · [Integrity audit](../../../reports/ai_update/train_genz500_r05_20261103/integrity_audit.json)',
 '- [Tiến độ](../../../tasks/AUTO_PROGRESS.md). Demo vẫn dùng V1.1; muốn thay model cần hoàn tất đánh giá còn thiếu và quyết định riêng.']
report.write_text('\n'.join(lines)+'\n',encoding='utf-8')
note=f'''\n\n## CURRENT requested training r05 — COMPLETE\n\nExplicit latest train request executed: new GenZ500 dataset,11340rows=6942ViCTSD+4398AI references; warmstart approvedV1.1 classifier, frozenV1-compatibleencoder. Actual {t['optimizer_steps']}steps/{len(t['epochs'])}epochs/{t['elapsed_seconds']:.2f}s; selectedepoch{t['selected']['epoch']}; config5e-6/synweight.1/distill1/max4CPUthreads900s/cost0. Saved models/candidates/T029_genz500_head_cpu_20261103_r05; reloadedprobeerror{t['reload_probe_max_error']}. No fullencoder/GPU training.\n\nValidationMacroF1 original{refs['original_V1']['macro_f1']:.6f}/default{refs['existing_default_V1_1']['macro_f1']:.6f}/r05{m['macro_f1']:.6f}; candidateP{m['toxic_precision']:.6f}/R{m['toxic_recall']:.6f}. Decision{v['decision']}; gates unchanged, no test/challenge scoring and no freshblind claim. Training completion doesnot imply promotion; defaultV1.1 remains active. Prior taskDONE and negative r03/r04 evidence preserved.\n\n42relatedpytestPASS/1warning; actualposttrainreload/source/data/integritychecksPASS;31protected artifacts +200legacy/500GenZ/contextreference/validation/test/SQLite unchanged. No externalAPI/download/paidGPU/reset/push/deploy. Follow-upstatusCOMPLETE. Current report docs/ai-update/final-report/GENZ500_TRAIN_R05.md; resume evidence reports/ai_update/train_genz500_r05_20261103/progress.json. Next: keep default, review measured validation and remaining release evidence before any model adoption.\n'''
for name in ['tasks/AUTO_PROGRESS.md','tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md','tasks/moderation-ai/T029-optional-train-candidate-visobert-on-colab.md']:
 with (R/name).open('a',encoding='utf-8') as f:f.write(note)
atomic_json(P/'progress.json',{'status':'COMPLETE_TRAINED_NOT_ACTIVATED','run_id':cfg['run_id'],'training_performed':True,
 'optimizer_steps':t['optimizer_steps'],'training_seconds':t['elapsed_seconds'],'selected_epoch':t['selected']['epoch'],
 'validation_macro_f1':m['macro_f1'],'decision':v['decision'],'related_tests_passed':42,'integrity':'PASS','test_scored':False,
 'default_changed':False,'report':report.relative_to(R).as_posix(),'next':'Keep default; review validation/remaining gates before any adoption'})
paths=[report,R/'configs/t029_genz500_cpu_head_r05.json',model/'training_report.json',model/'threshold_config.json']
paths += [path for path in P.rglob('*') if path.is_file() and path.name!='ARTIFACTS.json']
paths += [R/name for name in ('tasks/AUTO_PROGRESS.md','tasks/TASK_ORDER.md','tasks/moderation-ai/TASK_ORDER_AI.md','tasks/moderation-ai/T029-optional-train-candidate-visobert-on-colab.md')]
broken=[]
for path in paths:
 if path.suffix!='.md':continue
 for raw in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
  raw=raw.strip('<>').split('#',1)[0]
  if raw and not raw.startswith(('http:','https:','mailto:')) and not (path.parent/unquote(raw)).resolve().exists():broken.append((str(path),raw))
assert not broken,broken
atomic_json(P/'ARTIFACTS.json',{'candidate_sha256':t['candidate_sha256'],'models_not_packaged':True,'broken_links':broken,
 'files':{path.relative_to(R).as_posix():{'sha256':file_hash(path),'bytes':path.stat().st_size} for path in sorted(set(paths))}})
print(json.dumps({'status':'COMPLETE_TRAINED_NOT_ACTIVATED','steps':t['optimizer_steps'],'seconds':t['elapsed_seconds'],
 'validation_macro_f1':m['macro_f1'],'decision':v['decision'],'protected':len(protected),'related_tests_passed':42}))
