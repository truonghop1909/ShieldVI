> CURRENT authority: latest PartsA/B/C restore T028-real200 + same human Round1/Round2, currently BLOCKED. Historical synthetic/CPU DONE is preserved, not real acceptance. Wikimedia paused/no more contact questions. No new training or production activation. See tasks/CURRENT_AI_SCOPE.json and docs/ai-update/final-report/INDEPENDENT_READINESS.md; older scope notices below are historical.

# 05 — Release gates và rollback

> Current autonomous scope03/11/2026: T028=REAL200 (still0/BLOCKED); synthetic500/G2-S is a separate accepted-AI research dataset, not human/real gold. Independent research T029–T033 may proceed; CUDA/cost/production approvals remain gated. Later scope notes override older synthetic-only T028 wording below. See final-report and current task files.


## Gate G0 (sau T020)
- Có snapshot baseline: git commit, dependency versions, API shape, model config, test pass/fail; checkpoint gốc tồn tại nhưng không thay đổi.

## Gate G1 (sau T021–T026): rule-based update
- Regression + counterexamples pass; output cũ ổn; no new auto-hide/ban.
- Bảng before/after cho 5 thread; theo dõi số case cải thiện và số case mới sai.
- Nếu human labels chưa hoàn thiện: ghi “developer regression only”, chưa tuyên bố nâng performance ngoài thực tế.

## Gate G2 (sau T027–T028): dữ liệu theo protocol

### G2-S — synthetic research, protocol T028 hiện hành (03/11/2026)
- AI tự viết hội thoại và nhãn; dùng bộ 200 hiện có khi đã kiểm chứng, giữ data_origin/label_source=synthetic, human_gold=false. Người dùng đã chọn dùng nhãn AI, không bắt buộc manual review hoặc thu thập Internet/contact Wikimedia.
- Artifact/schema/parent/time/target/repeated phải hợp lệ; có manifest/hash, phân bố/giới hạn, kiểm exact/near-duplicate và leakage với holdout gốc. UNCERTAIN tách riêng, không giả nhãn người.
- Bộ 200 synthetic chỉ dùng augmentation training, không dùng đồng thời làm test. ViCTSD validation/test hiện có giữ nguyên; model selection chỉ dùng validation. Thiếu benchmark hội thoại thật không chặn thí nghiệm synthetic này.
- Đạt G2-S chỉ cho phép xét bước G3; không tự duyệt tài nguyên/train/deploy. Code readiness phải kiểm chứng dữ liệu thật sự theo protocol, không chỉ sửa cờ trạng thái.

### G2-R — đánh giá thực tế độc lập, tùy chọn mở rộng
- Khi có dữ liệu thật: giữ provenance/quyền dùng/ẩn danh, nhãn người phù hợp và blind isolation; chỉ công bố metrics tương ứng sau kiểm chứng. Nhánh này không còn là prerequisite của T028/G2-S.
- evaluation_manifest.json và real_conversations vẫn mô tả nhánh real cũ; không điền synthetic hoặc nhãn AI vào đó để giả đạt G2-R.

G2-S thay điều kiện real/human bắt buộc trước đây theo yêu cầu người dùng. Kết quả synthetic không chứng minh hiệu quả ngoài đời; G4/G5 vẫn cần đánh giá và quyết định phù hợp trước promotion.

## Gate G3 (trước T029): duyệt GPU/train
Người dùng duyệt rõ dataset version, base model/path, train split, hyperparameters, resource, output path mới, điều kiện dừng. Không chạy CPU train ngầm và không upload test/user data lên dịch vụ ngoài.

## Gate G4 (sau T030): đánh giá candidate
- Candidate được đánh giá trên tập tương đương B0; không có data leakage, có confusions/per-class scores, FP/FN breakdown theo apology, indirect attack, teencode; nếu tệ hơn về yêu cầu an toàn, không promote.
- Không đặt một số ngưỡng cải thiện cứng tùy tiện: người dùng/giáo viên phê duyệt trade-off. Nếu bằng chứng không đủ → giữ V1.

## Gate G5 (trước T031): quyết định deploy
- Người dùng duyệt model registry manifest, rollback to V1, canary/shadow test, integration smoke. Không overwrite `visobert_toxic_final`.
- Ghi model version trên Dashboard/API; nếu lỗi inference, Social API trả UNKNOWN/retry chứ không auto-hold.

## Gate G6 (T032–T033): báo cáo
- Checkpoint đúng, latency/health, human review, model raw vs policy, audit và privacy, E2E offline-worker test. Đánh dấu những gì chỉ mock, chỉ synthetic, chưa được xác thực.

**Kill switch:** HIGH auto-hold tắt theo mặc định, bật chỉ sau chính sách riêng được kiểm chứng và người dùng duyệt. Model update **không tự bật** chế độ này.

## Current all-task authorization: bounded localCPU alternative

A separately versioned frozen-encoder/head-only CPU experiment may execute under the latest user request to run all tasks and revise blocked scope: max4threads/900seconds, externalcost0, config+preparedSHA-bound local authorization record quoting the request. This record does not claim human approval of exact hyperparameters and cannot approve the older GPU/fullfine-tune mode. G2-S still recomputes data integrity/leakage; V1/0.41/source/test/DB remain immutable. One candidate run, selection only from validation; a worse candidate is reported/rejected, not hidden or retrained against test. T031 acceptance is local shadow/fallback/rollback decision; production unchanged.

## Current follow-up: rejected work versus rejected model

The latest request ("task nào bị từ chối thì sửa task rồi thực hiện tiếp đi") permits continued feasible local rework. Preserve the prior r03 negative decision and task completion history. One new r04 recipe uses the same bounded CPU scope, lowers synthetic loss weight/LR and increases baseline distillation; exact configuration, data and user request are hash-bound before training in `reports/ai_update/candidate_revision_20261103/`. Validation selection is exploratory because historical evaluation was already viewed. No test or development-challenge rescore in this follow-up; no checkpoint activation. The original numeric gates are unchanged. A passed validation screen alone never authorizes promotion.

Scope clarification may remove superseded REAL/GPU prerequisites from local research tasks. A quality rejection requires better measured behavior; it cannot be resolved by relabeling examples, lowering gates or marking deployment DONE. A filesystem permission failure may be retried with the appropriate execution permission; editing a task does not grant additional resource or production authority.
