> CURRENT verified follow-up: T028/T029 formal BLOCKED; T030–T033 PARTIAL. Safe synthetic/local evidence verified, no real/human-gold acceptance or production activation. Historical DONE below is preserved. See [v5 report](../../docs/ai-update/final-report/REPEATED_RECOVERY_V5.md) and ../CURRENT_AI_SCOPE.json.

# T033 — Technical report / thesis handoff

- **Status:** DONE
- **Priority:** P2
- **Dependencies:** T030,T032
- **Owner:** Codex đề xuất code, người dùng duyệt
- **Scope:** cập nhật AI ShieldVI, không phải tự động bật xử phạt

## Mục tiêu

Đóng gói chứng cứ học thuật và hướng dẫn demo ShieldVI Social + AI Update.

## Các bước triển khai

1. Tổng hợp architecture diagram, bảng modules thay đổi, legacy vs current và contract versions.
2. Báo thí nghiệm B0/B3/(B4 nếu có), metrics với provenance, confusion matrices, failure analysis và rollback.
3. Demo 5 synthetic threads: nhận xúc phạm, xin lỗi, lexicon, target/repeated, admin review; có câu disclaimer về synthetic.
4. Ghi giới hạn solo annotation, ViCTSD vs ViHOS, domain shift, không overclaim hiệu quả, HIGH auto-hold off trừ khi đã duyệt.
5. Đưa quy trình chạy test/Colab/VS Code và danh sách artifacts có hash; không đóng gói checkpoint lớn nếu không yêu cầu.
6. Cập nhật `TASK_ORDER_AI.md` và kế hoạch task tiếp theo theo dependencies.

## Phạm vi file

- Codex **phải xác minh** service thực tế ở `app/` legacy hoặc `services/moderation-ai/`; chỉ tạo/sửa file hợp lý trong đó.
- Test và tài liệu trong `tests/`, `docs/ai-update/`, `datasets/` hoặc service-scoped equivalents.
- Không sửa Social DB, baseline checkpoint, train/test split hay nội dung fixture trừ khi task nêu rõ và người dùng duyệt.

## Kiểm thử / bằng chứng

Tài liệu có ví dụ reproduction, đường dẫn artifacts tồn tại, test evidence đủ; không tự tuyên bố điểm tốt nghiệp hoặc real-world performance.

## Acceptance criteria (Definition of Done)

Có bộ technical report kiểm chứng được, checklist demo, rủi ro còn lại và limitations trung thực.

## Chặn rủi ro / stop conditions

- Nếu thiếu dữ liệu, license, nhãn người kiểm duyệt, checkpoint, GPU hoặc quyền phù hợp: ghi `BLOCKED` + lý do, không giả lập thành PASS.
- Nếu xuất hiện breaking change hoặc metric xấu đi rõ ràng: báo tác động, rollback và xin duyệt.
- Task chỉ `DONE` sau khi có evidence đúng; công việc chưa chạy cần ghi `CHƯA CHẠY`.

## Nhật ký thực hiện (Codex cập nhật)

- Ngày/commit:
- Các file đã sửa:
- Test/command thực tế:
- Kết quả PASS/FAIL/CHƯA CHẠY:
- Metric/số case thay đổi (nếu áp dụng):
- Blocker / rủi ro:
- Task đề xuất tiếp theo:

### Evidence-only handoff completed03/11/2026

DONE for the current user-authorized report of available evidence, not a declaration that REAL/train/release succeeded. `docs/ai-update/final-report/` includes19-part technical report, all data/provenance/AI-label limitations, architecture, true metrics/failures, error analysis, five synthetic demos, commands and hashed inventory. Local links and dataset/batch/hash/lock/notebook integrity verified. T030 research-evaluation and T032 verification complete independently; T028REAL, T029training and T031candidate activation remain BLOCKED.

Final root358PASS/1warning; Social177PASS/1warning; browser1PASS; webbuilds3PASS. RealV1 challenge and isolated registry/API fallback smokePASS; E2E fixture scores are explicitly distinguished. 31protected artifacts plus200legacythreads/2CSV unchanged, threshold0.41 unchanged, notebook unexecuted, candidateNOT_TRAINED/optimizer0. No production/default/DB/reset/push/deploy action. See reports/ai_update/autonomous_20261103/session_verification.json.

### Current CPU candidate completion supplement

Actual head-only CPUcandidate trained534steps, encoderfrozen. T030candidate comparison now has validation/final-test/synthetic reports; T031localshadow/fallback/rollbackcomplete and promotionREJECTED. Current candidate legacy/V2/internalSocialcontractAPI200 verified in isolation, no production/default/DB change; no new full-stack-live-candidate deployment is claimed.434rootPASS. Earlier evidence remains historical; current report docs/ai-update/final-report/CPU_HEAD_COMPLETION.md.


## Latest independent-readiness criteria

Historical status/evidence above preserved. Current scoped status: **DONE** — Provisional technical report with missing evidence explicit. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/INDEPENDENT_READINESS.md. New criteria never turn missing real/human evidence into DONE. Evidence:574root/177Social/E2E/UI/registry/live smoke PASS; valid real0, no new training.


