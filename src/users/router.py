from fastapi import APIRouter, Depends, Form, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from database.dependencies import get_scoped_session_dependency
from users.schemas import UserCreate, UserResponse
from users.service import (
    confirm_user,
    register_user,
    request_password_reset,
    resend_confirmation_email,
    reset_password,
)

router = APIRouter(tags=["Users"])


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    session: AsyncSession = Depends(get_scoped_session_dependency),
):
    email = email.lower().strip()
    user_data = UserCreate(username=username, email=email, password=password)
    return await register_user(user_data, session)


@router.get("/users/confirm", status_code=status.HTTP_200_OK)
async def confirm_email(token: str, session: AsyncSession = Depends(get_scoped_session_dependency)):
    user = await confirm_user(token, session)
    return {"detail": "Email confirmed successfully.", "user": user}


@router.post("/users/resend-confirmation", status_code=status.HTTP_200_OK)
async def resend_confirmation(
    email: str = Form(...),
    session: AsyncSession = Depends(get_scoped_session_dependency),
):
    email = email.lower().strip()
    return await resend_confirmation_email(email, session)


@router.post("/users/password-reset", status_code=status.HTTP_200_OK)
async def request_reset(
    email: str = Form(...),
    session: AsyncSession = Depends(get_scoped_session_dependency),
):
    email = email.lower().strip()
    return await request_password_reset(email, session)


@router.post("/users/password-reset/confirm", status_code=status.HTTP_200_OK)
async def reset_password_endpoint(
    token: str = Query(...),
    new_password: str = Form(...),
    session: AsyncSession = Depends(get_scoped_session_dependency),
):
    return await reset_password(token, new_password, session)
