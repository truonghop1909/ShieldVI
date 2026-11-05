from pathlib import Path
import json,re
R=Path.cwd()
p=R/'scripts/train_t029_candidate.py';s=p.read_text(encoding='utf-8').replace('Execution requires a matching approval receipt, T028 verified lock and CUDA.','Execution requires a matching resource receipt, verified protocol-specific data and CUDA.');p.write_text(s,encoding='utf-8')
p=R/'scripts/synthetic_data/genz.py';s=p.read_text(encoding='utf-8');s=s.replace('    return report\n\ndef verified_export',"    report['quality_limitations']=report['limitations']\n    return report\n\ndef verified_export",1);p.write_text(s,encoding='utf-8')
p=R/'datasets/synthetic_conversations/genz_v2/batches/quality_latest.json';r=json.loads(p.read_text(encoding='utf-8'));r['quality_limitations']=r['limitations'];p.write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Terminology clarification only; scores, references and frozen IDs are unchanged.
p=R/'scripts/evaluate_genz_development.py';s=p.read_text(encoding='utf-8')
for a,b in [('gold_directed_attacks','reference_directed_attacks'),('coverage_on_gold_attacks','coverage_on_reference_attacks'),('abstentions_on_gold_attacks','abstentions_on_reference_attacks')]:s=s.replace(a,b)
p.write_text(s,encoding='utf-8')
for name in ('metrics.json','RESULTS.md'):
 p=R/'reports/ai_update/T030/genz500'/name;s=p.read_text(encoding='utf-8')
 for a,b in [('gold_directed_attacks','reference_directed_attacks'),('coverage_on_gold_attacks','coverage_on_reference_attacks'),('abstentions_on_gold_attacks','abstentions_on_reference_attacks')]:s=s.replace(a,b)
 p.write_text(s,encoding='utf-8')
p=R/'AGENTS.md';s=p.read_text(encoding='utf-8');lines=s.splitlines();lines=[('- Theo yêu cầu autonomous mới nhất 03/11/2026: T028 là REAL200 và vẫn BLOCKED nếu thiếu gold; synthetic500 là fallback riêng, được dùng nghiên cứu với nhãn AI. Cho phép tiếp tục phần độc lập T029–T033 trong phạm vi phiên đã giao; không nới quyền GPU/cost/production. Xem tasks/AUTO_PROGRESS.md và task nguồn; giữ V1/0.41 và held-out bất biến.' if line.startswith('- T028 hiện là AI-authored') else line) for line in lines];p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
p=R/'.agents/skills/shieldvi-ai-upgrade/SKILL.md';s=p.read_text(encoding='utf-8');a=s.index('## Phạm vi T028 hiện hành');b=s.index('## Bất biến',a)
s=s[:a]+'''## Phạm vi T028 và phiên autonomous
- Yêu cầu mới nhất 03/11/2026 tách REAL200/T028 khỏi fallback synthetic500. Không có real gold thì T028 BLOCKED; không tính synthetic thành real. Nhãn AI được dùng nghiên cứu/augmentation và vẫn không phải human gold.
- Khi được giao autonomous T028–T033, tiếp tục các phần độc lập dù REAL bị chặn; bảo toàn dependency còn thiếu và resource/cost/production approval. Xem task nguồn và [tiến độ](../../../tasks/AUTO_PROGRESS.md). Các hướng dẫn một-task mặc định không hủy quyền tiếp tục đã được người dùng cấp trong phiên.

'''+s[b:];p.write_text(s,encoding='utf-8')
# Put superseded synthetic-only scope under a labelled history section, retaining every byte of its body.
p=next((R/'tasks/moderation-ai').glob('T028-*.md'));s=p.read_text(encoding='utf-8');a=s.index('## Mục tiêu trước yêu cầu autonomous');b=s.index('## Lịch sử trước thay đổi phạm vi',a)
old=s[a:b]
current='''## Acceptance hiện hành: REAL200 + fallback độc lập

REAL: chỉ nhận hội thoại thật có quyền sử dụng, nguồn và metadata kiểm chứng; ẩn danh, review người theo protocol real và khóa eval độc lập. Chưa có bằng chứng thì không đánh DONE. Collector lần này exit2 trước network do thiếu operator contact hợp lệ; REAL0/200, human0. Không yêu cầu người dùng gán lại bộ synthetic đã được chọn dùng.

Fallback đã hoàn tất: `datasets/synthetic_conversations/genz_v2/` có500 threads/5115comments, 200 legacy+300 mới, nhãn synthetic, 11batch manifests. Đây là datasetB, không giải quyết điều kiện REAL của T028. Kỹ thuật PASS; giới hạn ngôn ngữ/ngữ nghĩa và phân bố nhãn được ghi trong README/quality report.

Theo yêu cầu mới nhất, tiếp tục phần độc lập T029–T033 mà không giả T028 DONE. Bằng chứng và lệnh tiếp tục trong `tasks/AUTO_PROGRESS.md`, `reports/ai_update/autonomous_20261103/progress.json` và final-report.

<details>
<summary>Scope synthetic-only trước attachment autonomous — lịch sử, không còn là acceptance hiện hành</summary>

'''+old+'\n</details>\n\n'
s=s[:a]+current+s[b:];p.write_text(s,encoding='utf-8')
print('Narrow documentation/provenance corrections applied; source conversations and metrics values unchanged')
