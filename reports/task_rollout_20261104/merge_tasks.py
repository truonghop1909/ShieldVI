"""Merge verified task pack, preserve source and historical task states."""
import json,hashlib,re,sys
from pathlib import Path
R=Path(__file__).resolve().parents[2];P=Path(__file__).resolve().parent
sys.path.insert(0,str(R/'scripts'))
from synthetic_data.pipeline import atomic_json,file_sha
SOURCE=Path('E:/lamDoAn/ShieldVI_T034_T043_Realtime_Training_Tasks/ShieldVI_T034_T043')
NAMES={34:'realtime-moderation-architecture',35:'durable-live-messaging-ai-jobs',36:'incremental-conversation-analysis',37:'live-conversation-client',
38:'live-moderator-board',39:'dataset-center',40:'annotation-studio',41:'training-studio',42:'evaluation-studio-model-registry',43:'realtime-studio-e2e-handoff'}
DEPS={34:[],35:[34],36:[34,35],37:[34,35,36],38:[35,36,37],39:[34],40:[39],41:[39],42:[41],43:list(range(35,43))}
SPEC={
34:('docs/realtime_moderation/','contracts/realtime_event.schema.json','SSE authenticated fetch; stable cursor, public-post read permission + explicit membership, no browser AI token.'),
35:('services/social-api/src/shieldvi_social/','/api/live/threads/{post_id}/events','Reuse Post/Comment/ModerationJob/ModerationResult and Worker. Add transactional event log; retain existing revision/idempotency policy.'),
36:('services/moderation-ai/app/','/api/live/moderate/comment','Default-v5 context with bounded score cache; no v6.1/v6.2 default selection. New endpoint/worker opt-in, original endpoints unchanged.'),
37:('apps/social-web/','/live','Fetch SSE with Authorization, cursor replay, reconnect backoff, dedupe revisions, pending send reconciliation; two browser contexts.'),
38:('apps/moderation-web/','/api/live/moderator/events','Reuse review/appeal RBAC and audit; staff-only evidence, manual visibility changes with reason/version.'),
39:('services/social-api/ and apps/moderation-web/','/api/studio/datasets','Bounded UTF8 CSV/JSON/JSONL import, mapping, immutable source SHA/version, rights quarantine, exclusion/leakage preflight.'),
40:('scripts/real_dataset/ and apps/moderation-web/','/api/studio/annotations','Reuse solo two-round revision workflow; blind mode, no fabricated human labels; separate AI suggestions.'),
41:('scripts/ and services/social-api/','/api/studio/training-runs','Real isolated CPU head-only smoke after dataset eligibility; max4CPUthreads/900s/cost0, distinct T041 run, not r07; safe config allowlist/cancel, no default promotion.'),
42:('scripts/ and apps/moderation-web/','/api/studio/models','Reuse registry/rollback tooling; same-dataset paired metrics with SHA/scope, proposal only, no activation.'),
43:('scripts/ and docs/ai-update/final-report/','local Windows demo runner','Disposable DB/accounts, real training/inference evidence separate from fixture tests; two-client/moderator E2E and measured timestamps, safe cleanup.')}

def old_states():
    return {p.relative_to(R).as_posix():re.findall(r'^(?:-\s+)?\*\*(?:Status|Trạng thái):\*\*\s*(.+)$',p.read_text(encoding='utf-8-sig'),re.M)[0]
        for p in (R/'tasks').rglob('T0*.md') if re.search(r'^(?:-\s+)?\*\*(?:Status|Trạng thái):\*\*',p.read_text(encoding='utf-8-sig'),re.M)}

