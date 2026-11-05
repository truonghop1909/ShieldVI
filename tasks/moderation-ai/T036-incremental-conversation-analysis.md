# T036 — Moderation AI: incremental thread analysis và repeated events

**Dự án:** ShieldVI · **Trạng thái ban đầu:** TODO / NOT STARTED (chỉ đổi theo evidence) · **Nhánh:** Realtime Moderation & Self-service ML Studio

**Mục tiêu:** Phân tích bình luận mới trong context cục bộ, xác định target và bằng chứng công kích lặp lại qua nhiều tin nhắn mà không re-run toàn bộ hội thoại.

**Phụ thuộc:** T034, T035. Các task mới là phạm vi triển khai kỹ thuật; T028–T033 không tự đổi trạng thái khi chưa đủ formal acceptance.

## Công việc triển khai
1. Audit inference API hiện tại, phân biệt comment classifier ViSoBERT và layer Context/Target/Repeated. Tạo `analyze_incremental` / adapter tương đương không phá `/api/v1/moderate/comment`, `/api/v2/analyze` hiện có.
2. Đầu vào gồm message và thread context tối thiểu cần thiết, `parent_id`, author timeline, `reply_to_user_id`, các attack instances đã xác nhận theo `(actor,target)`; context snapshot/revision có provenance.
3. Tái sử dụng score cache theo `(message_text_hash, model_sha)` khi hợp lệ; invalidate khi edit hoặc dependency đổi; chỉ tái đánh giá các affected nodes. Định nghĩa rõ điều kiện cần recompute khi parent thay đổi.
4. Hệ thống trả raw toxicity, assessment, context cues, `directed_at_user_id` có grounding, attack instance, repeated events, evidence comment IDs + timestamps, rule_version; `null` khi không đủ bằng chứng.
5. Repeated dựa trên **cùng actor→target, >=2 instances hợp lệ và timestamps khác nhau**, không gom nhiều người công kích chung; có configurable time horizon nhưng không nới sau khi xem challenge để tăng điểm.
6. Quote/report/apology/defense/intervention/negation và những câu chửi cảm thán phải được kiểm soát; nội dung độc hại trong quote không tự sinh attack instance, nhưng clause xúc phạm mới ngoài quote vẫn có thể sinh.
7. Xử lý timeout/batch fallback, quality/gate khi model không tải; không xuất raw score giả. CPU moderation worker được ưu tiên tài nguyên so với worker training.
8. Hỗ trợ selector `default-v5` và `experimental-v6.2` chỉ qua quyền test/shadow, không nhầm model weights với rule processor version. Không tự đổi default.

## Nghiệm thu
- Gửi ít nhất 3 tin trong cùng thread (benign → attack → repeated attack): từng tin có analysis mới, lần sau nhận đủ prior grounded evidence mà không quét lại toàn bộ 3 lần.
- Không tạo repeated từ 2 actor khác nhau, lời can ngăn, trích dẫn hoặc lời xin lỗi thuần túy. Bài bình luận CLEAN reply người khác không đồng nghĩa targeted attack.
- Regression cached và CPU actual inference test có log tách riêng; kết quả offline/replay không tự gắn tên real-world eval.
- Benchmark so sánh số lần inference và latency incremental vs full recomputation, không tuyên bố số chưa đo.

## Bằng chứng / đầu ra
- Incremental API contracts, traces, reliability tests, regression report, benchmark và giới hạn coverage.


## Implementation specification (repository audit 04/11/2026)

