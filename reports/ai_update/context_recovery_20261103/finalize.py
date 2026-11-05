from pathlib import Path
import json,re,hashlib
from urllib.parse import unquote
R=Path.cwd();P=R/'reports/ai_update/context_recovery_20261103';report=R/'docs/ai-update/CONTEXT_RECOVERY_GAME_RANK_30.md'
def read_log(path):
 data=path.read_bytes()
 return data.decode('utf-16' if data[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8-sig')
# Confirm real command evidence before marking the task complete.
assert '417 passed' in read_log(P/'handoff_tests.txt')
assert '177 passed' in read_log(P/'social_tests.txt')
assert json.loads((P/'real_api_smoke.json').read_text(encoding='utf-8'))['status']=='PASS'
assert json.loads((P/'dashboard_browser_smoke.json').read_text(encoding='utf-8'))['status']=='PASS'
cleanup=json.loads((P/'social_e2e/cleanup.json').read_text(encoding='utf-8'));privacy=json.loads((P/'social_e2e/log-privacy.json').read_text(encoding='utf-8'))
assert cleanup['owned_processes_exited'] and not privacy['sensitive_markers_found_in']
assert '1 passed' in read_log(P/'social_e2e_runner.txt')
assert 'built in' in read_log(P/'dashboard_build.txt')
s=report.read_text(encoding='utf-8');s=s.replace('Đang chờ xác nhận log fullsuite cuối; Social177PASS', 'Full root417PASS/1warning, Social177PASS/1warning')
s=s.replace('Không train, đọc nhãn test độc lập để tune, đổi DBthật, tự gán human gold, push hoặc deploy.', 'Không train; không dùng nhãn test độc lập để tune; không đổi DBthật, tự gán human gold, push hoặc deploy.')
s+='\n[Log root417PASS](../../reports/ai_update/context_recovery_20261103/handoff_tests.txt) · [Social177PASS](../../reports/ai_update/context_recovery_20261103/social_tests.txt) · [BrowserDashboard](../../reports/ai_update/context_recovery_20261103/dashboard_browser_smoke.json) · [SocialE2E](../../reports/ai_update/context_recovery_20261103/social_e2e_runner.txt) · [API thật sau sửa](../../reports/ai_update/context_recovery_20261103/real_api_smoke.json) · [Integrity](../../reports/ai_update/context_recovery_20261103/integrity_audit.json).\n'
report.write_text(s,encoding='utf-8')
p=R/'datasets/fixtures/context_recovery_v1/README.md';s=p.read_text(encoding='utf-8');s+='\n[Root-cause, before/after and remaining errors](../../../docs/ai-update/CONTEXT_RECOVERY_GAME_RANK_30.md).\n';p.write_text(s,encoding='utf-8')
p=next((R/'tasks/moderation-ai').glob('T028-*.md'));s=p.read_text(encoding='utf-8').replace('- **Status:** IN_PROGRESS','- **Status:** DONE',1)
s+='''\n## GAME_RANK_30 acceptance — DONE theo scope synthetic-only mới nhất\n\nAI tự viết12thread/120comments trước khi sửa rule; dataset500/5115 cũ và test độc lập bất biến.30nhãn user-reference frozen, không gold. ActualV1before890comments và realAPIafter30GAME; raw/checkpoint0.41 bất biến. GAMEadvisory TP4/FP0/TN26/FN0; raw vẫn TP4/FP5. Đã tìm bundlelegacy cũ, cập nhật bundle demo sangV2 và thêm assessment/policy/reply-target riêng. Evidenceexact c08,c11,c15,c18; nhận lỗi/xin lỗi không tạo lượt mới.\n\n417rootPASS/1warning,177SocialPASS/1warning, DashboardbrowserPASS,realscoreAPI/PydanticPASS, SocialfiveprocessE2E1PASS, DashboardbuildPASS. Không runtimeJSONSchema validator vì package chưa cài; typedDTOparse/schema generation verified. Initial4regressions đã sửa và log giữ nguyên; cuối0lỗi mới trên890comments, nhưng GenZcòn16FP/9FN và repeated0/7, không giấu residual misses.\n\nBáo cáo docs/ai-update/CONTEXT_RECOVERY_GAME_RANK_30.md; progress reports/ai_update/context_recovery_20261103/progress.json. Không còn REAL/contact prerequisite trong T028 hiện hành. T029 vẫn thiếu CUDA/G3; không train/deploy hoặc tự bắt đầu task khác.\n''';p.write_text(s,encoding='utf-8')
# Keep confirmed task states; record one authorized follow-up across context/target/repeated/schema/UI.
for tid in ('T022','T024','T025','T026'):
 p=next((R/'tasks/moderation-ai').glob(tid+'-*.md'));s=p.read_text(encoding='utf-8');s+='\n### User-authorized GAME_RANK_30 follow-up\n\nConfirmed DONE status preserved. Context-v2/ACKNOWLEDGEMENT + clause scope, additive reply/attacktarget/assessment/policy fields, exact4attack GAMEevidence and localDashboardV2 updated. Root417PASS,Social177PASS,2browser checks/build/realV1smokePASS; residual GenZ repeated0/7 disclosed. Details: docs/ai-update/CONTEXT_RECOVERY_GAME_RANK_30.md and AUTO_PROGRESS. No labels/checkpoint/0.41/test changes or production deploy.\n';p.write_text(s,encoding='utf-8')
p=next((R/'tasks/moderation-ai').glob('T029-*.md'));s=p.read_text(encoding='utf-8');s+='\nLatest scope note — GAME_RANK_30: T028 synthetic-only DONE; REAL/contact is not a research-training prerequisite. T029 status remains BLOCKED because localCUDA/G3 resource receipt is missing. No fine-tune performed; latest prepared config remains t029_genz500_candidate.json.\n';p.write_text(s,encoding='utf-8')
for p in (R/'tasks/TASK_ORDER.md',R/'tasks/moderation-ai/TASK_ORDER_AI.md'):
 s=p.read_text(encoding='utf-8');lines=[]
 for line in s.splitlines():
  if line.startswith('| ') and ('**T028**' in line or '[T028](' in line):
   parts=line.split('|')
   if '**T028**' in line:parts[-3]=' DONE ';parts[-2]=' Synthetic-only;12new/120 + GAME30reference;417root/177Social PASS; no train '
   else:parts[-2]=' DONE ';parts[-3]=' Synthetic-only;512syntheticthreads total; GAMEcontext regression verified '
   line='|'.join(parts)
  lines.append(line)
 s='\n'.join(lines)+'\n'
 if p.name=='TASK_ORDER_AI.md':
  a=s.index('## Điểm tiếp tục hiện hành');s=s[:a]+'''## Điểm tiếp tục hiện hành — GAME_RANK_30

T028 synthetic-only DONE theo yêu cầu mới nhất, không cần REAL/contact/human gold. GenZ500/5115 giữ nguyên;AI12thread/120comment mới,30user-reference riêng/notgold. LocalDashboard đã thay bundlelegacy bằngV2; raw/context/assessment/policy/reply-target riêng. GAMErawTP4/FP5 không đổi, assessmentTP4/FP0/FN0; evidenceexact c08,c11,c15,c18.

Root417PASS,Social177PASS,browserDashboardPASS,SocialE2E1PASS,buildDashboardPASS,actualV1APIafterPASS.0suy giảm mới trên890comments đã kiểm, nhưng GenZrepeated vẫn0/7. Không claim blind/realworld hoặc traincandidate. T029/T031 giữBLOCKED(CUDA/G3,candidate/activation); các DONE khác giữ nguyên. ScopeREAL cũ là lịch sử tùy chọn.

[Báo cáo](../../docs/ai-update/CONTEXT_RECOVERY_GAME_RANK_30.md) · [Tiến độ](../AUTO_PROGRESS.md). Dừng sau sửa được giao; demo cần restartbackend vàCtrl+F5, không deploy.
'''
 else:s+='\n## Current GAME_RANK_30 handoff\n\nT028synthetic-only DONE, REAL/contact không còn bắt buộc. AI12newthread/120comments +30userreference riêng;500GenZ bất biến. Root417/Social177PASS,browser2checks/buildPASS, actualV1afterPASS. T029/T031 BLOCKED về GPU/candidate, không phải dữ liệu thật. Không tự train hoặc deploy; các mục scopeREAL trước đó là lịch sử. Xem taskAI/AUTO_PROGRESS và CONTEXT_RECOVERY_GAME_RANK_30 report.\n'
 p.write_text(s,encoding='utf-8')
state={'status':'COMPLETE_REQUESTED_FIX_NOT_MODEL_TRAINING','task':'T028','task_status':'DONE','protocol':'synthetic_research_context_recovery_v1','real_required':False,'real_collected_in_session':0,
 'existing_GenZ_threads_unchanged':500,'new_AI_threads':12,'new_AI_comments':120,'user_reference_comments':30,'human_gold':False,
 'game_raw_before_after':{'tp':4,'fp':5,'tn':21,'fn':0},'game_advisory_after':{'tp':4,'fp':0,'tn':26,'fn':0},'raw_scores_changed':False,
 'game_evidence':['c08','c11','c15','c18'],'cross_thread_new_errors':0,'GenZ_remaining_repeated_fn':7,
 'tests':{'root_passed':417,'Social_passed':177,'Dashboard_browser':'PASS recorded-response replay','Social_E2E':'PASS fixture AI','actual_V1_after_API':'PASS','Dashboard_build':'PASS','jsonschema_validator':'NOT_INSTALLED_TYPED_DTO_PASSED'},
 'initial_regressions_preserved_in':'attempt1_before_after.json','candidate':'NOT_TRAINED','threshold':.41,'production_deployed':False,'local_demo_static_updated':True,
 'next_action':'Restart the local backend and hard-refresh /dashboard/ to use V2. No further task started; T029 still requires CUDA and exact resource approval. Never turn these development references into independent gold.'}
(P/'progress.json').write_text(json.dumps(state,indent=2)+'\n',encoding='utf-8')
with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as f:f.write('''\n## CURRENT — GAME_RANK_30 synthetic context recovery COMPLETE\n\nLatest request replaces REAL prerequisite: T028synthetic-only DONE; no real/contact/manualgold required. AI12threads/120comments created before rule edits in datasets/fixtures/context_recovery_v1; original500/5115unchanged. GAME30userreference frozen separately,4TOXIC(c08,c11,c15,c18)/26CLEAN,notgold. No expectedlabel changes; initialmetadata audit repaired1repeat flag without text/label/target edits.\n\nActual beforeV1CPU890comments, aftercache+actualV1API30GAME: raw4TP/5FP/21TN/0FN unchanged; contextual assessment4TP/0FP/26TN/0FN. Main rootcause served oldstatic index-B6t7Eu4q.js called /api/analyze; source wasV2but bundle stale. Newlocalbundle callsV2 with raw/assessment/policy/reply-target separated; c21ACK and clause-scoped new-attack recognition added. ExactGAMErepeat evidence4comments; no c21/c23. Restart backend/hardrefresh required for user session; no existing process killed.\n\nTests actual: root417PASS/1warning(handoff_tests.txt);Social177PASS/1warning;DashboardChrome replayPASS;Social5processfixtureE2E1PASS;DashboardbuildPASS;actualV1afterAPI/PydanticPASS(static200/legacy200). jsonschema runtimevalidator missing; schema generated from typedmodel. Initial rulepass4regressions+quote case fixed, storedattempt1/firsttests. One newtest had accidentalUnicodewrite corruption; restored intended text, expectedclass unchanged. One collector tempfile WinError5 transient; freshbasetemp recheckPASS, no collector/testexpected edits.\n\nFinal0newerrors/abstentions vsraw and0newcontext errors on890developmentcomments. Residuals explicitly retained: GenZ16FP/9FN/0of7repeated events recovered;4otherfixtures4FP/1FN. New120assessmentallcorrect onAIrefs; not human/realworld accuracy. TargetGenZcorrect11→13of35, coverage37.14%, no targeterrors; no target/eventgold for4otherfixtures. No hide of residuals, no test/threshold tuning.\n\n31protectedartifacts+200oldthreads/2CSV+500GenZ/exports/frozenlocks unchanged; no modeltraining/checkpoint/default0.41/realDB change/push/productiondeploy. Humanlabels not autosaved. T022/T024/T025/T026 confirmedDONE retained with follow-up evidence;T029/T031 stillBLOCKED(CUDA/G3,candidate) and not started. T030/T032/T033 earlierhandoff remains historical.\n\nResume rootE:/lamDoAn/ShieldVI_V3_Hybrid_Review. Currentprogress reports/ai_update/context_recovery_20261103/progress.json; report docs/ai-update/CONTEXT_RECOVERY_GAME_RANK_30.md. Source scripts/evaluate_context_recovery.py(beforeimmutable;afterreusesactualscores), scripts/audit_context_recovery_evidence.py, scripts/smoke_context_dashboard.mjs; original fixture unchanged. Prior autonomous progress.json/ARTIFACTS are historical; do not overwrite their hashes to look current. Next user step restartbackend onlocalport andCtrl+F5, or supply approvedCUDA config for a separately authorized train; do not auto-startT029.\n''')
# Check links across current deliverables and tracking files.
files=[report,R/'datasets/fixtures/context_recovery_v1/README.md',R/'AGENTS.md',R/'.agents/skills/shieldvi-ai-upgrade/SKILL.md',R/'tasks/TASK_ORDER.md',R/'tasks/moderation-ai/TASK_ORDER_AI.md',next((R/'tasks/moderation-ai').glob('T028-*.md'))]
missing=[];count=0
for p in files:
 for link in re.findall(r'\]\(([^)]+)\)',p.read_text(encoding='utf-8')):
  link=link.strip('<>').split('#',1)[0]
  if not link or link.startswith(('http:','https:','mailto:')):continue
  count+=1
  if not (p.parent/unquote(link)).resolve().exists():missing.append({'file':str(p.relative_to(R)),'target':link})
assert not missing,missing
# New-version manifest; historical artifacts remain untouched.
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tracked=files+[R/'tasks/AUTO_PROGRESS.md',R/'contracts/analysis_response_v2.schema.json']
tracked += [R/'services/moderation-ai/app'/n for n in ('context_signals.py','context_assessment.py','signal_engine.py','schemas.py','engine.py','target_signals.py','lexical.py')]
tracked += [R/'apps/moderation-web/legacy-v3/src'/n for n in ('App.jsx','utils.js')]
tracked += [R/'scripts'/n for n in ('generate_context_recovery_dataset.py','evaluate_context_recovery.py','audit_context_recovery_evidence.py','smoke_context_dashboard.mjs','synthetic_data/context_recovery_catalogue.txt')]
tracked += [R/'tests/test_context_recovery_regression.py']
tracked += [p for p in P.glob('*.json') if p.name!='ARTIFACTS.json']+[P/'handoff_tests.txt',P/'social_tests.txt',P/'dashboard_build.txt',P/'social_e2e_runner.txt']
tracked += list((R/'datasets/fixtures/context_recovery_v1').glob('*.json'))
for tid in ('T022','T024','T025','T026','T029'):tracked.append(next((R/'tasks/moderation-ai').glob(tid+'-*.md')))
manifest={'scope':'GAME_RANK_30 recovery, synthetic-only','historical_handoffs_not_rewritten':True,'linked_files_checked':count,'missing_links':missing,
 'files':{str(p.relative_to(R)).replace('\\','/'):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(set(tracked))},
 'dataset_thread_checksums_in':'datasets/fixtures/context_recovery_v1/manifest.json','protected_unchanged_in':'reports/ai_update/context_recovery_20261103/integrity_audit.json'}
(P/'ARTIFACTS.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'T028':'DONE','new_AI_threads':12,'new_AI_comments':120,'root_passed':417,'Social_passed':177,'links_checked':count,'new_cross_thread_errors':0,'historical_misses_disclosed':True}))
