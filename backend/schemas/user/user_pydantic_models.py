from typing import Annotated, Literal, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, StringConstraints, field_validator, model_validator


Username = Annotated[
    str,
    StringConstraints(
        strip_whitespace=True,
        min_length=3,
        max_length=32,
        pattern=r"^[A-Za-z0-9_]+$",
    ),
]
# Complexity rules are handled elsewhere.
Password = Annotated[str, StringConstraints(min_length=12)]


class UserCreateLocal(BaseModel):
    """
    Payload for /auth/signup (local).
    DB has username/hash optional overall, but for local signup we require them.
    """
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr
    username: Username
    password: Password
    password_confirm: Password

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()

    @model_validator(mode="after")
    def check_passwords_match(self):
        if self.password != self.password_confirm:
            raise ValueError("passwords do not match")
        return self


class UserLogin(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr
    password: str  # presence checked; complexity handled on signup

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class OAuthCallbackData(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    provider: Literal["google", "github"]
    provider_user_id: str
    email: Optional[EmailStr] = None
    email_verified: bool = False    # Providers may omit it
    display_name: Optional[str] = None

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: Optional[str]) -> Optional[str]:
        return v.strip().lower() if v else v

    @field_validator("provider_user_id")
    @classmethod
    def ensure_provider_user_id(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("provider_user_id cannot be empty")
        return v


class UserRead(BaseModel):
    """
    Safe projection of a User ORM object.
    - username and name are optional in DB, so Optional here.
    - role exposed as lower-case literal; service maps to/from your Enum.
    - uses from_attributes=True for ORM compatibility.
    """
    model_config = ConfigDict(from_attributes=True, extra="forbid", str_strip_whitespace=True)

    id: UUID
    email: EmailStr
    username: Optional[str] = None
    name: Optional[str] = None
    role: Literal["admin", "dm", "player"]
    is_approval_pending: bool


class UserRoleUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: UUID
    role: Literal["admin", "dm", "player"]


class UserApprovalUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    user_id: UUID
    is_approval_pending: bool