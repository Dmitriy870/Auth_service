from uuid import UUID

from fastapi import APIRouter, Depends, Form, Header, Query, Response, status

from auth.dependencies import get_current_user
from auth.schemas import LoginRequest, TokensResponse, UserCreate, UserResponse
from auth.service import (
    confirm_user,
    login_user,
    refresh_access_token,
    register_user,
    request_password_reset,
    resend_confirmation_email,
    reset_password,
)
from database import get_unit_of_work
from repositories.uow import UnitOfWork

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    email = email.lower().strip()
    user_data = UserCreate(username=username, email=email, password=password)
    return await register_user(user_data, uow)


@router.post("/users/token", response_model=TokensResponse, status_code=status.HTTP_200_OK)
async def get_token(
    email: str = Form(...),
    password: str = Form(...),
    uow: UnitOfWork = Depends(get_unit_of_work),
    response: Response = None,
):
    data = LoginRequest(email=email, password=password)
    return await login_user(data, uow, response)


@router.post("/users/refresh", response_model=TokensResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    refresh_token: str = Header(..., alias="Refresh-Token"),
    uow: UnitOfWork = Depends(get_unit_of_work),
    response: Response = None,
):
    return await refresh_access_token(refresh_token, uow, response)


@router.get("/users/confirm", status_code=status.HTTP_200_OK)
async def confirm_email(
    token: str,
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    user = await confirm_user(token, uow)
    return {"detail": "Email confirmed successfully.", "user": user}


@router.post("/users/resend-confirmation", status_code=status.HTTP_200_OK)
async def resend_confirmation(
    email: str = Form(...),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    email = email.lower().strip()
    return await resend_confirmation_email(email, uow)


@router.post("/users/password-reset", status_code=status.HTTP_200_OK)
async def request_reset(
    email: str = Form(...),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    email = email.lower().strip()
    return await request_password_reset(email, uow)


@router.post("/users/password-reset/confirm", status_code=status.HTTP_200_OK)
async def reset_password_endpoint(
    token: str = Query(...),
    new_password: str = Form(...),
    uow: UnitOfWork = Depends(get_unit_of_work),
):
    return await reset_password(token, new_password, uow)


@router.get("/users/protected")
async def some_protected_route(current_user_id: UUID = Depends(get_current_user)):
    # current_user_id — это тот, кто сейчас залогинен
    return {"message": "Hello, your user_id is " + str(current_user_id)}