## Current verified follow-up — repeated/context/target v5

T028 BLOCKED(real0/200,humanlabels0); T029 formalBLOCKED(r06 experimental already trained, no r07); T030/T031/T032/T033 PARTIAL (safe synthetic/local work verified; missing independent acceptance, no production authorization). Historical DONE preserved; current scope tasks/CURRENT_AI_SCOPE.json.

Five event regression red5FAIL before fix; old challenge repeated0/5→5/5, evidence10/10correct. Fresh post-freeze12threads/74comments:2/6→4/6, precision1/recall.6667, evidence8/8correct;2misses retained, no post-score rule changes. Canonical500/5115 unchanged. Broad890replay known886 FP18→18/FN6→4; repeated2/10→8/10,FP0,evidence20/20; no new label errors. Old prose34target/3events superseded by archived/recomputed33/54and2/10; DANCE lacks grounding refs and cannot count as TP.

Tests610rootPASS/177SocialPASS/browserfiveprocessE2EPASS; actual r06 shadow/fallbackV1/ASGI200→503→200PASS. Browser uses fixtureAI/disposableSQLite, actual models tested separately. Model/default/V1/0.41/test/SQLite/reference labels unchanged; no training/deploy. Runtime context_signals.py/target_signals.py/signal_engine.py+contract defaults; two new test files, reusable evaluate_repeated_recovery.py,12new fixture JSONs/manifest, isolated registry, real-cohort development exclusions, report/progress/task notes. Full file inventory/hashes in reports/ai_update/repeated_recovery_20261103/ARTIFACTS.json.

Report docs/ai-update/final-report/REPEATED_RECOVERY_V5.md; evidence/reproduction reports/ai_update/repeated_recovery_20261103/README.md. Next: real permitted source/human rounds for acceptance; new predeclared holdout before further rule tuning. Do not train r07, recreate500, change default or call synthetic human gold.


## Stabilization & Evaluation Readiness — DONE safe scope

Two residual repeated events audited: unseen cục_chì metaphor;66minute gap beyond30minute reciprocal window. No technical bug proven; no rule/label changes or re-inference to obtain6/6. Preserve old5/5/fresh4/6(P1,R.667,evidence8/8).

READINESS_LOCK_T028_v2.json seals1311files(model/rule versions, datasets/manifests/reference labels, raw/ablation/confusions/FPFN/target/repeated and integration evidence). Read-only verificationPASS; no resealing. Latest620rootPASS/0FAIL/1warning,48review protocolPASS included; Chrome empty-corpus UIPASS/0submissions/0AI. Prior177Social/browserE2E/actual shadow+rollback preserved and hash-verified, not rerun. Protected259artifacts/V1/default/0.41/test/SQLite unchanged.

T028/T029formalBLOCKED; T030/T031/T032/T033PARTIAL. Technical T032, frozen T030synthetic and provisional T033 handoffDONE; independent acceptance still absent. Real0/200/humanlabels0, collectorPAUSED. Manualintake/anonymization/CSRF/provenance checks and same-humanRound1/Round2 tested; manual inbox still needs verified receipt/supported adapter before source admission. StaleRound2 cannot lock after Round1 revision. Empty-source URL API500 reproduced, one-line min_length1 fix now422/no key/inbox writes; original lock preserved, tooling-v2 lock with SHA lineage. No labels requested/fabricated, no r07/train/deploy/default switch.

Report/checklist/architecture/dataset/training/comparison/error analysis/demo: docs/ai-update/final-report/FINAL_READINESS_REPORT.md. Evidence/reproduction: reports/ai_update/stabilization_20261103/README.md; lock READINESS_LOCK_T028_v2.json, latest-test/report binding READINESS_ATTESTATION.json. New code scripts/verify_ai_readiness_lock.py; scripts/real_dataset/intake.py(min_length1fix); new tests test_ai_readiness_lock.py/test_real_review_lock_readiness.py; AI/Social/frontend/model unchanged. Current authority tasks/CURRENT_AI_SCOPE.json. Next: permitted/source-verifiable real200, privacy/leakage, same-human two rounds and evaluation lock; then predeclared independent evaluation and formal sign-off. No automatic training.


## Fresh10 recovery — 04/11/2026, research only

648root tests PASS/0FAIL/1deprecation warning (28Fresh10 tests included). Imported10analysis JSONs/originalreference CSVs byte-preserved. Fresh10 development195binary: TP15→18,FP6→1,FN7→4,TN167→172,MacroF1.830105→.931861,target5→16/22,repeated2→6/7(P1/R.8571),evidence15/15correct,15/19coverage. Old890cached-V1 regression classification/target/repeated unchanged, no new errors.

Initial48comment post-freeze challenge exposed one new apology/report FP; original source/lock/outputs retained, then explicitly converted to development. Generic reporting-scope fix and v6.1 refreeze; another24comments first-scored after freeze: TP5/FP1/FN1/TN17,MacroF1.888889,target5/6,repeated1/2(P1/R.5),evidence2/2correct,2/4coverage. One metaphor FN/raw-score FP remain; no post-score tuning. All labels synthetic_reference, not human gold/independent real; no label edits.

