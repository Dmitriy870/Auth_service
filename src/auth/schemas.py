from datetime import datetime
from enum import Enum
from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class KafkaTopic(str, Enum):
    MODELS_TOPIC = "models_topic"
    EVENTS_TOPIC = "events_topic"


class EventName(str, Enum):
    REGISTRATION = "registration"
    LOGIN = "login"
    REFRESH = "refresh_token"
    CONFIRM = "user_confim_email"
    RESEND = "resend_email_request"
    RESET_PASSWORD = "reset_password_request"
    CONFIRM_PASSWORD = "confirm_password_reset"
    GET_ALL = "get_all"
    UPDATE = "update"
    GET = "get_me"
    DELETE = "delete"


class EventType(str, Enum):
    MODEL = "MODEL"
    EVENT = "EVENT"


class UserBase(BaseModel):
    email: EmailStr = Field(...)


class UserCreate(UserBase):
    username: str = Field(...)
    password: str = Field(...)
    role_id: UUID | None = Field(None)


class UserUpdate(BaseModel):
    username: str | None = Field(None)
    email: EmailStr | None = Field(None)


class UserUpdatePassword(BaseModel):
    id: UUID
    password: str = Field(...)


class UserConfirm(BaseModel):
    id: UUID
    is_approved: bool = Field(...)


class UserResponse(UserCreate):
    id: UUID = Field(...)
    created_at: datetime
    updated_at: datetime
    is_approved: bool = Field(...)
    is_globally_blocked: bool = Field(...)
    role_id: UUID = Field(...)


class UserResponseWithRoleName(UserCreate):
    id: UUID = Field(...)
    created_at: datetime
    updated_at: datetime
    is_approved: bool = Field(...)
    is_globally_blocked: bool = Field(...)
    role_id: UUID = Field(...)
    role: str = Field(...)


class RoleBase(BaseModel):
    id: UUID = Field(...)
    name: str = Field(...)


class RoleResponse(RoleBase):
    pass


class LoginRequest(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(...)


class TokensResponse(BaseModel):
    access_token: str = Field(...)
    refresh_token: str | None = Field(None)
    token_type: str = Field("bearer")
    role: str | None = Field(None)


class PaginatedUserResponse(BaseModel):
    users: List[UserResponse]
    total: int = Field(...)
    page: int = Field(...)
    page_size: int = Field(...)
    total_pages: int = Field(...)


class SetFalse(BaseModel):
    is_approved: bool = Field(False)


class RefreshTokenRequest(BaseModel):
    refresh_token: str = Field(...)


class AccessTokenRequest(BaseModel):
    access_token: str = Field(...)


class ValidationResponse(BaseModel):
    valid: bool = Field(...)
    user_id: UUID = Field(...)


class Event(BaseModel):
    event_name: str = Field(...)
    model_data: dict | None = Field(None)
    entity_id: str | None = Field(None)
    model_type: str | None = Field(None)
    received_from: str = "auth"
