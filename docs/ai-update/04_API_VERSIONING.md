# 04 — Contract AI V2: chỉ mở rộng, không phá dữ liệu V3

## Nguyên tắc

- Giữ `POST /api/analyze`, input (`thread_id, comments[]`, `comment_id,parent_id,user_id,timestamp,text,mentioned_user_ids`) và output `toxicity_score`, `toxic_for_moderation`, `review_recommended`, `target_*`, `lexical_signals` để Dashboard V3 và Social adapter cũ không vỡ.
- Thêm object tuỳ chọn `analysis_signals` cho từng comment: `context_tags`, `directed_attack_candidate`, `attack_confidence`, `target_candidate`, `target_evidence`, `lexicon_version`, `rule_version`, `needs_human_review`. Không thay nghĩa `toxic_for_moderation`.
- Thêm metadata top-level `analysis_version`, `checkpoint_id`, `source_model_threshold`, `rule_versions`, `policy_executed=false` nếu được; nếu schema không cho thêm tùy ý thì version contract và sửa serializer/test rõ ràng.
- Dữ liệu `target_evidence` chỉ là tham chiếu comment IDs/method, không chứa thông tin riêng tư người ngoài.
- Các prediction model raw, signal lexicon/context và evidence repeated cần phân tách. `risk_level` cũ là **heuristic của engine**, không tự biến thành Social policy risk.
- Contract tích hợp Social API có idempotency key, model_version, timeout, status/unknown; Social API mới sở hữu visibility và audit.

## Tránh breaking change

- Không thay kiểu `toxic_for_moderation` sang string hay tái định nghĩa `risk_level` âm thầm.
- Nếu cần breaking change, tạo endpoint `/api/v2/analyze` hoặc version JSON rõ, giữ old endpoint với compatibility adapter và test contract.
- UI nên hiển thị “ViSoBERT dự đoán TOXIC” riêng với “Context: APOLOGY, không là lượt công kích mới” và “Quyết định: Admin/Policy”.

## Những test bắt buộc

Legacy sample Thread DEMO_A vẫn trả 200 và field cũ; new JSON schema parse; model unavailable trả 503 (không tạo score fake); timeout Social API xử lý UNKNOWN/retry; không tự quyết định HIDDEN trong AI API.

## Current camping revision — context-v3 / repeated-v4

`APOLOGY_ACCEPTANCE` means accepting another person's apology, distinct from `ACKNOWLEDGEMENT` of one's own fault. Clients should tolerate additional context tags; the Dashboard renders the new tag explicitly. A fresh attack still takes precedence over apology/acceptance or intervention.

`analysis_signals.attack_instance_basis` is additive/optional for parsing older V2 responses. `context_with_grounded_target` requires a clause-level attack and a medium/high-confidence target; it may identify an advisory attack instance even when raw `toxic_for_repeated_rule` is false. `insufficient_context_or_target` abstains. Repeated-v4 groups qualified instances by actor/target at distinct timestamps. This does not alter any model threshold or raw/legacy field and does not execute Social policy. The V2 contract preserves analysis_version2.0 while rule_versions identify the changed evidence semantics. Model scores, lexical evidence, advisory assessment, context targets and policy remain separate. Legacy `/api/analyze` and internal Social moderation semantics are preserved.

## GAME_RANK_30 recovery revision ? additive analysis2.0/context-v2

V2comment c? `reply_to_user_id` (t?c gi? parent th?c t?), `directed_at_user_id` (ch? target c?ng k?ch ???c grounded), `moderation_assessment` (CLEAN/TOXIC/UNCERTAIN,basis,advisory_only=true,human_gold=false) v? `policy_risk` (LOW/REVIEW/UNKNOWN,reason,executed=false). C?c field m?i optional ?? parse response c?; response m?i ?i?n ??y ??. Tag ACKNOWLEDGEMENT v? context.non_attack_context_confirmed/unresolved_new_clause h? tr? nh?n l?i theo ph?m vi m?nh ??. Raw score/threshold/legacytarget_* kh?ng ??i.

Policy signal n?y l? ?? xu?t AI, kh?ng ph?i ch?nh s?ch Social ?? th?c thi hay visibility; REVIEW ???c gi? khi rawTOXIC m?u thu?n contextCLEAN. K?t qu? h? tr? kh?ng ph?i nh?n ng??i. Rawfallback ???c gi? khi ch?a c? ?? context; xin l?i kh?ng ph?i whitelist. EndpointSocial1.0 v? legacy/api/analyze kh?ng th?m/s?a semantics. JSONschema m?i sinh t? AnalyzeResponseV2; ch?a deploy production.


## context-v4 / target-v4 — additive clause grounding

ContextSignals.attack_clause_spans is optional for older responses and uses half-open coordinates in normalized folded context text, not original text offsets. Participant metadata only grounds names literally present in an asserted attack clause; background/quoted names do not automatically become targets. Missing addressee metadata still abstains. Raw fields, legacy API and Social policy semantics are unchanged.
