from datetime import datetime
from typing import List
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


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

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    id: UUID = Field(...)
    name: str = Field(...)


class RoleResponse(RoleBase):
    pass

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(...)


class TokensResponse(BaseModel):
    access_token: str = Field(...)
    refresh_token: str | None = Field(None)
    token_type: str = Field("bearer")

    class Config:
        from_attributes = True


class PaginatedUserResponse(BaseModel):
    users: List[UserResponse]
    total: int = Field(...)
    page: int = Field(...)
    page_size: int = Field(...)
    total_pages: int = Field(...)


class SetFalse(BaseModel):
    is_approved: bool = Field(False)
