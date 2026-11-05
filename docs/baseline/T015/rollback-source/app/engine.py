"""Explainable, heuristic actor-to-target and repeated-harassment engine.

Never reads dataset gold labels; all targets are inferred from platform metadata.
"""
from collections import Counter, defaultdict
from datetime import timezone
from .schemas import AnalyzeRequest, AnalyzeResponse, CommentOut, EvidenceOut
from .lexical import detect


CONF_LEVELS = {"none": 0, "low": 1, "medium": 2, "high": 3}


def analyze_thread(payload: AnalyzeRequest, predictor) -> AnalyzeResponse:
    ordered = sorted(payload.comments, key=lambda c: (c.timestamp, c.comment_id))
    scores = predictor.predict_scores([c.text for c in ordered])
    if len(scores) != len(ordered):
        raise ValueError("Model trả về số lượng điểm không khớp số bình luận")
    for score in scores:
        if not isinstance(score, (float, int)) or not 0 <= score <= 1:
            raise ValueError("Model trả về điểm ngoài [0,1]")

    by_id = {c.comment_id: c for c in ordered}
    root = next((c for c in ordered if not c.parent_id), ordered[0])
    # Separate the original comment-level threshold from the research-only
    # conversation threshold tuned on synthetic validation.
    repeated_thr = predictor.threshold if payload.profile == "conservative" else 0.03
    output = []
    past_replies = defaultdict(list)

    for c, score in zip(ordered, scores):
        lexical = detect(c.text)
        parent_author = by_id[c.parent_id].user_id if c.parent_id else None
        explicit_mentions = [x for x in c.mentioned_user_ids if x != c.user_id]
        explicit_mentions = list(dict.fromkeys(explicit_mentions))
        target = None
        method = "undetermined"
        confidence = "none"

        if len(explicit_mentions) == 1:
            target, method, confidence = explicit_mentions[0], "platform_mention", "high"
        elif parent_author and parent_author != c.user_id:
            target, method, confidence = parent_author, "reply_parent_author", "medium"
        elif root.user_id != c.user_id:
            target, method, confidence = root.user_id, "thread_root_fallback", "low"

        # Target-V2 research heuristic: majority of prior direct reply recipients
        # can disambiguate a reply to a third-party. This is low confidence.
        if payload.profile == "research_synthetic" and parent_author and parent_author != c.user_id and len(past_replies[c.user_id]) >= 2 and method != "platform_mention":
            common, count = Counter(past_replies[c.user_id]).most_common(1)[0]
            if count >= 2 and common != parent_author:
                target, method, confidence = common, "speaker_history_candidate", "low"

        if parent_author and parent_author != c.user_id:
            past_replies[c.user_id].append(parent_author)

        output.append(CommentOut(
            comment_id=c.comment_id,
            user_id=c.user_id,
            parent_id=c.parent_id,
            timestamp=c.timestamp,
            toxicity_score=round(float(score), 6),
            toxic_for_moderation=score >= predictor.threshold,
            toxic_for_repeated_rule=score >= repeated_thr,
            target_user_id=target,
            target_method=method,
            target_confidence=confidence,
            profanity_detected=lexical['profanity_detected'],
            lexical_review_recommended=lexical['lexical_review_recommended'],
            directed_insult_candidate=lexical['directed_insult_candidate'],
            reported_or_apology_context=lexical['reported_or_apology_context'],
            review_recommended=score >= predictor.threshold or lexical['lexical_review_recommended'],
            lexical_signals=lexical['lexical_signals'],
        ))

    pairs = defaultdict(list)
    for c in output:
        if not c.toxic_for_repeated_rule or not c.target_user_id:
            continue
        if c.user_id == c.target_user_id:
            continue
        # Conservative deployment must not promote uncertain root fallback to a harassment alarm.
        if payload.profile == "conservative" and CONF_LEVELS[c.target_confidence] < 2:
            continue
        pairs[(c.user_id, c.target_user_id)].append(c)

    evidence = []
    for (actor, target), rows in sorted(pairs.items()):
        times = {c.timestamp.astimezone(timezone.utc).isoformat() for c in rows}
        if len(rows) >= 2 and len(times) >= 2:
            weakest = min((c.target_confidence for c in rows), key=lambda v: CONF_LEVELS[v])
            evidence.append(EvidenceOut(
                actor_user_id=actor,
                target_user_id=target,
                evidence_comment_ids=[c.comment_id for c in rows],
                n_distinct_timestamps=len(times),
                target_confidence=weakest,
            ))

    has_repeated = bool(evidence)
    has_any_moderation = any(c.toxic_for_moderation for c in output)
    has_any_lexical = any(c.lexical_review_recommended for c in output)
    has_any_research = any(c.toxic_for_repeated_rule for c in output)
    if has_repeated:
        level = "suspected_repeated"
        n = max(len(ev.evidence_comment_ids) for ev in evidence)
        risk = min(95, 65 + 5 * n)
    elif has_any_moderation or has_any_lexical or (payload.profile == "research_synthetic" and has_any_research):
        level = "needs_review"
        risk = 35 if has_any_moderation else 20
    else:
        level = "none"
        risk = 0

    warnings = [
        "Đây là cảnh báo hỗ trợ kiểm duyệt, KHÔNG kết luận một cá nhân thực hiện bắt nạt.",
        "Target suy luận từ cấu trúc trả lời/lượt tương tác; có thể sai với trích dẫn, đùa giỡn hoặc nhắc tới bên thứ ba.",
        "Risk score là heuristic chưa được hiệu chuẩn; mô hình chưa phân loại category/severity.",
        "Không đánh giá hiệu năng thực tế bằng test mô phỏng hoặc nhãn AI dự thảo.",
        "Từ điển đa ngôn ngữ chỉ tạo tín hiệu rà soát, không tự động nâng nhãn toxic hoặc tính là bằng chứng bắt nạt lặp lại.",
    ]
    if payload.profile == "research_synthetic":
        warnings.append("NGHIÊN CỨU: ngưỡng 0.03 được chọn trên validation mô phỏng; không dùng để tự động xử phạt/công bố kết luận.")

    return AnalyzeResponse(
        thread_id=payload.thread_id,
        model_name=getattr(predictor, "name", "unknown"),
        model_threshold=float(predictor.threshold),
        repeated_rule_threshold=float(repeated_thr),
        profile=payload.profile,
        research_only=payload.profile == "research_synthetic",
        suspected_repeated_harassment=has_repeated,
        risk_level=level,
        risk_score_heuristic=risk,
        evidence=evidence,
        comments=output,
        warnings=warnings,
    )