- **Status:** DONE_VERIFIED
- **Dependencies:** T034, T035. FormalT028/T029 BLOCKED and T030–T033 PARTIAL remain independent.
- **Architecture context:** Social API FastAPI/SQLAlchemy schema0004, bearer sessions; posts/comments, durable worker and review/appeal already exist. Approved AI defaultV1.1 with threshold.41; v5 signal rules, legacy internal contract1.0.
- **Input:** authenticated requests and immutable synthetic fixtures; canonical model/dataset manifests when applicable.
- **Output:** implemented behavior below, versioned contract, test logs, source SHA, task evidence.
- **Backend/frontend/AI/database scope:** `services/moderation-ai/app/`; reuse existing modules and original API. No live migration/default-model mutation.
- **Concrete design:** Default-v5 context with bounded score cache; no v6.1/v6.2 default selection. New endpoint/worker opt-in, original endpoints unchanged.
- **Contract/schema:** `/api/live/moderate/comment`; pin schema/version, IDs, content_revision, decision_version and analysis provenance; fail closed on unknown version.
- **Acceptance:** all original Nghiệm thu criteria above plus existing tests pass, negative authorization/error paths verified. NOT_RUN is not PASS; no DONE_VERIFIED from docs alone.
- **Unit tests:** valid/malformed schema, limits, stale revision, duplicate IDs, unauthorized caller and absence of side effects.
- **Integration tests:** real temporary SQLite and existing services/worker, restart/retry/idempotency and transaction rollback. Actual inference/training tested separately when required.
- **E2E:** local browser when UI is in scope, independent contexts, no mocked API claimed as actual. For architecture-only T034, contract/sequence validation replaces browser testing.
- **Security/privacy:** bearer auth + server RBAC; membership/post visibility checked; no credentials in URL/log, no raw evidence to normal user; upload/config allowlists and no shell/eval of external input.
- **Errors/recovery:** bounded retry/backoff; truthful queued/failed/cancelled/stale states; explicit missing rights/model/data; preserve user input and idempotency key across retries.
- **Performance:** cap body1MiB/request, content8000chars, context50comments, event page100, no neural inference in send request. These are budgets/limits, not measured latency promises; record real timings.
- **Evidence:** [docs/realtime_moderation/INCREMENTAL_AI.md](../../docs/realtime_moderation/INCREMENTAL_AI.md); additional verified logs/outputs are listed below.
- **Definition of Done:** all task acceptance met with actual tests and retained evidence; otherwise PARTIAL/BLOCKED with exact missing criteria; update shared task order/progress.
- **Current risks/blockers:** Verified local evidence is recorded below; formal human-gold gates remain unmet. GPU/paid/external/private data/production not authorized. Training Studio CPU smoke authorized by current user only after accepted synthetic dataset/preflight. T041 also depends on T040 for unlabeled inputs.

Common safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md). Imported source preserved at workspace task-pack path; SHA/rename map in TASK_MERGE_REPORT.md.


### Execution evidence

Implement additive authenticated incremental AI adapter using approved default-v5, bounded model/text score cache, typed context/target/attack-instance evidence and context-dependency stale guard in existing worker. No v6.1/v6.2 default activation.



### Execution evidence

Additive default-v5 incremental adapter/client implemented; per-model/text LRU raw cache, typed context/target/instances/evidence,1800s horizon and worker snapshot dependency CAS. Explicit live-provenance-v1 subtractive report/quote gate preserves base-v5 flags/raw/assessment, prevents inherited pure-apology instanceFP; fresh outsidequote attack retained.15AIunit+4worker testsPASS, full737root/207SocialPASS. Actual approveddefaultV1.1 CPU2threads smoke6→3neuraltexts, scoresinvariant, grounded[b,c]; measured274.6676→222.9778ms(single sample). Original apps/weights/default/0.41/readiness baseline untouched; experimental selector rejected by liveclient.

- docs/realtime_moderation/INCREMENTAL_AI.md
- contracts/live_moderation_response.schema.json
- reports/task_rollout_20261104/T036_actual_benchmark.json
- reports/task_rollout_20261104/T036_root_regression.log
- reports/task_rollout_20261104/T036_social_regression.log


---

## Additional Social Feed v2 specification — 04/11/2026

Initial source status below is not an override of verified historical work. Current v2 acceptance is tracked separately.

# T036 — AI phân tích bình luận theo bài đăng và ngữ cảnh realtime

**Trạng thái ban đầu:** `NOT_STARTED — VERIFY_IN_REPOSITORY`  
**Độ ưu tiên:** `P0`  
**Phụ thuộc:** T035 comment/job lifecycle; các AI contracts hiện có  
**Loại:** Thực thi code + kiểm thử + evidence; không chỉ thiết kế tài liệu.

## 1. Mục tiêu

Tự phân tích **mỗi bình luận mới** cùng post gốc, parent và lịch sử liên quan để phát hiện toxic, target và repeated harassment; trả và lưu advisory/evidence versioned mà không tự ẩn comment.

## 2. Phạm vi

Worker orchestration/adapter Social API ↔ Moderation AI, context builder, inference history, target & repeated evidence, stale result prevention, tracing/latency.

## 3. Các bước thực hiện

1. Audit moderation worker và contract v1/v2 đang chạy; không thay default V1.1 hoặc kéo v6.1/v6.2 research vào runtime mà chưa có quyền.
2. Context builder lấy post text, comment hiện tại, parent chain, bounded sibling/reply context, actor ID đã ẩn danh, timestamp và attack history; ghi rõ cutoff, ordering, source revision.
3. Dùng AI pipeline đang được phê duyệt: raw ViSoBERT, lexicon, context, target, repeated, policy advisory; giữ các nhãn/score/risks tách biệt và truyền đủ evidence/comment IDs.
4. `reply_to_user_id` là người nhận reply, không phải `directed_at_user_id` khi chưa đủ attack evidence; raw toxic không tự thành directed instance.
5. Tổng hợp repeated theo `(actor_user_id,target_user_id)` với ít nhất hai attack instance/timestamp hợp lệ, loại apology, report/quote, intervention, self-defense không có attack mới.
6. Dùng revision/model+rule hash để lưu kết quả. Worker xử lý cũ kết thúc sau phải không ghi đè assessment mới hoặc visibility do moderator quyết định.
7. Đánh giá incremental recompute: chỉ cập nhật comment/threads phụ thuộc; giới hạn CPU và lưu metrics inference/queue wait.
8. Chế độ AI down => `UNKNOWN/RETRYING`, không tự gắn CLEAN. Schema và quyền nhận realtime events giữ đúng T034.