if __name__=='__main__':
    state_path=R/'tasks/moderation-ai/AUTO_EXECUTION_STATE.json';assert not state_path.exists()
    manifest=json.loads((SOURCE/'MANIFEST_SHA256.json').read_text(encoding='utf-8'))
    for name,digest in manifest.items():assert file_sha(SOURCE/name)==digest
    historical=old_states();assert len(historical)==27
    imported=[];commons=[];task_files={}
    for number,slug in NAMES.items():
        candidates=list((R/'tasks').rglob(f'T{number:03}[-_]*.md'));assert not candidates,('Existing task requires manual content merge',candidates)
        source=next((SOURCE/'tasks/moderation-ai').glob(f'T{number:03}_*.md'));text=source.read_text(encoding='utf-8')
        body,common=text.split('## Quy tắc chung và bảo vệ hệ thống',1);commons.append(common)
        dest=R/'tasks/moderation-ai'/f'T{number:03}-{slug}.md';scope,contract,design=SPEC[number]
        dependency=', '.join(f'T{x:03}' for x in DEPS[number]) or 'Read verified T033 architecture; formal T033 completion is not a prerequisite'
        supplements=f'''
## Implementation specification (repository audit 04/11/2026)

- **Status:** NOT_STARTED
- **Dependencies:** {dependency}. FormalT028/T029 BLOCKED and T030–T033 PARTIAL remain independent.
- **Architecture context:** Social API FastAPI/SQLAlchemy schema0004, bearer sessions; posts/comments, durable worker and review/appeal already exist. Approved AI defaultV1.1 with threshold.41; v5 signal rules, legacy internal contract1.0.
- **Input:** authenticated requests and immutable synthetic fixtures; canonical model/dataset manifests when applicable.
- **Output:** implemented behavior below, versioned contract, test logs, source SHA, task evidence.
- **Backend/frontend/AI/database scope:** `{scope}`; reuse existing modules and original API. No live migration/default-model mutation.
- **Concrete design:** {design}
- **Contract/schema:** `{contract}`; pin schema/version, IDs, content_revision, decision_version and analysis provenance; fail closed on unknown version.
- **Acceptance:** all original Nghiệm thu criteria above plus existing tests pass, negative authorization/error paths verified. NOT_RUN is not PASS; no DONE_VERIFIED from docs alone.
- **Unit tests:** valid/malformed schema, limits, stale revision, duplicate IDs, unauthorized caller and absence of side effects.
- **Integration tests:** real temporary SQLite and existing services/worker, restart/retry/idempotency and transaction rollback. Actual inference/training tested separately when required.
- **E2E:** local browser when UI is in scope, independent contexts, no mocked API claimed as actual. For architecture-only T034, contract/sequence validation replaces browser testing.
- **Security/privacy:** bearer auth + server RBAC; membership/post visibility checked; no credentials in URL/log, no raw evidence to normal user; upload/config allowlists and no shell/eval of external input.
- **Errors/recovery:** bounded retry/backoff; truthful queued/failed/cancelled/stale states; explicit missing rights/model/data; preserve user input and idempotency key across retries.
- **Performance:** cap body1MiB/request, content8000chars, context50comments, event page100, no neural inference in send request. These are budgets/limits, not measured latency promises; record real timings.
- **Evidence:** `reports/task_rollout_20261104/T{number:03}/`, test command/exit code, isolated DB/schema trace, measured timings and hashes. Secrets/raw private data excluded.
- **Definition of Done:** all task acceptance met with actual tests and retained evidence; otherwise PARTIAL/BLOCKED with exact missing criteria; update shared task order/progress.
- **Current risks/blockers:** no implementation evidence yet; GPU/paid/external/private data/production not authorized. Training Studio CPU smoke authorized by current user only after accepted synthetic dataset/preflight. T041 also depends on T040 for unlabeled inputs.

Common safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md). Imported source preserved at workspace task-pack path; SHA/rename map in TASK_MERGE_REPORT.md.
'''
        dest.write_text(body+supplements,encoding='utf-8');task_files[f'T{number:03}']=dest.relative_to(R).as_posix()
        imported.append({'source':str(source),'source_sha256':file_sha(source),'destination':dest.relative_to(R).as_posix()})
    assert len(set(commons))==1,'Common rules differ; retain individual variants before proceeding'
    (R/'tasks/moderation-ai/RULES_REALTIME_STUDIO.md').write_text('# Common safeguards T034–T043\n'+commons[0]+'\nLatest user authorization allows automatic local implementation/testing and an eligible bounded CPU Studio smoke, not r07, paid GPU or production. Existing locked files remain a baseline: prefer additive opt-in extensions; do not rewrite any readiness manifest.\n',encoding='utf-8')
    state={'scope':'T034–T043 local development','source_manifest_sha256':file_sha(SOURCE/'MANIFEST_SHA256.json'),'historical_task_states':historical,
        'tasks':{key:{'status':'NOT_STARTED','file':name,'dependencies':[f'T{x:03}' for x in DEPS[int(key[1:])]],'evidence':[]} for key,name in task_files.items()},
        'training_authorization':'T041 synthetic-only eligible bounded CPU smoke max4threads/900s/cost0; no r07/default/promotion',
        'current':'T034','production_activation_allowed':False}
    atomic_json(state_path,state);atomic_json(P/'MERGE_MANIFEST.json',{'source_untouched':True,'files':imported,'original_pack_files_verified':len(manifest),'historical_states':historical})
    order='\n\n## T034–T043 current authorized local rollout\n\n| Task | Status | Dependencies | File |\n|---|---|---|---|\n'
    for key,name in task_files.items():order+=f'| {key} | NOT_STARTED | '+','.join(state['tasks'][key]['dependencies'])+f' | [{Path(name).name}]('+ (Path(name).name if False else name.removeprefix('tasks/moderation-ai/'))+') |\n'
    with (R/'tasks/moderation-ai/TASK_ORDER_AI.md').open('a',encoding='utf-8') as f:f.write(order)
    with (R/'tasks/TASK_ORDER.md').open('a',encoding='utf-8') as f:f.write('\n\n## Local realtime/studio extension T034–T043\n\nSee [AI rollout order](moderation-ai/TASK_ORDER_AI.md), [execution state](moderation-ai/AUTO_EXECUTION_STATE.json), [dependencies](moderation-ai/TASK_DEPENDENCIES_T034_T043.md). New tasks do not change historical statuses or formalT028/T029 blockers.\n')
    (R/'tasks/moderation-ai/TASK_DEPENDENCIES_T034_T043.md').write_text('# Dependencies\n\nRealtime: T034→T035→T036→T037→T038. Studio: T034→T039→T040; T041 needsT039 andT040 for unlabeled data, thenT042. T043 needsT035–T042. Existing T008–T019 auth/content/jobs/review are reused. T028/T029 remain formalBLOCKED, T030–T033PARTIAL; no dependency is fabricated DONE.\n',encoding='utf-8')
    (R/'tasks/moderation-ai/TASK_ACCEPTANCE_MATRIX.md').write_text('# Acceptance matrix\n\n| Task | Required evidence | Status |\n|---|---|---|\n'+''.join(f'| T{n:03} | '+('Architecture+contract validation' if n==34 else 'Original acceptance + unit/integration'+('/browser' if n>=37 else '')+('/actual CPU train+reload' if n==41 else ''))+' | NOT_STARTED |\n' for n in NAMES),encoding='utf-8')
    (R/'tasks/moderation-ai/TASK_MERGE_REPORT.md').write_text('# T034–T043 merge report\n\nImported10task specifications from verified source pack; no existing taskID collision. Renamed to existing kebab-case convention, added concrete implementation/acceptance sections; deduplicated byte-identical common safeguards into RULES_REALTIME_STUDIO.md. Created execution state/dependency/acceptance/resume tracking; appended task orders. Kept all27historical task states, source pack, model/dataset/DB/reports/AGENTS unchanged. No ZIP scripts executed; directory pack available, no extraction required. Source map and SHA: reports/task_rollout_20261104/MERGE_MANIFEST.json. Git metadata absent; cannot claim clean/dirty commit status.\n\nNo source-content conflicts. Proposed endpoints adapted to audited API in task specs; implementation evidence currently absent. Links to future implementation paths are planned outputs, not existing functionality. Original start-prompt retained only in source backup, not made repository authority.\n',encoding='utf-8')
    (R/'tasks/AUTO_RESUME_T034_T043.md').write_text('# Resume T034–T043\n\nCanonical root ShieldVI_V3_Hybrid_Review. Read AUTO_PROGRESS and moderation-ai/AUTO_EXECUTION_STATE.json first. Merge complete/10tasksNOT_STARTED; nextT034 architecture/contracts. Existing Social API schema0004/auth/posts/comments/jobs/worker/review/appeal and both React apps reused. Prefer additive opt-in modules to preserve readiness1311SHA. No Git. Current user authorizes local autonomous tasks incl eligible T041CPU smoke, no r07/default/push/deploy. Continue ready tasks without routine confirmation. No automation runs after the Codex session ends.\n',encoding='utf-8')
    with (R/'tasks/AUTO_PROGRESS.md').open('a',encoding='utf-8') as f:f.write('\n\n## T034–T043 — MERGE_COMPLETE\n\nVerified source pack13SHA entries, imported10tasks with20implementation fields, commonrules/dependencies/acceptance/execution/resume files created; sourcepack/27historicalstates preserved. Current tasks allNOT_STARTED, nextT034 actualarchitecture/contracts; no implementation claimed. Git metadata absent. Canonical architecture audited: SocialAPI auth/content/schema0004/durableworker/review/appeal, AIdefaultV1.1/.41/v5, Social/AdminReact, source/dataset/training/registry tooling. New user authorizes safe local tasks incl gated T041CPU smoke; no r07/paid/private/default/deploy. Evidence reports/task_rollout_20261104/.\n')
    print(json.dumps({'tasks_imported':10,'source_files_verified':len(manifest),'historical_states_preserved':len(historical),'next':'T034'}))
