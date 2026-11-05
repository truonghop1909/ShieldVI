from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, field_validator


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class RegisterInput(StrictInput):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-z0-9_]+$")
    email: EmailStr = Field(max_length=254)
    password: SecretStr = Field(min_length=12, max_length=128)

    @field_validator("username", "email", mode="before")
    @classmethod
    def normalize_identity(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class LoginInput(StrictInput):
    username: str = Field(min_length=3, max_length=30, pattern=r"^[a-z0-9_]+$")
    password: SecretStr = Field(min_length=1, max_length=128)

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class UserOutput(BaseModel):
    id: str
    username: str
    role: str
    status: str
    created_at: datetime

    @classmethod
    def from_user(cls, user):
        return cls(id=user.id, username=user.username, role=user.role, status=user.status,
                   created_at=datetime.fromtimestamp(user.created_at, tz=timezone.utc))


class TokenOutput(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
