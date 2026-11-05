from pathlib import Path
import json,re
R=Path.cwd();p=next((R/'tasks/moderation-ai').glob('T028-*.md'));previous=p.read_text(encoding='utf-8')
new='''# T028 — AI-authored synthetic dataset and context recovery regression

- **Status:** IN_PROGRESS
- **Priority:** P1
- **Dependencies:** T021,T027
- **Protocol:** synthetic_research_context_recovery_v1
- **Owner:** Codex tự viết hội thoại, gán nhãn AI và kiểm thử; nhãn người dùng cung cấp được lưu riêng.

## Phạm vi mới nhất — yêu cầu GAME_RANK_30

Người dùng yêu cầu tự sinh dataset, không cần dữ liệu thực tế, đồng thời sửa task. REAL/contact/collector/human gold không còn là điều kiện hoàn thành T028 hiện hành. Không đổi dữ liệu đã thu thật hoặc biến nhãn AI thành gold; hồ sơ REAL cũ giữ làm lịch sử tùy chọn.

Tái sử dụng GenZ500/5115comments đã có và không sửa frozen split/labels. Trước khi chỉnh rule, AI đã viết thêm12thread/120comments trong datasets/fixtures/context_recovery_v1, gồm can ngăn, nhận lỗi, xin lỗi, cảm xúc người bị công kích và các phản ví dụ có công kích mới.30nhãn GAME theo người dùng nằm game_rank_30_reference.json: c08,c11,c15,c18TOXIC,26câu còn lạiCLEAN; reference-only, không human gold hay independent test. Không sửa kỳ vọng để pass.

## Acceptance

1. Kiểm kê/sinh thực sự dataset synthetic, IDs/parent/timestamp/duplicates và provenance; không train.
2. Freeze user reference và AI counterexamples trước khi sửa code.
3. Đo before/after raw V1/context/lexicon/final advisory riêng trên GAME30, các thread regression còn lại và GenZdevelopment; giữ score/0.41/checkpoint/test độc lập.
4. Cải thiện context theo mệnh đề; xin lỗi/nhận lỗi không loại trừ công kích mới. Tách reply_to_user_id khỏi directed_at_user_id; GAME evidence chính xác c08,c11,c15,c18, không c21,c23.
5. Regression/API/UI tests; ghi rõ mọi suy giảm và abstention. Cập nhật AUTO_PROGRESS; không deploy.

## Thực hiện

Dataset đã sinh12/120,30user-reference; ứng dụng chưa sửa khi dữ liệu được khóa. Initial authoring audit chỉ sửa1cờ repeated từ hai công kích cùng actor/target, không thay text/label/target; bản đầu giữ trong reports/ai_update/context_recovery_20261103/generation_initial. Việc tiếp: snapshot before, sửa context/assessment/UI, kiểm thử.

<details>
<summary>Scope và bằng chứng trước yêu cầu mới — lịch sử, không còn là dependency REAL bắt buộc</summary>

'''+previous+'\n</details>\n'
p.write_text(new,encoding='utf-8')
p=R/'AGENTS.md';s=p.read_text(encoding='utf-8');s=re.sub(r'(?m)^- Theo yêu cầu autonomous mới nhất.*$', '- Yêu cầu GAME_RANK_30 mới nhất chuyển T028 sang synthetic-only: tự viết dữ liệu/nhãn AI, không cần REAL/contact/human gold. Giữ reference người dùng riêng, không sửa kỳ vọng để pass. Scope cũ là lịch sử; xem task nguồn/AUTO_PROGRESS. Giữ V1/0.41/test độc lập và quyền GPU/cost/production.',s);p.write_text(s,encoding='utf-8')
p=R/'.agents/skills/shieldvi-ai-upgrade/SKILL.md';s=p.read_text(encoding='utf-8');s=s.replace('- Yêu cầu mới nhất 03/11/2026 tách REAL200/T028 khỏi fallback synthetic500. Không có real gold thì T028 BLOCKED; không tính synthetic thành real. Nhãn AI được dùng nghiên cứu/augmentation và vẫn không phải human gold.','- Yêu cầu GAME_RANK_30 mới nhất chuyển T028 sang synthetic-only: sinh và kiểm dataset AI, không phụ thuộc REAL/contact hoặc human gold. Nhãn người dùng là reference riêng, không tự thành independent gold. Giữ dữ liệu cũ bất biến; khi sửa context phải kiểm cả công kích mới sau xin lỗi/nhận lỗi và báo suy giảm ở thread khác.')
p.write_text(s,encoding='utf-8')
for p in (R/'tasks/moderation-ai/TASK_ORDER_AI.md',R/'tasks/TASK_ORDER.md'):
 s=p.read_text(encoding='utf-8');lines=[]
 for line in s.splitlines():
  if line.startswith('| ') and ('**T028**' in line or '[T028](' in line):
   cols=line.split('|')
   if '**T028**' in line:cols[2]=' **T028** — Synthetic dataset + context recovery regression ';cols[-3]=' IN_PROGRESS ';cols[-2]=' Không cần REAL; AI12thread/120comments mới,30reference người dùng; đang đo/sửa '
   else:cols[-2]=' IN_PROGRESS ';cols[-3]=' Synthetic-only theo yêu cầu mới; REAL không chặn, chưa train '
   line='|'.join(cols)
  lines.append(line)
 s='\n'.join(lines)+'\n';s+='\n## Active GAME_RANK_30 revision\n\nLatest user request supersedes REAL requirement: T028 synthetic-only IN_PROGRESS. AI12newthreads/120comments generated before rule edits; original GenZ500/test intact;30user-reference labels frozen separately from gold. Work on context/assessment/reply-target/repeated plus before-after regression; no training/deploy. Earlier REAL blockers/handoff are historical.\n';p.write_text(s,encoding='utf-8')
with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as f:f.write('\n## ACTIVE — GAME_RANK_30 context recovery, synthetic-only T028\n\nUser explicitly replaces REAL prerequisite with self-authored synthetic data. T028 IN_PROGRESS; GenZ500 unchanged;12newthreads/120AI comments generated in datasets/fixtures/context_recovery_v1 before app rules change. GAME30 user reference frozen:4TOXIC(c08,c11,c15,c18),26CLEAN; not gold. Authorship metadata audit repaired1repeat flag without label/text/target changes; first generation preserved. No train. Next capture originalV1 before scores/signals, then context/assessment/API/UI changes and regression report including losses.\n')
print('T028 scope changed to synthetic-only; original confirmed DONE tasks unchanged')
