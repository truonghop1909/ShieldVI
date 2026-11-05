# Independent readiness — safe development and real-data blockers

## Current authority and task scopes

Latest PartsA/B/C and follow-up restore real200/human-review criteria for T028. Historical27task DONE records, including the earlier synthetic-only T028 and bounded CPU experiments, are preserved; they do not fulfill the newly requested real acceptance. Current criteria are machine-readable in [CURRENT_AI_SCOPE](../../../tasks/CURRENT_AI_SCOPE.json). No new training, source scraping, model promotion or production deployment was performed.

| Task | Current requested scope | Status |
|---|---|---|
| T022 | Indirect attack/context development on frozen synthetic references | DONE |
| T024 | Target inference from actual attack clauses and available participant metadata | DONE |
| T025 | Repeated-evidence regression; missing targets still abstain, no promised perfect recall | DONE |
| T027 | Source/inventory audit, paused collector guard, anonymized quarantine and human review preparation | DONE |
| T028 | Independent real200 cohort | BLOCKED |
| T029 | New training | BLOCKED |
| T030 | Synthetic development evaluation tooling and before/after | DONE |
| T031 | Actual local registry/shadow/fallback/rollback mechanics using existing candidate | DONE |
| T032 | 574root/177Social regressions and isolated5process integration E2E | DONE |
| T033 | Provisional technical report with missing evidence explicit | DONE |

Eight safe task scopes completed; T028real and T029training remain BLOCKED. T029preparation is complete separately. T030real-world metrics and T033real-world conclusions remain unavailable. Local T031 mechanics use the already-existing r05 artifact, not a newly trained candidate; that model remains rejected for promotion.

## Part A — paired synthetic development

Rules now recognize bounded indirect capability/body/voice disparagement, while checking negation, quotations, reporting and fresh attacks after apology. Available participant IDs help recognize a named addressee only when present in an attack clause. Target-v4 excludes background names from the target set and retains abstention for root attacks without addressee metadata. No target is invented from later participants or every reply.

One shipping reference gains a supported two-turn actor→target chain after its earlier personal insult is recognized; GAME/camping exact4attack chains and recovery/apology exclusions remain intact. Repeated-v4 stays advisory and policy is never executed.

Inputs:890already-viewed synthetic/development comments,886known binary references;4UNCERTAIN references excluded and disclosed. Aggregate scores reuse the identical actual original-V1 CPU cache. New code was selected on development, not a blind benchmark. No real-world metric or human-gold claim.

| Metric | Before | After |
|---|---:|---:|
| FP / FN | 20 / 9 | 18 / 6 |
| Macro-F1 | 0.889700 | 0.909296 |
| Toxic precision / recall | 0.7403 / 0.8636 | 0.7692 / 0.9091 |
| Grounded targets correct / reference attacks | 30 / 54 | 34 / 54 |
| Target precision / recall | 1.0000 / 0.5556 | 1.0000 / 0.6296 |
| Repeated TP / FP / FN | 2 / 0 / 8 | 3 / 0 / 7 |
| Repeated F1 | 0.333333 | 0.461538 |

Zero new label regressions. Remaining18FP/6FN,20target abstentions on reference attacks and7missed repeated events are preserved in the output; no expected labels were changed. Grounding references cover797known comments, omitting three legacy threads without target truth. Abstention counts as a miss in class F1, not silently dropped. Distinct event timestamps are normalized to UTC.

[Full before/after, groups and remaining errors](../../../reports/ai_update/independent_readiness_20261103/development_final/metrics.json) · [Unit regression](../../../tests/test_indirect_scope_regression.py).

## Part B — real inventory, rights and collection

Old30threads/313comments: **NOT_FOUND** in the current repository inventory across datasets/, fixtures/if present, tests/, docs/ and related manifests. Documentary mentions of a Wikipedia pilot are not corpus evidence. Known100/200/500synthetic sets and5regression fixtures are not reclassified as real. Inventory1478structured files is retained; relevant collection/manifest structures were checked, flat classification files were not combined into invented conversations.

Actual admitted real threads: **0/200**, comments0, manual human labels0. Six source candidates were researched using primary metadata/docs; none was admitted. No corpus download or live collector request was made. Wikimedia is explicitly PAUSED by user, enforced before network-client creation even if a stale contact variable exists. No fake email/account/URL or browser User-Agent was used; no further contact/path question is required this session.

