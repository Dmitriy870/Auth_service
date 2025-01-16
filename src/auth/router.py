from fastapi import APIRouter, Depends, Form, Header, Query, status
from pydantic import EmailStr
from redis.asyncio import Redis

from auth.dependencies import (
    CurrentAdmin,
    CurrentUser,
    get_redis_client,
    get_user_service,
)
from auth.schemas import LoginRequest, TokensResponse, UserCreate, UserResponse
from auth.service import UserService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    username: str = Form(...),
    email: EmailStr = Form(...),
    password: str = Form(...),
    service: UserService = Depends(get_user_service),
    redis_client: Redis = Depends(get_redis_client),
):
    email = email.lower().strip()
    user_data = UserCreate(username=username, email=email, password=password)
    return await service.register_user(user_data, redis_client)


@router.post("/users/token", response_model=TokensResponse, status_code=status.HTTP_200_OK)
async def get_token(
    email: EmailStr = Form(...),
    password: str = Form(...),
    service: UserService = Depends(get_user_service),
):
    data = LoginRequest(email=email, password=password)
    return await service.login_user(data)


@router.post("/users/refresh", response_model=TokensResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_token: str = Header(..., alias="Refresh-Token"),
    service: UserService = Depends(get_user_service),
):
    return await service.refresh_access_token(refresh_token)


@router.get("/users/confirm", status_code=status.HTTP_200_OK)
async def confirm_email(
    code: str = Query(...),
    encrypted_user_id: str = Query(...),
    service: UserService = Depends(get_user_service),
    redis_client: Redis = Depends(get_redis_client),
):
    user = await service.confirm_user(code, encrypted_user_id, redis_client)
    return {"detail": "Email confirmed successfully.", "user": user}


@router.post("/users/resend-confirmation", status_code=status.HTTP_200_OK)
async def resend_confirmation(
    email: EmailStr = Form(...),
    service: UserService = Depends(get_user_service),
    redis_client: Redis = Depends(get_redis_client),
):
    email = email.lower().strip()
    return await service.resend_confirmation_email(email, redis_client)


@router.post("/users/password-reset", status_code=status.HTTP_200_OK)
async def request_reset(
    email: EmailStr = Form(...),
    service: UserService = Depends(get_user_service),
    redis_client: Redis = Depends(get_redis_client),
):
    email = email.lower().strip()
    return await service.request_password_reset(email, redis_client)


@router.post("/users/password-reset/confirm", status_code=status.HTTP_200_OK)
async def reset_password_endpoint(
    code: str = Query(...),
    encrypted_user_id: str = Query(...),
    new_password: str = Form(...),
    service: UserService = Depends(get_user_service),
    redis_client: Redis = Depends(get_redis_client),
):
    return await service.reset_password(code, new_password, encrypted_user_id, redis_client)


@router.get("/users/me")
async def some_protected_route(current_user: CurrentAdmin):
    return {"message": f"Hello, {current_user.username}"}


@router.get("/users/all")
async def get_all_users(
    current_user: CurrentUser,
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    sort_by: str = Query(None, regex="^(created_at|username|role)$"),
    order: str = Query("asc", regex="^(asc|desc)$"),
    role: str = Query(None),
    service: UserService = Depends(get_user_service),
):
    return await service.get_all_user(page, page_size, sort_by, order, role)


@router.get("/roles/all")
async def get_all_roles(
    current_user: CurrentUser, service: UserService = Depends(get_user_service)
):
    return await service.get_all_roles()


@router.post("/user/admin/role")
async def update_user_role(
    email: EmailStr = Form(...),
    role: str = Form(...),
    current_admin=CurrentAdmin,
    service: UserService = Depends(get_user_service),
):
    return await service.update_users_role(email, role)
