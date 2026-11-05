from pathlib import Path
import json,csv,collections
R=Path.cwd();out=R/'docs/ai-update/final-report';out.mkdir(parents=True,exist_ok=True)
m=json.loads((R/'datasets/synthetic_conversations/genz_v2/dataset_manifest.json').read_text(encoding='utf-8'))
q=json.loads((R/'datasets/synthetic_conversations/genz_v2/batches/quality_latest.json').read_text(encoding='utf-8'))
e=json.loads((R/'reports/ai_update/T030/genz500/metrics.json').read_text(encoding='utf-8'))
p=next((R/'tasks/moderation-ai').glob('T033-*.md'));s=p.read_text(encoding='utf-8').replace('- **Status:** TODO','- **Status:** IN_PROGRESS',1);p.write_text(s,encoding='utf-8')
(out/'README.md').write_text('''# ShieldVI — Evidence handoff, 03/11/2026

[Technical report](TECHNICAL_REPORT.md) · [Error analysis](ERROR_ANALYSIS.md) · [Reproduction/demo](REPRODUCTION.md) · [Artifact inventory](ARTIFACTS.json).

REAL0/200. Synthetic500/500 (200 imported,300 newly authored),5115 AI labels/human0. Eleven successful batch manifests. [Dataset](../../../datasets/synthetic_conversations/genz_v2/README.md) contains annotated JSONs, API-clean JSONs, CSVs, JSONLs and provenance. Technical validation passes; semantic novelty/naturalness are not established.

Candidate NOT_TRAINED:11340 rows prepared; local CUDA and exact GPU/cost receipt missing. V1/threshold0.41/defaultV1.1/test/DB remain unchanged. Development-only V1 Macro-F1=0.739974 on617 AI references; Hybrid target coverage31.43%, repeated recall0/7. No improvement or real-world performance claim.

T028,T029,T030,T031 remain BLOCKED for their complete acceptance; T032 verification and this evidence-only T033 handoff are complete. Missing experiments and unresolved errors are retained here. This handoff does not certify a new model release.
''',encoding='utf-8')
(out/'TECHNICAL_REPORT.md').write_text('''# ShieldVI technical report — current evidence

## 1. Problem

ShieldVI assists Vietnamese social moderation while keeping model prediction, contextual signals and human visibility decisions separate. The poster example motivated false-positive/false-negative investigation; it does not establish performance. This session generated research augmentation and measured remaining failures without changing baseline behavior.

## 2. System architecture

```mermaid
flowchart LR
 U[Social Web] --> S[Social API]
 S --> DB[(Social SQLite)]
 S --> J[Durable moderation jobs]
 J --> W[Worker: authenticated HTTP]
 W --> AI[Moderation AI: contract 1.0]
 AI --> V[ViSoBERT raw score, threshold 0.41]
 AI --> L[Lexicon and contextual evidence]
 W --> DB
 M[Moderation Web: admin review and appeal] --> S
 D[AI Dashboard] --> V2[Moderation AI /api/v2/analyze]
 V2 --> V
 V2 --> L
```

## 3. Repository and modules

Canonical root is ShieldVI_V3_Hybrid_Review. `services/moderation-ai/app` is the implementation; root `app` is an import bridge. Social API owns its DB/jobs/audit; AI never writes Social DB. This session added GenZ schema/compiler validation, versioned preparation, a protocol-specific research gate, a frozen development evaluator, isolated registry and E2E wrapper. No existing Social task status or production model selector changed. Previous document/AI-update directories remain backups.

## 4. AI API

`GET /health`, legacy `POST /api/analyze`, versioned `POST /api/v2/analyze`, authenticated `POST /api/v1/moderate/comment`, summary/review APIs remain available. Internal Social contract1.0 is advisory. V2 carries context, target/repeated evidence, analysis_version2.0 and policy_executed=false. Legacy recipient fields retain their old meaning. Real V1 smoke showed legacy/v2 raw-score identity and isolated503→200 recovery.

## 5. Historical datasets

This run uses6942 retained ViCTSD training rows and the unchanged historical validation split for proposed training selection. Test text is read only for exclusion, not labels, optimization or scoring. ViHOS is not loaded, relabeled or merged into the run; label definitions must be reconciled before any future integration. Old30-thread sources remain NOT_FOUND in the existing audit; they were not reconstructed. Prior100-thread training and150-comment regression fixtures remain separate evidence, not fresh test data.

## 6. Dataset A: REAL / T028

Actual0 valid threads/200,0comments,0human labels. Collector was tried within the bounded budget and exited2 before content requests because no genuine Wikimedia operator contact was supplied. Metadata source eligibility is not conversation collection or thread-level rights clearance. No contact/source/timestamp/license was invented. Genuine source authorization, anonymization, real labeling and evaluation lock remain missing. T028 stays BLOCKED.

## 7. Dataset B: synthetic

500threads/5115comments; 200 legacy threads/2048comments reused with unchanged text and lineage SHA,300new threads/3067comments authored directly by Codex. All timestamps/people are fictional. Output is `datasets/synthetic_conversations/genz_v2`, not the real directory or original200 snapshot. Eleven successful batch manifests:4 imported50-blocks, pilot20, next30, then five50-blocks.

15 broad domains with aliases cover game,fandom,social video,study,shopping,friendship,beauty,film/music,technology,sports,fanart/cosplay,travel,food,life,hobbies. Speaker counts3–6; comments10–18 observed (within requested10–30). 453/500 threads have10 comments; short threads dominate.

## 8. Generation method

Six explicitly authored catalogues contain300 new microplots and utterances. Python compiles the authored text; it does not create language by substitutions, model predictions or templates. It generates deterministic IDs/timestamps, performs schema/category adaptation and exports. No external LLM API or dataset download was used. Header plans name setting, voices, primary A–T scenario, semantic family and ending. Corpus checks run at every successful checkpoint. Checkpoint450 first rejected one duplicate sentence; the unpublished new sentence was rewritten and checked again, without relaxing the validator or altering earlier threads.

## 9. Labels and uncertainty

CLEAN4667,TOXIC369,UNCERTAIN79. All5115 are AI references, not human gold; new human confirmations=0. Fields retain source=synthetic, category, target/evidence, profanity/direct/repeated/apology/quote flags, reason and needs_human_review.102 comments carry uncertainty/review flags. Binary training excludes UNCERTAIN and flagged rows. Mixed apology+insult remains an attack; clean apologies, quotations, intervention and self-defense are not made toxic from keywords alone. Repeated annotations require prior same-actor/same-target attacks and distinct timestamps.

## 10. Quality and provenance

Technical checks PASS: timezone/increasing timestamps, IDs/users/parents/cycles, JSON schema, 3–6speakers/10–30comments, evidence consistency, exact comments, near comments, raw/delexicalized near threads, role-structure frequency and detailed-family split. Exact/near duplicates detected after corrections=0 at documented thresholds.396 distinct role sequences, maximum frequency12. Broad A–T patterns may still recur across splits: detailed family IDs plus character similarity cannot prove semantic separation or human-like variety. No independent naturalness review or agreement score exists. CLEAN dominates91.24%; this is not balanced training data.

## 11. ViSoBERT baseline

Original V1 is loaded from the existing local checkpoint, threshold0.41. The configured approved runtime default remains V1.1; the earlier synthetic experiment V2 is not the newly proposed candidate.31 protected hashes and original200 thread+2CSV checksums were verified unchanged. Original weights, tokenizers, thresholds, historical held-outs and root review SQLite were not rewritten.

## 12. Candidate fine-tune

PREPARED_NOT_TRAINED:11340 rows=6942ViCTSD+4398eligible synthetic,38.783%synthetic.440 train threads;60 newly authored development threads/620comments kept separate by detailed family. Preparation excludes exact/character5 near matches against validation,test text and development; observed exclusions0. Max fraction0.40 is a proposal, not an approved optimum. Proposed max3epochs,batch8×accumulation2,LR2e-5,maxlen128,seed20261103,patience1,3600seconds on approved ColabGPU. Local torch is CPU-only; matching GPU/cost receipt missing. Optimizer steps0; no new candidate/validation gain/reload result. Real gate remains unchanged for real protocols; G2-S recomputes synthetic eligibility instead of flipping a REAL manifest flag.

## 13. Hybrid context and lexicon

The current Hybrid annotates separate signals; it deliberately does not rewrite raw V1 toxicity. CLEAN review-flag rate is1/582 on this challenge; a review flag can be appropriate on a quotation, so this is not classifier FPR. Profanity detection2positive examples is too small and lexically coupled to AI flags to support generalization. No tuning followed evaluation.

## 14. Target detection

On35 AI-reference directed attacks, Hybrid emitted11targets, all11matched;24abstentions. Emission precision1.0 at coverage31.43%, not evidence of reliable full coverage. Parent/mentions can ground a candidate; they cannot alone prove attack intent. Legacy recipient IDs are not directly comparable target labels.

## 15. Repeated harassment

Seven reference actor-target events. Current legacy-API diagnostic:2TP,2FP,5FN (P=.50,R=.2857). HybridV2:0TP,0FP,7FN (recall0,precision undefined). No Hybrid evidence emitted; evidence correctness is undefined. This is a loss of recall on this synthetic challenge, not an improvement. No deployment/rule/model change was made in response.

## 16. Experimental results and ablations

V1 and Hybrid raw predictions are identical on617known labels;3UNCERTAIN excluded. Confusion rows[clean,toxic],columns[clean,toxic]:[[559,23],[15,20]]. MacroF1=.739974,accuracy=.938412; toxicP=.465116,R=.571429,F1=.512821; cleanP=.973868,R=.960481,F1=.967128. Paired classifier617ties,0wins/0losses by design. Frozen IDs/model/code hashes precede inference. Full B1/B2 and exact pre-update V3 comparison NOT_RUN because the original lexical/context snapshot is unavailable; the current legacy endpoint is explicitly a diagnostic. Candidate/B4 unavailable. No original test scoring or real blind evaluation. T030 full acceptance stays BLOCKED.

## 17. Error analysis and system tests

[Error analysis](ERROR_ANALYSIS.md) lists all error artifacts and deterministic examples. Fullstack browser E2E uses explicit synthetic AI scores and a disposable SQLite: registration,post/comment,offline/retry,manual override,appeal,recovery PASS;5 server logs without private test markers,0direct browser-to-AI requests. Separate real V1 API/registry fallback smoke PASS. Social177tests PASS; threefrontend builds PASS. Root final test count and exact evidence are in ARTIFACTS/verification. Fixtures are never represented as real model inference.

## 18. Limitations and release decision

REALgold0,human labels0,solo-independent agreement unavailable,synthetic label errors possible,short and explicit discourse overrepresented,semantic templates can recur,domain shift unmeasured. The model still mistakes defense/intervention and misses indirect attacks/threats. Candidate not trained. Do not promote V1/V2/localregistry or enable HIGH auto-hide from this run. T031 local tools are tested but activation/candidate comparison remains BLOCKED. T032 independently verifies the existing integration; this T033 deliverable is a bounded evidence handoff, not certification that all upstream tasks succeeded.

## 19. Future work

Provide legitimate REAL source/operator contact and rights; finish real anonymization/review/eval lock. Approve exact GPU/config/cost if candidate training is wanted. Preserve the frozen challenge: use separate development data to revise general context/target/repeated behavior, not lookup IDs or alter these labels. Recover verifiable pre-update snapshots for full ablation. Validate any candidate on historical validation, then immutable test and independent real data under the declared protocol; record regressions as well as gains before considering activation. No production deployment or live DB migration is authorized by this report.
''',encoding='utf-8')
rows=list(csv.DictReader((R/'reports/ai_update/T030/genz500/paired_predictions.csv').open(encoding='utf-8-sig')))
fp=[r for r in rows if r['ai_reference']=='CLEAN' and r['raw_toxic']=='True'];fn=[r for r in rows if r['ai_reference']=='TOXIC' and r['raw_toxic']=='False']
lines=['# Error analysis — synthetic development, not real gold','', 'Frozen60threads/620comments. All reference labels are AI-authored. No examples, labels, rules, model or threshold were changed to improve these results. Terminology in output keys was clarified from gold to reference after evaluation; numeric values stayed identical.','', '## Full counts','', 'Raw23FP: '+str(dict(collections.Counter(r['semantic_role'] for r in fp))), '','Raw15FN: '+str(dict(collections.Counter(r['semantic_role'] for r in fn))), '', 'Hybrid target11correct emissions/35attacks;24abstentions. Context attack candidate13TP/2FP/22FN (see metrics); target grounding must be evaluated separately from toxicity. Repeated event recall fell from legacy diagnostic2/7 to Hybrid0/7, while false events fell2→0. Precision for zero emitted events is undefined. This does not meet an improvement claim.', '', '## Deterministic illustrations','', 'First3FP and first3FN in frozen ID order are illustrations; every error remains in the full artifacts.','']
for kind,group in [('FP',fp),('FN',fn)]:
 for r in group[:3]:lines.append(f"- {kind} {r['comment_id']} ({r['semantic_role']}), score={float(r['raw_score']):.4f}: {r['text']}")
