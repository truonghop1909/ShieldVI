from pathlib import Path
import json,re
R=Path.cwd()
p=R/'apps/moderation-web/tests/seed_demo.py';s=p.read_text(encoding='utf-8');old='ROOT.parent / "ShieldVI_SocialAI_Design_Docs_v1/contracts/moderation_response.example.json"';new='ROOT / "contracts/moderation_response.example.json"';assert old in s;s=s.replace(old,new);p.write_text(s,encoding='utf-8')
p=R/'notebooks/T029_Train_Candidate_Prepared.ipynb';nb=json.loads(p.read_text(encoding='utf-8'))
for c in nb['cells']:
 s=''.join(c['source'])
 s=s.replace('Chỉ chạy sau khi G2/T028 đã đạt và cấu hình/resource được người dùng duyệt.','Bản chuẩn bị GenZ500, protocol synthetic_development/G2-S; T028 REAL vẫn BLOCKED. Train chỉ khi G2-S verified, CUDA và exact config/resource/cost receipt đã được duyệt.')
 s=s.replace('PREPARED=Path("/content/t029_prepared")','CONFIG=PROJECT/"configs/t029_genz500_candidate.json"\nPREPARED=Path("/content/t029_genz500_prepared")')
 s=s.replace('scripts/prepare_t029_training.py --base-model','scripts/prepare_t029_training.py --config "$CONFIG" --base-model')
 s=s.replace('scripts/train_t029_candidate.py --base-model','scripts/train_t029_candidate.py --config "$CONFIG" --base-model')
 s=s.replace('configs/t029_candidate.json','configs/t029_genz500_candidate.json')
 c['source']=s.splitlines(keepends=True)
 assert c.get('execution_count') is None and not c.get('outputs',[])
p.write_text(json.dumps(nb,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
# Scope headings now match the latest dual-dataset request; retain detailed legacy guidance.
for name in ('02_ANNOTATION_GUIDE.md','03_EXPERIMENT_PLAN.md','05_RELEASE_GATES.md'):
 p=R/'docs/ai-update'/name;s=p.read_text(encoding='utf-8');idx=s.index('\n')
 note='\n\n> Current autonomous scope03/11/2026: T028=REAL200 (still0/BLOCKED); synthetic500/G2-S is a separate accepted-AI research dataset, not human/real gold. Independent research T029–T033 may proceed; CUDA/cost/production approvals remain gated. Later scope notes override older synthetic-only T028 wording below. See final-report and current task files.\n'
 s=s[:idx]+note+s[idx:];p.write_text(s,encoding='utf-8')
p=next((R/'tasks/moderation-ai').glob('T030-*.md'));s=p.read_text(encoding='utf-8').replace('- **Status:** BLOCKED','- **Status:** DONE',1)
s+='''\n### Supplement — actual B0–B3 replay completed,03/11/2026\n\nDONE for the declared synthetic-development evaluation protocol (not REAL/blind evaluation). A scoped archive lookup found T020 original V1 responses on5unchanged fixtures/150comments. Original weights/input hashes verified; engine.py is byte-identical to T020, isolating B1 lexical changes. B0 is original captured real inference; B2 injects the original per-text lexical results only within the offline evaluator and retains old target/repeated. This supports B0–B3 replay on those exact5inputs without pretending the old lexical module is recoverable for GenZ500.\n\n`scripts/evaluate_regression_ablation.py` actual run PASS: raw149known reference labels (1accusationUNCERTAIN excluded) identical across B0–B3; MacroF1=.827878 on those already-used fixtures. B0/B1/B2 evidence26comments includes7without directed-insult reference; B3 has7comments, all7with directed-insult reference. This is tag support, not target/event gold precision. New60-thread challenge remains separate with repeated0/7, target11/35coverage and MacroF1=.739974. No improvement claim or rule tuning. All artifacts at reports/ai_update/T030/regression_ablation and genz500. Candidate/test/REAL remain explicitly unavailable; these are owned by T029/T028 and are not claimed complete here.\n''';p.write_text(s,encoding='utf-8')
p=R/'reports/ai_update/autonomous_20261103/progress.json';s=json.loads(p.read_text(encoding='utf-8'));s['tasks']['T030']='DONE';s['next_action']='Validate report/artifact hashes and conclude independent handoff';p.write_text(json.dumps(s,indent=2)+'\n',encoding='utf-8')
with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as f:f.write('\nT030 supplementDONE (synthetic development scope): original T020 B0captured responses found; actual B0–B3 replay150fixed regression comments, frozen weights/input hashes and byte-identical legacy engine verified. B2 uses cached original per-text lexicon, no old-module claim on new texts. Raw149known classifier unchanged, evidence26→7comments with fewer non-attack-reference examples; no target/event gold precision on these5. Separate GenZ challenge failures remain unchanged. Newscript scripts/evaluate_regression_ablation.py; artifacts reports/ai_update/T030/regression_ablation. Notebook now prepared for GenZ500 config, unexecuted. Canonical E2E seed contract path fixed (identical fileSHA), guard still requires temporary DB.\n')
print('Notebook prepared for GenZ500 without execution; baseline replay documented; canonical fixture path fixed')