Opt-in processor services/moderation-ai/app/experiments/fresh10_v6.py; evaluator scripts/evaluate_fresh10_recovery.py and evaluate_fresh10_challenge.py; tests/test_fresh10_recovery.py. API/Dashboard stillv5. V1/r06/default/0.41/readiness1311hashes unchanged; no training/deploy. New fixture exclusion extension prepared but NOT merged into locked runtime exclusions. T028/T029formalBLOCKED,T030–T033PARTIAL; historicalDONE preserved. Report docs/ai-update/final-report/FRESH10_RECOVERY.md, evidence reports/ai_update/fresh10_recovery_20261103/README.md, hashes ARTIFACTS.json. Continue only with separate future release/evaluation scope; no automatic activation or new training.


## NOV10 root-cause audit — 04/11/2026

Audit complete; rules/checkpoints/default unchanged. Imported10inputs/10v6.1analysis/200comments and original synthetic_reference CSVs. Exact wire replay10/10; 7attack predicate families have0matches before/after masking on all200comments, so context.attack_candidatefalse causes infer_target earlyreturn and0instances. Actual canonical ASGI r06 probe63comments PASS: contextcalled20times/thread forTest12/15/20, rawdiff0; positivecontrol repeatedPASS. Not a Dashboard-v5 assumption or global disable. Eight referencepairs10–20min have0qualifiedinstances, not time-window rejection.

NOV10 unchanged:199binary,TP7/FP3/FN15/TN174,MacroF1.694160,target0/22,repeated0/8. OldFresh10+890cachedregression unchanged.24adjudication candidates pending/no reference edits. Versioned development_exclusions.research_20261104.json registers NOV10/Fresh10/challenges;10/10NOV10 excluded via explicit overlay preflight, sealed defaultmanifest/loader unchanged.

Standardroot677PASS/0FAIL/1warning. Separate supplemental quote-scope red probes2FAIL/1PASS: new locked24comment challenge found narrative-quote attribution bug; NOT fixed or hidden. Challengev6.1:23binary TP6/FP1/FN0/TN16,Macro.946387,target5/6,repeated1/2(P1/R.5),evidence2/2correct/2of4referencecoverage. No post-inference tuning. Audit scope complete, quote fix/indirect coverage still OPEN; next revision needs red-before-fix and fresh challenge. Readiness1311SHA PASS; no train/deploy/DB/default edits. FormalT028/T029BLOCKED,T030–T033PARTIAL/historicalDONE preserved.

Report docs/ai-update/final-report/NOV10_ROOT_CAUSE_AUDIT.md; evidence/reproduction reports/ai_update/nov10_audit_20261104/README.md; labels-to-review adjudication_candidates.csv; source/hash inventory ARTIFACTS.json.


## Controlled v6.2 research — 04/11/2026, EXPERIMENTAL

Completed safe research cycle, no formal acceptance/promotion. New research_v62.py leaves sealedv6.1/default untouched. Two quote expectation RED→GREEN (same inputs/assertions; currentv6.2 replay, originalv6.1JSON/probes unchanged), outside assignment/attribution/cau noun/cau addressee/NFC spans handled; new outsidequote attacks preserved.43processor+2adjudication targetedPASS; full722rootPASS/0FAIL/1warning.24owner cases exported with full20commentcontexts and blank decisions; latest adjudication_v3/HTML+CSV, timestamped decision annotationversions, no humanreview/gold or originalreference edits.

Bounded indirect grammars with negativecontrols; weak sarcasm cues diagnostic-only pending adjudication. NOV10TP7→8,FP3→3,FN15→14,TN174→174,Macro.694160→.719137,target0→2/22,repeated0→1/8(P1/R.125),evidence2/2correct but2/21coverage/full0of8events. Fresh10/old890 no regression; all7developmentcohorts no newlabelerrors. Some viewedchallenge gains; do not call independent.

V62_LOCK before new6threads/36comment authoring/inputfreeze/inference. One actualr06CPUoffline scorecache, no post-score tuning. Challengev6.1→v6.2 Macro.731744→.911330,TP3→6,FP0→0,FN5→2,TN28→28,target1→6/8,repeated0→2/3(P1/R.667),evidence4/4correct/4of6coverage. Two unseen metaphor/exclusion misses remain unchanged.52remainingbinaryerrors/12UNCERTAIN across8cohorts saved; emittedtarget/evidenceerrors0 on groundedreferences. Newversionedexclusionoverlay verifies10NOV10+6newchallenge excluded; defaultloader unchanged.

V1/r06/default/.41/readiness1311SHA unchangedPASS; no Dashboard/default runtime/DB edits, trainingr07, deploy or promotion. T028/T029formalBLOCKED,T030–T033PARTIAL; historicalDONE preserved. Report docs/ai-update/final-report/CONTROLLED_V62_RESEARCH.md; progress/evidence/changelog/SHA/reproduction reports/ai_update/v62_research_20261104/. Next owner adjudication when convenient, future independent research revision only; no automatic activation.
