from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr


class UserCreate(UserBase):
    username: str
    password: str
    role_id: UUID | None = None


class UserUpdate(BaseModel):
    username: str | None = None
    email: EmailStr | None = None
    password: str | None = None


class UserResponse(UserCreate):
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_approved: bool
    is_globally_blocked: bool
    role_id: UUID

    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    id: UUID
    name: str


class RoleResponse(RoleBase):
    pass

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokensResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"

    class Config:
        from_attributes = True
