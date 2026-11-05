from datetime import datetime
from uuid import UUID

from pydantic import Field, field_validator

from .schemas import StrictInput


class ContentCreate(StrictInput):
    body: str = Field(min_length=1, max_length=8000)

    @field_validator("body")
    @classmethod
    def nonblank(cls, value):
        if not value.strip() or "\x00" in value:
            raise ValueError("Body must contain non-whitespace text")
        try:
            value.encode("utf-8")
        except UnicodeEncodeError:
            raise ValueError("Body must contain valid Unicode") from None
        return value  # Preserve original spelling/spacing; never render as raw HTML.


class CommentCreate(ContentCreate):
    parent_id: UUID | None = None


class ContentUpdate(ContentCreate):
    expected_revision: int = Field(ge=1)
    expected_decision_version: int = Field(ge=0)


class ContentDelete(StrictInput):
    expected_revision: int = Field(ge=1)
    expected_decision_version: int = Field(ge=0)
    reason: str | None = Field(default=None, min_length=1, max_length=500)

    @field_validator("reason")
    @classmethod
    def nonblank_reason(cls, value):
        if value is not None and (not value.strip() or "\x00" in value or any(0xD800 <= ord(char) <= 0xDFFF for char in value)):
            raise ValueError("Reason cannot be blank")
        return value


class PostOutput(StrictInput):
    id: str
    author_id: str
    body: str | None
    content_revision: int
    decision_version: int
    visibility_status: str
    review_status: str | None
    risk_tier: str | None
    created_at: datetime
    updated_at: datetime


class CommentOutput(PostOutput):
    post_id: str
    parent_id: str | None


class PostPage(StrictInput):
    items: list[PostOutput]
    page: int
    page_size: int
    total: int


class CommentPage(StrictInput):
    items: list[CommentOutput]
    page: int
    page_size: int
    total: int
