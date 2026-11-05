from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class CommentIn(BaseModel):
    comment_id: str = Field(min_length=1, max_length=120)
    user_id: str = Field(min_length=1, max_length=120, description="Pseudonymous ID, not a real username")
    text: str = Field(min_length=1, max_length=8000)
    timestamp: datetime
    parent_id: str | None = Field(default=None, max_length=120)
    mentioned_user_ids: list[str] = Field(default_factory=list, max_length=5, description="Optional platform-resolved user IDs; not annotated labels")


class AnalyzeRequest(BaseModel):
    thread_id: str = Field(min_length=1, max_length=120)
    comments: list[CommentIn] = Field(min_length=1, max_length=500)
    profile: Literal["conservative", "research_synthetic"] = "conservative"

    @model_validator(mode="after")
    def validate_thread(self):
        ids = [c.comment_id for c in self.comments]
        if len(ids) != len(set(ids)):
            raise ValueError("Trùng comment_id trong cùng một thread")
        lookup = {c.comment_id: c for c in self.comments}
        for c in self.comments:
            if c.timestamp.tzinfo is None or c.timestamp.utcoffset() is None:
                raise ValueError(f"{c.comment_id}: timestamp phải có timezone (ví dụ Z)")
            if c.parent_id:
                if c.parent_id == c.comment_id:
                    raise ValueError(f"{c.comment_id}: không được tự trả lời chính mình (self-parent)")
                if c.parent_id not in lookup:
                    raise ValueError(f"{c.comment_id}: parent_id không có trong thread")
                if lookup[c.parent_id].timestamp > c.timestamp:
                    raise ValueError(f"{c.comment_id}: parent timestamp nằm sau comment")
        for c in self.comments:
            seen = set()
            p = c.parent_id
            while p:
                if p in seen or p == c.comment_id:
                    raise ValueError(f"{c.comment_id}: có vòng lặp parent_id")
                seen.add(p)
                p = lookup[p].parent_id
        return self


class LexicalSignalOut(BaseModel):
    rule_id: str
    category: str
    matched_form: str
    strength: str
    canonical_form: str = ''
    language: str = ''
    reason: str = ''
    source_ids: list[str] = Field(default_factory=list)
    start: int | None = None
    end: int | None = None


class CommentOut(BaseModel):
    comment_id: str
    user_id: str
    parent_id: str | None
    timestamp: datetime
    toxicity_score: float
    toxic_for_moderation: bool
    toxic_for_repeated_rule: bool
    target_user_id: str | None
    target_method: str
    target_confidence: Literal["high", "medium", "low", "none"]
    profanity_detected: bool = False
    lexical_review_recommended: bool = False
    directed_insult_candidate: bool = False
    reported_or_apology_context: bool = False
    review_recommended: bool = False
    lexical_signals: list[LexicalSignalOut] = Field(default_factory=list)


class EvidenceOut(BaseModel):
    actor_user_id: str
    target_user_id: str
    evidence_comment_ids: list[str]
    n_distinct_timestamps: int
    target_confidence: str


class AnalyzeResponse(BaseModel):
    thread_id: str
    model_name: str
    model_threshold: float
    repeated_rule_threshold: float
    profile: str
    research_only: bool
    suspected_repeated_harassment: bool
    risk_level: Literal["none", "needs_review", "suspected_repeated"]
    risk_score_heuristic: int
    evidence: list[EvidenceOut]
    comments: list[CommentOut]
    warnings: list[str]


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_path: str | None
    details: str


class HumanReviewItem(BaseModel):
    comment_id: str = Field(min_length=1, max_length=120)
    human_label: Literal["clean", "toxic", "uncertain"]
    ai_label: Literal["clean", "toxic"]
    toxicity_score: float = Field(ge=0, le=1)
    lexical_flag: bool = False


class HumanReviewBatch(BaseModel):
    thread_id: str = Field(min_length=1, max_length=120)
    reviewer_id: str = Field(min_length=1, max_length=30)
    items: list[HumanReviewItem] = Field(min_length=1, max_length=500)

    @model_validator(mode="after")
    def unique_comment_ids(self):
        ids = [item.comment_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("Trùng comment_id trong lô nhãn")
        return self
