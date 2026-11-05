# ShieldVI responsive UI/UX — 05/11/2026

Status: DONE_VERIFIED for the opt-in Live/Studio responsive scope; legacy and
device coverage limits are listed below. Historical task/formal acceptance states
are unchanged.

## Scope and audit

React 18 / Vite 6, CSS without a framework, existing lucide icons, no new dependency.
Live routes use page entrypoints rather than a client routing library. Reuse existing
auth, content components, SSE + polling, API permissions, pagination and Studio APIs.

| Route / surface | Before | Implementation |
| --- | --- | --- |
| Social `/live.html`, login/feed/create/detail | Wide single column; small action targets | Mobile bottom navigation, tablet icon rail, desktop sidebar, readable center and optional wide-screen help panel |
| Comment/reply | Small actions, long metadata, parent indentation | 44px targets, wrapping metadata, bounded indentation, expandable parent context, composer kept before comments |
| Account | Username in greeting only | Read-only account summary using existing `/me`; no invented profile editing API |
| Moderator `/live.html` | Fixed-height header; overflow at 820px | Auto-height header, wrapping filters, queue cards and one-column detail on mobile, side-by-side desktop |
| Admin JSON tab | Wide result table | Same fields rendered as labeled cards on mobile; desktop table scrolls locally |
| Studio `/studio.html` → Datasets | Small controls, wide file/identifier content | Grid import form, native file picker, wrapping preview/provenance/errors and label distribution |
| Studio → Labeling | Long control panel below context | Collapsible annotation panel on mobile, sticky desktop controls, explicit selection opens panel; state retained on resize |
| Studio → Training | Raw status/report only; small controls | Touch-friendly dataset choices, config grid, honest indeterminate progress, local log scroll, SVG loss/F1 charts from supplied epoch metrics |
| Studio → Models & Evaluation | Table overflow at 320/360/375/390px | Labeled mobile cards with SHA and metrics retained; desktop table |

Frozen `/` legacy entrypoints and `legacy-v3/` are retained. Their sources are in
the readiness lock and are excluded from modifications, builds and responsive
acceptance here. No claim that these legacy screens received the new layout.

## Design and accessibility

Shared opt-in CSS tokens: ink, muted text, brand, surface, canvas, border, radius
and fluid spacing in `apps/shared/responsive.css`. Segoe UI/system fonts support
Vietnamese without font downloads. Existing light theme remains; no dark theme
existed on these entrypoints. Focus outlines, skip links, native summary/details,
labels and text statuses accompany color indicators. Native confirmation guards
comment deletion and manual hide; Escape/cancel preserves content and browser
dialog focus behavior. No modal library or custom focus trap is introduced.

Mobile first: below 640px single column/bottom navigation; 640–1023px tablet rail
and two-column forms; from 1024px desktop sidebar/detail layout; from 1440px
additional help panel and wider filtering. Extra <375px rules keep tiny screens
usable. No page-level `overflow-x:hidden` masks layout failures. Logs/previews
and desktop tables have their own scroll containers. Queue text is a four-line
preview; selecting the card always exposes full content/context/evidence.

## Baseline evidence

Complete baseline: `reports/task_rollout_20261104/demo_77a6b5d6c9fe3d7b/`.
`responsive_result.json`: 120 layout measurements, 5 overflow cases, no page JS
errors. Evaluation registry overflow at 320, 360, 375, 390px; moderator detail at
820px. Small enabled controls: social132, moderator108, dataset72, annotation60,
training77, evaluation12, moderator login24, Studio login24 across 12 viewports.
Two preliminary audit attempts retained separately: first used the wrong job
status name; second used a label selector incompatible with the existing select.
Both were test harness errors, corrected against the real DOM/API, not app logic.

Baseline and after screenshots use the same isolated synthetic controls; database
IDs/times differ. Long comments, long URLs, a four-level parent chain, two real
authenticated Social accounts and real approved default neural inference are used.
No dataset/test reference is changed and these controls are not human gold.

## Validation

Initial after run: `reports/task_rollout_20261104/demo_54b01969555b1735/`:
132 layout checks PASS, zero horizontal overflow, 9 workflow checks PASS.
Final run: `reports/task_rollout_20261104/demo_087f9ab44bf232fa/`:
144/144 layout checks PASS, zero horizontal overflow, zero enabled controls below
44px under the measured button/input/select/summary criteria, zero page JS errors.
13 workflows PASS: authenticated two-account realtime, four-level reply tags,
real AI warning, real JSON inference/result cards, isolated file upload and
annotation autosave, fixture training charts/logs, touch dataset/model choices,
configuration retention across resize, canceled hide confirmation, account,
offline/reconnect without duplication, mobile draft/scroll preservation, and
actual post creation (some assertions grouped into one workflow).

