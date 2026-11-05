"""Versioned internal moderation contract, vendored identically by both services."""
from datetime import datetime
from typing import Annotated, Literal
from pydantic import AfterValidator, AwareDatetime, BaseModel, ConfigDict, Field, model_validator

OpaqueId = Annotated[str, Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9:_-]+$")]

def valid_text(value):
    if not value.strip() or "\x00" in value:
        raise ValueError("Invalid text")
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        raise ValueError("Invalid Unicode") from None
    return value

Text = Annotated[str, Field(min_length=1, max_length=8000), AfterValidator(valid_text)]

class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

class ContextComment(ContractModel):
    comment_id: OpaqueId
    user_id: OpaqueId
    text: Text
    timestamp: AwareDatetime
    parent_id: OpaqueId | None = None
    mentioned_user_ids: list[OpaqueId] = Field(default_factory=list, max_length=5)

class ModerationContext(ContractModel):
    post_id: OpaqueId
    source: Literal["social-api"] = "social-api"
    complete: bool = False
    recent_comments: list[ContextComment] = Field(default_factory=list, max_length=50)

class ModerationRequest(ContractModel):
    schema_version: Literal["1.0"]
    request_id: OpaqueId
    content_id: OpaqueId
    content_type: Literal["post", "comment"] = "comment"
    content_revision: int = Field(ge=1, strict=True)
    user_id: OpaqueId
    text: Text
    timestamp: AwareDatetime
    parent_id: OpaqueId | None = None
    mentioned_user_ids: list[OpaqueId] = Field(default_factory=list, max_length=5)
    context: ModerationContext
    language_hint: Literal["vi", "en", "mixed", "unknown"] = "vi"

    @model_validator(mode="after")
    def validate_context(self):
        current = ContextComment(comment_id=self.content_id, user_id=self.user_id, text=self.text,
            timestamp=self.timestamp, parent_id=self.parent_id, mentioned_user_ids=self.mentioned_user_ids)
        rows = [*self.context.recent_comments, current]
        if any(row.timestamp > self.timestamp for row in self.context.recent_comments):
            raise ValueError("Context cannot contain future comments")
        lookup = {row.comment_id: row for row in rows}
        if len(lookup) != len(rows) or sum(len(row.text) for row in rows) > 64000:
            raise ValueError("Duplicate ids or excessive context")
        for row in rows:
            seen = {row.comment_id}
            parent = row.parent_id
            while parent:
                if parent not in lookup or parent in seen:
                    raise ValueError("Missing parent or cyclic context")
                if lookup[parent].timestamp > row.timestamp:
                    raise ValueError("Parent timestamp is after child")
                seen.add(parent)
                parent = lookup[parent].parent_id
        return self

class LexicalSignal(ContractModel):
    rule_id: str = Field(min_length=1, max_length=120)
    category: Literal["profanity", "directed_insult", "ambiguous", "other_sensitive"]
    matched_form: str = Field(max_length=8000)
    strength: str = Field(max_length=32)
    canonical_form: str = Field(default="", max_length=1000)
    language: str = Field(default="", max_length=32)
    reason: str = Field(default="", max_length=3000)
    source_ids: list[str] = Field(default_factory=list, max_length=30)
    start: int | None = Field(default=None, ge=0)
    end: int | None = Field(default=None, ge=0)

class TargetEvidence(ContractModel):
    target_user_id: OpaqueId | None = None
    method: str = Field(max_length=100)
    confidence: Literal["none", "low", "medium", "high"]

class RepeatedEvidence(ContractModel):
    actor_user_id: OpaqueId
    target_user_id: OpaqueId
    evidence_comment_ids: list[OpaqueId] = Field(min_length=2, max_length=51)
    n_distinct_timestamps: int = Field(ge=2, le=51)
    target_confidence: Literal["medium", "high"]

class ModerationResponse(ContractModel):
    schema_version: Literal["1.0"]
    request_id: OpaqueId
    content_id: OpaqueId
    content_revision: int = Field(ge=1, strict=True)
    model_name: str = Field(min_length=1, max_length=200)
    model_version: str = Field(min_length=1, max_length=200)
    lexicon_version: str = Field(min_length=1, max_length=100)
    analyzed_at: AwareDatetime
    model_threshold: Literal[0.41]
    toxicity_score: float = Field(ge=0, le=1, strict=True)
    ai_label: Literal["CLEAN", "TOXIC"]
    lexical_review_recommended: bool
    directed_insult_candidate: bool
    reported_or_apology_context: bool
    lexical_signals: list[LexicalSignal] = Field(max_length=2000)
    target_evidence: TargetEvidence
    suspected_repeated_harassment: bool
    evidence: list[RepeatedEvidence] = Field(max_length=50)
    suggested_action: Literal["approve", "needs_review"]
    decision_authority: Literal["advisory"]
    limitations: list[Annotated[str, Field(max_length=3000)]] = Field(max_length=30)

    @model_validator(mode="after")
    def coherent_prediction(self):
        if self.ai_label != ("TOXIC" if self.toxicity_score >= self.model_threshold else "CLEAN"):
            raise ValueError("Label/score mismatch")
        if self.suspected_repeated_harassment != bool(self.evidence):
            raise ValueError("Repeated evidence mismatch")
        return self