## 4. API, dữ liệu và hợp đồng tích hợp

Ghi nhận ít nhất `comment_id, post_id, source_revision, inference_model_version, processor_version, toxicity_score, moderation_assessment, policy_risk, visibility_state (owned by Social), directed_at_user_id, attack_instance_candidate, repeated_evidence_ids, job_state`. Giữ V1 `/api/v1/moderate/comment` và V2 `/api/v2/analyze` nếu hiện có.

## 5. Kế hoạch kiểm thử

- Positive/negative controls: CLEAN, direct insult, indirect/mỉa mai chưa chắc, non-directed profanity, quote, apology, self-defense, intervention.
- Repeated: same actor→target hai lần, actor A/B công kích qua lại, nhiều actor→một target nhưng không gom sai, target UNKNOWN.
- Ordering: parent gửi trước/đến muộn, results stale, job retry idempotent, AI offline/restore.
- Privacy: actor IDs ẩn danh trong AI calls/logs, user thường không nhận evidence nội bộ.
- Latency: trace ít nhất queue_wait/inference/result_delivery (không đặt số giả).

## 6. Acceptance criteria / Definition of Done

- [ ] Mỗi comment mới tự trigger AI job và cuối cùng có versioned advisory result nếu worker còn hoạt động.
- [ ] AI chạy có post/parent context, không chỉ text rời.
- [ ] Repeated evidence đúng actor–target và thời điểm, không gom nhiều actor.
- [ ] Quote/apology/intervention không tự tạo attack evidence nếu thiếu công kích mới.
- [ ] Không có double update/stale overwrite; AI down xử lý theo retry.
- [ ] Không thay default model, ngưỡng 0.41, visibility/policy.

## 7. Deliverables và bằng chứng

Context builder/adapter tests, fixture đa nick, trace JSON, performance logs, implementation notes.



Shared safeguards: [RULES_REALTIME_STUDIO.md](RULES_REALTIME_STUDIO.md), Social Feed v2 section. The source journal was unstarted; actual execution follows below.

## T036 Social Feed v2 — IN_PROGRESS, 04/11/2026

Verify post/parent context and existing target/repeated, stale snapshot and approved processor guards; no model/rule edits.

Evidence: 

## T036 Social Feed v2 — DONE_VERIFIED, 04/11/2026

5 Social worker tests and15 incremental analyzer tests PASS. Explicit new test verifies post text, parent chain and current reply in AI payload without account names/email; existing stale/forged-target/experimental-processor guards pass. No model or rule changes.

Evidence: reports/social_feed_v2_20261104/T036_worker.log, reports/social_feed_v2_20261104/T036_incremental.log


## Live usernames and structured reply tags - 05/11/2026

Added opt-in live_identity metadata/schema and authenticated /api/live/feed;
message ACKs and snapshots expose server-derived author_username plus readable
parent reply_to_user_id/username. Permissions filter content before resolving
handles; hidden parent identity remains null, client identity spoofing rejected.
Core V1 APIs/schemas, worker snapshot/hash logic, AI inputs/rules/model/threshold
and readiness lock untouched. No DB migration or rewriting historical text.

Social feed/post/comments display usernames, Reply shows an @username chip
and original parent excerpt; saved comments name the reply recipient. Chip is
presentation over parent_id, not text inserted into authored body, and is not
an attack verdict. Moderator context and actor-target evidence show names while
retaining canonical IDs. Plain typed handles without Reply create no parent link.

Validation:254Social tests PASS (26related included),15incremental AI tests
PASS,4actual Chrome control groups/3sessions PASS, both frontend builds PASS,
1311readiness files PASS. Actual default neural results: clean reply recipient
correct with no target/instance;2direct attacks Bob-to-Alice correctly grounded;
repeated pair/evidence correct and clean reply excluded. Synthetic controls,
not human-gold quality evaluation. Screenshots inspected for Social identity.

Active user demo_8d1daf6059b99b03 was preserved/read-only, never restarted.
Backend currently running uses old loaded routes: operator must stop/relaunch
demo to load names API. UI falls back on404 during that interval. A normal
relaunch creates a fresh demo DB/accounts; old session data/logs stay in their
original report directory, not reset/deleted. No training/default/production
change or task-status overwrite. Evidence: reports/demo_identity_20261105_*.log,
reports/demo_identity_20261105_ai_verified.json,
reports/demo_identity_20261105_verified.json and demo_531e30a5c4f2f43f/ actual
browser/AI evidence under reports/task_rollout_20261104/.