Existing browser workflows rerun against actual default AI in
`reports/task_rollout_20261104/demo_9a8b1169d4c85243/`: composer7, identity/reply4,
quick JSON5 and moderation/hide/appeal/restore/audit8 = 24 checks PASS. The old
T043 browser script now explicitly accepts and checks the new native hide
confirmation; its visibility/appeal/evidence assertions remain intact.

Both final frontend builds PASS, no new packages. Startup13 and shared transport4
tests PASS. Readiness lock verification: 1311 files PASS; model/default/.41 intact.
Logs: `reports/responsive_20261105_{social_final_build,admin_ready_build,startup,
transport,readiness,regression_01,after_final}.log`. No full Python/backend suite
is claimed for this UI-only change; the real integration workflows above ran.

Before/after examples (repository-relative links):

- [Social mobile before](../../reports/task_rollout_20261104/demo_77a6b5d6c9fe3d7b/before_social_feed_detail_390.png)
  / [after](../../reports/task_rollout_20261104/demo_087f9ab44bf232fa/after_social_feed_detail_390.png).
- [Moderator mobile before](../../reports/task_rollout_20261104/demo_77a6b5d6c9fe3d7b/before_moderator_review_320.png)
  / [after](../../reports/task_rollout_20261104/demo_087f9ab44bf232fa/after_moderator_review_320.png).
- [Evaluation mobile before](../../reports/task_rollout_20261104/demo_77a6b5d6c9fe3d7b/before_evaluation_registry_320.png)
  / [after](../../reports/task_rollout_20261104/demo_087f9ab44bf232fa/after_evaluation_registry_320.png).
- [JSON result cards](../../reports/task_rollout_20261104/demo_087f9ab44bf232fa/after_json_results_320.png),
  [annotation](../../reports/task_rollout_20261104/demo_087f9ab44bf232fa/after_annotation_390.png),
  [training UI fixture](../../reports/task_rollout_20261104/demo_087f9ab44bf232fa/after_training_progress_390.png).

Required viewports: 320×700, 375×812, 390×844, 768×1024, 1024×768,
1366×768, 1440×900, 1920×1080. Intermediate widths: 360, 600, 820, 1180px.
Screenshot coverage: 320, 390, 768, 1366 and 1920px for each audited screen.
Training progress/charts/logs use a clearly named browser-only fixture. No new
training job/worker is executed; these screenshots are UI verification, not
training evidence. Upload/annotation use a separate disposable synthetic dataset
in the owned test database, never the active demo or original datasets.

Final source/evidence SHA inventory: `reports/responsive_20261105_verified.json`.
Active user demo pointer remains `demo_85046f8406365373`, PID6456, untouched by
noninteractive checks. No API contract, backend/ML implementation, checkpoint,
dataset/reference, permission, production default or deployment change.

## Modified components and limits

Social: `live.jsx`, new `live-responsive.css` and shared `responsive.css`.
Admin: `live.jsx`, `QuickAiTest.jsx`, new `workspace-responsive.css`.
Studio: `studio.jsx`, `AnnotationStudio.jsx`, `TrainingStudio.jsx`,
`EvaluationStudio.jsx`, new `ChoiceList.jsx`, `TrainingProgress.jsx`,
`LabelDistribution.jsx`. Native checkbox lists replace Ctrl/Command multi-select
for dataset/model choices without changing request values or selection limits.
Additive browser runners, startup mode selection, report/index and progress notes
are also updated. No framework rewrite, dependency or API change.

No horizontal overflow remains in the measured populated Live/Studio states.
Limits: Chrome desktop viewport emulation, not real Android/iOS devices; virtual
keyboard/safe-area behavior still needs physical-device review. Legacy `/` pages
remain sealed and unmodified. Account is a read-only summary, not profile editing.
Native single-select menus remain OS/browser controlled. Training charts only
render reported numeric epoch metrics; without them the UI states they are
unavailable. No training/evaluation job was launched to validate these controls.
Human-gold evaluation and formal T028/T029 blockers remain outside this work.
Git diff unavailable because this workspace has no `.git` repository metadata.

## Run and inspect

From repository root in PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\demo_realtime_studio.ps1
```

Keep the launcher running. Use its authenticated Social, Moderator and Studio
windows. Existing Vite sessions can refresh to load frontend changes; do not
restart solely for CSS if the backend already supports the existing Live/Studio
APIs. A new launcher run creates a new isolated session, retaining old data/logs.

Build without overwriting sealed outputs:

```powershell
cd apps/social-web
npm.cmd run build -- --config vite.live.config.js --outDir dist-live-responsive-20261105
cd ../moderation-web
npm.cmd run build -- --config vite.live.config.js --outDir dist-live-responsive-20261105
```

Responsive browser check from repository root (local Chrome/dependencies required):

```powershell
.\services\social-api\.venv\Scripts\python.exe -X utf8 reports/task_rollout_20261104/run_browser_actual.py --responsive-check
```

The noninteractive check keeps unique evidence and stops only owned processes.
It does not overwrite `ACTIVE_DEMO.json` or start a training worker.