lines+=['','## Reproduction and limits','', '[All paired predictions](../../../reports/ai_update/T030/genz500/paired_predictions.csv), [all hybrid outputs](../../../reports/ai_update/T030/genz500/hybrid_outputs.jsonl), [error union](../../../reports/ai_update/T030/genz500/errors.json), [metrics](../../../reports/ai_update/T030/genz500/metrics.json), [per-scenario raw counts](../../../reports/ai_update/T030/genz500/paired_by_scenario.json). The error union includes target/context errors beyond raw FP/FN; it must not be counted as classifier errors alone.','', 'The high raw accuracy mainly reflects CLEAN prevalence. A precision1.0target value over only11 emitted predictions coexists with low coverage; no repeated evidence means no supported correctness estimate. Missing attacks can arise from context detection, target grounding or the conservative raw-score qualification. These observations are hypotheses for separate future development, not proof that fine-tuning fixes them.']
(out/'ERROR_ANALYSIS.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
# Demonstrations use five distinct newly authored conversations and the API-clean export.
threads=[json.loads(p.read_text(encoding='utf-8')) for p in sorted((R/'datasets/synthetic_conversations/genz_v2/threads').glob('*.json')) if int(p.stem[-4:])>200]
chosen=[]
for tag,goal in [('E','repeated attack with earlier actor/target evidence'),('I','attacker apology after earlier attack'),('K','quotation must not become a new attack solely from words'),('C','profanity as non-directed exclamation'),('L','indirect non-profane attack')]:
 t=next(t for t in threads if tag in t['scenario_tags'] and t['thread_id'] not in [x[0] for x in chosen]);chosen.append((t['thread_id'],goal))
repro='''# Reproduction and safe local demo

Run PowerShell at repository root. Use existing virtualenvs; no package/model/data download is needed for verified commands. All commands below are local. They do not start GPU training.

## Dataset and preparation

```powershell
.\\.venv\\Scripts\\python.exe -X utf8 scripts/generate_genz_dataset.py --through 500
.\\.venv\\Scripts\\python.exe -X utf8 scripts/prepare_t029_training.py --config configs/t029_genz500_candidate.json --output reports/ai_update/T029/genz500_prepared --base-model C:/Users/admin/Downloads/visobert_toxic_final
.\\.venv\\Scripts\\python.exe -X utf8 scripts/train_t029_candidate.py --config configs/t029_genz500_candidate.json --prepared reports/ai_update/T029/genz500_prepared --base-model C:/Users/admin/Downloads/visobert_toxic_final --report reports/ai_update/T029/genz500_preflight.json
```

Last command is preflight only and returns BLOCKED (CUDA/G3). Do not add `--run` or fake a receipt. The existing Colab notebook is unexecuted and was prepared for older200 config; explicitly review/change its config/prepared paths before proposing the new500 run. G2-S permits research while REAL remains blocked, not an external-cost approval.

## Tests

```powershell
.\\.venv\\Scripts\\python.exe -m pytest tests -q -p no:cacheprovider --basetemp reports/ai_update/test_tmp/next_root_run
Push-Location services/social-api
$env:PYTHONPATH='src'
.\\.venv\\Scripts\\python.exe -m pytest tests -q -p no:cacheprovider --basetemp ../../reports/ai_update/test_tmp/next_social_run
Pop-Location
$env:PYTHONPATH=(Join-Path (Get-Location) 'services/social-api/src')
.\\services\\social-api\\.venv\\Scripts\\python.exe -X utf8 scripts/run_ai_update_e2e.py
```

Use a fresh basetemp for each rerun. E2E automatically creates isolated SQLite/testaccounts and stops only owned processes; no live database is reset. Its AI scores are fixtures. Do not add fixture users to your existing DB. Frontend builds: `npm.cmd run build -- --outDir <new-absolute-report-directory>` from each app, including moderation-web/legacy-v3. Outputs in this session are under reports/ai_update/autonomous_20261103/build_*.

## Real model experiment

```powershell
.\\.venv\\Scripts\\python.exe -X utf8 scripts/evaluate_genz_development.py --base-model C:/Users/admin/Downloads/visobert_toxic_final --output reports/ai_update/T030/new_untuned_rerun
.\\.venv\\Scripts\\python.exe -X utf8 reports/ai_update/autonomous_20261103/registry_smoke.py
```

Evaluation refuses overwriting completed results, checks frozen data hashes and loads V1 offline. Reruns do not turn synthetic development into independent validation. Registry smoke deliberately faults the primary loader, actually loads V1 on fallback and compares V1 with itself to test mechanics; there is no candidate accuracy comparison.

## Five AI demos

In a separate PowerShell window, set MODEL_PATH to the desired existing local checkpoint for that process. To reproduce this report use original V1; the normal approved default is V1.1. Keep STORE_SUMMARIES=0 for this demonstration.

```powershell
$env:MODEL_PATH='C:/Users/admin/Downloads/visobert_toxic_final'
$env:STORE_SUMMARIES='0'
$env:HF_HUB_OFFLINE='1'
.\\.venv\\Scripts\\python.exe -m uvicorn app.main:app --app-dir services/moderation-ai --host 127.0.0.1 --port 8020 --no-proxy-headers
```

Open http://127.0.0.1:8020/docs and use POST/api/v2/analyze. If Dashboard is served, open /dashboard/ and choose an API-clean JSON from dashboard_threads; this is the AI Dashboard, not the optional labeling reviewer on8011 (which still shows the original200). Annotated JSON is for reading and is not the API upload shape. On the Dashboard verify the requested V2 endpoint; Swagger V2 is the authoritative signal view if a legacy UI does not render all V2 fields. Never expect keyword presence to force a TOXIC result.

'''
repro+='| JSON file | What to inspect |\n|---|---|\n'
for tid,goal in chosen:repro+=f'| [dashboard_threads/{tid}.json](../../../datasets/synthetic_conversations/genz_v2/dashboard_threads/{tid}.json) | {goal} |\n'
repro+='''
Record raw0.41prediction separately from lexical/context/target/repeated signals. Missing targets/repeated warnings are observable limitations, not a reason to alter the example. Synthetic AI labels are references; no human gold claim. The automatic E2E separately demonstrates admin review/appeal/retry on fresh synthetic accounts, without making the AI responsible for visibility or enabling HIGH auto-hide.
'''
(out/'REPRODUCTION.md').write_text(repro,encoding='utf-8')
print('Five report/demo documents prepared; artifact inventory and validation follow')
