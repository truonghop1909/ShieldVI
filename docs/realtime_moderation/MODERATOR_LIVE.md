# Moderator Live (T038)

Use the opt-in Social factory documented in RUN_LOCAL.md; build/serve
`apps/moderation-web/live.html` with `vite.live.config.js` and the same Social API
proxy. Existing `/` dashboard and default builds remain unchanged. Sign in with
an existing admin/moderator account. There is no new trainer role or auth bypass;
ML Studio uses admin authorization until a separate role migration is approved.

Queue tabs and pagination use the existing review API. Search, thread, risk and
time filters explicitly apply to the current page. Global authenticated fetch
SSE has a staff-only polling fallback. Stream bodies contain notification IDs and
versions, never source text, tokens or raw evidence. Detail endpoints enforce RBAC.

Existing ReviewDetail retains reason drafts during queue/evidence refresh. Its
read snapshot is deliberately stable: reload detail before a decision after a
version change; server CAS rejects stale writes. The companion analysis panel
refreshes full thread context, raw score, policy risk, reply recipient, directed
target and grounded repeated evidence separately. Comment links jump to context.
No AI output automatically hides content. Approve dismisses a warning manually;
hide/restore/appeal actions reuse existing audited review flows. Clarification is
an audited note with a decision-version increment, never a visibility change.

Evidence: T038_backend_tests_fixed.log (33 PASS), T038_browser_result.json
(8 Chrome checks, 3 independent contexts), T038_moderator.png and cleanup JSON
under reports/task_rollout_20261104/. The browser workflow uses a deterministic
raw-score fixture plus actual default-v5 rules/worker; it is not neural quality
evaluation. T036 retains a separate real approved-checkpoint CPU benchmark.

The first browser attempt failed on a Playwright label-text selector after typing
into a nested textarea. Its aria snapshot showed the draft intact. The selector
was changed to the accessible textbox role; the value assertion was retained.
The first backend invocation could not use the OS temp location; rerunning with
an explicit workspace basetemp passed. Failed logs are retained transparently.