| Source | Observation and current disposition |
|---|---|
| Wikimedia | Existing CC-BY-SA metadata does not override the user pause; collector must recheck rights receipt before any future content acquisition. [API etiquette](https://www.mediawiki.org/wiki/API:Etiquette), [official User-Agent policy](https://foundation.wikimedia.org/wiki/Policy:Wikimedia_Foundation_User-Agent_Policy/en). |
| ViHOS | [Official repository](https://github.com/phusroyal/ViHOS) and [MIT repository license](https://raw.githubusercontent.com/phusroyal/ViHOS/master/LICENSE) inspected. Flat span/comment data is not a source-verified multi-party cohort; repository software licensing is not assumed to resolve every underlying comment right. |
| ViHSD | [Official repository](https://github.com/sonlam1102/vihsd) describes comment classification; no clear dataset-use grant was located in inspected pages. Hold for rights and thread/provenance requirements. |
| ViCTSD | [Official repository](https://github.com/tarudesu/ViCTSD) plus local manifest: existing user-copy license not reverified; already a supervised classification source, not a new independent thread cohort. |
| ViLexNorm | [Official repository](https://github.com/ngxtnhi/ViLexNorm), local README/license hashes and CC-BY-NC-SA metadata. Normalization pairs already used in development do not provide the requested source thread graph. |
| mDIA | [Original repository](https://github.com/DoctorDream/mDIA) and [SEACrowd card](https://huggingface.co/datasets/SEACrowd/mdia/blob/main/README.md). Wrapper CC-BY declaration/paper citation do not establish an inspected upstream grant plus complete10–30turn provenance; parent-response pairs were not stitched into invented threads. |

These are acquisition eligibility findings, not a legal assurance. [Inventory/audit](../../../reports/ai_update/independent_readiness_20261103/old_30_audit.json) · [Source research metadata](../../../reports/ai_update/independent_readiness_20261103/source_candidates.json).

### Future human intake and review

The blind UI is running at http://127.0.0.1:8010/. The new JSON intake stores an anonymized, unverified local quarantine with source URL/license claim/evidence URL, source timestamp/null and parent graph. It preserves missing metadata rather than inventing it, rejects preloaded labels, and never counts a staged item as real/evaluation/training eligible. A verified source adapter/rights receipt, privacy and leakage checks are still needed before admission; a user-uploaded license claim is not verification.

Reviewer entry and JSON input were checked in Chrome; no labels/data were submitted to the actual dataset. Existing labeling supports the same human across Round1/Round2 with revision history; stale Round2 returns to the queue after Round1 changes. This is not inter-annotator agreement. No second reviewer is simulated. The evaluation lock remains unavailable for the empty cohort.

Leakage exclusion now binds GenZ500train/development and12context fixtures as well as prior references/ViCTSD; source hashes and whole-thread near checks remain mandatory. Metadata changed, frozen text/labels did not. Exact comment hashes use>=80characters and do not certify absence of all paraphrases. [Manual intake template](../../../templates/T028_MANUAL_INTAKE.example.json) · [Real-data instructions](../../../datasets/real_conversations/README.md).

## Part C — preparation and safe integration

- T029: new unapproved real-protocol config and11340preparedrows exist. Actual preflight blocks on current no-training scope, missing real verified cohort, matching approval and CUDA. Gate also requires real acceptance with>=200threads; preparation did not create a checkpoint or optimizer.
- T030: reproducible synthetic metric CLI, frozen before state, per-group FP/FN/MacroF1 and target/repeated support. No historical classification test or real-cohort metric was scored.
- T031: actual existingr05 shadow load, implicit-selection refusal, deliberate candidate-loader fault with actual V1fallback, isolated ASGI200→503→200rollback; default path unchanged. Scores are mechanics probes, not a performance claim.
- T032:574root and177Social testsPASS; existing5process E2E/browserPASS with fixture AI and disposable SQLite/accounts. Fixture integration is explicitly not real model accuracy. Owned test processes exited; five logs had no sensitive markers. Separate live V1.1/r05 smoke on5syntheticthreads/90comments each confirmed raw/legacy invariants and indirect targets/shipping/GAME/camping chains after local code reload. No production model switch.
- T033: this provisional report and current scope ledger preserve missing evidence rather than marking real acceptance DONE.

## Validation, blockers and handoff

Final:574rootPASS/177SocialPASS/E2EbrowserPASS/reviewUIbrowserPASS/registryPASS/live-smokePASS. Initial new-regression red failures were retained; one named-target test required the participant metadata supplied in the real pipeline, without changing its expected target. Browser smoke initially lacked the bundled browser and was rerun with installed Chrome, without download. Registry warning on PowerShell stderr was resolved by recording the actual Python exit0; warning logs retained.

31protected originals, V1/defaultV1.1/r03/r04/r05 checkpoints, frozen200/500synthetic data/labels/splits, context/user references, original validation/test and live SQLite unchanged. All27historical task status lines unchanged. No training, paid/external upload, destructive migration, push, production deployment or auto-hide.

Next: when actual permitted source material is available, use the local intake and verification workflow, then personally perform Round1 and Round2. T028real remains BLOCKED until the cohort/rights/human-review/lock criteria pass; T029new training additionally needs explicit approval. Do not ask again for the declined Wikimedia contact or missing old path in this session.

[Current progress](../../../tasks/AUTO_PROGRESS.md) · [Current scope](../../../tasks/CURRENT_AI_SCOPE.json) · [Evidence](../../../reports/ai_update/independent_readiness_20261103/progress.json).
