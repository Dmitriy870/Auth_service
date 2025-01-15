from fastapi import Response

from auth.enums import ActionEnum, RoleEnum
from auth.exceptions import (
    AlreadyConfirmedException,
    AlreadyRegisteredException,
    InvalidTokenException,
    NotFoundException,
    ServerErrorException,
    TokenExpiredException,
    UnauthorizedException,
)
from auth.schemas import LoginRequest, TokensResponse, UserCreate, UserResponse
from auth.utils import (
    generate_token,
    hash_password,
    send_confirmation_email,
    send_password_reset_email,
    verify_password,
    verify_token,
)
from repositories.uow import UnitOfWork


async def register_user(user_data: UserCreate, uow: UnitOfWork) -> UserResponse:
    user_repo = uow.users

    existing_user = await user_repo.get_user_by_email(user_data.email)
    if existing_user:
        raise AlreadyRegisteredException("User with this email already exists.")

    existing_user = await user_repo.get_user_by_username(user_data.username)
    if existing_user:
        raise AlreadyRegisteredException("Username already exists.")

    hashed_password = hash_password(user_data.password)
    user_data.password = hashed_password

    role_repo = uow.roles
    role = await role_repo.get_role_by_name(RoleEnum.USER.value)
    if not role:
        raise ServerErrorException("Role not found.")

    user_data.role_id = role.id

    user = await user_repo.create(user_data)

    token = generate_token(user.id, ActionEnum.CONFIRMATION.value)
    send_confirmation_email(email=user.email, token=token)

    await uow.commit()
    return user


async def login_user(data: LoginRequest, uow: UnitOfWork, response: Response) -> TokensResponse:
    user_repo = uow.users

    user = await user_repo.get_user_by_email(data.email)
    if not user:
        raise NotFoundException("User not found.")

    if not verify_password(data.password, user.password):
        raise UnauthorizedException("Invalid email or password.")

    access_token = generate_token(user.id, ActionEnum.ACCESS.value)
    refresh_token = generate_token(user.id, ActionEnum.REFRESH.value)

    response.headers["Authorization"] = f"Bearer {access_token}"
    response.headers["Refresh-Token"] = refresh_token

    return TokensResponse(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )


async def refresh_access_token(
    refresh_token: str, uow: UnitOfWork, response: Response
) -> TokensResponse:
    try:
        user_id = verify_token(refresh_token, ActionEnum.REFRESH.value)
    except TokenExpiredException:
        raise TokenExpiredException("Token expired.")
    except InvalidTokenException:
        raise InvalidTokenException("Token invalid.")

    user_repo = uow.users
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise NotFoundException("User not found.")

    new_access_token = generate_token(user.id, ActionEnum.ACCESS.value)

    response.headers["Authorization"] = f"Bearer {new_access_token}"

    return TokensResponse(access_token=new_access_token, refresh_token=None, token_type="bearer")


async def confirm_user(token: str, uow: UnitOfWork) -> UserResponse:
    user_repo = uow.users

    user_id = verify_token(token, ActionEnum.CONFIRMATION.value)

    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise NotFoundException("User not found.")

    if user.is_approved:
        raise AlreadyConfirmedException("User already confirmed.")

    user.is_approved = True
    await uow.commit()
    return user


async def resend_confirmation_email(email: str, uow: UnitOfWork) -> dict:
    user_repo = uow.users

    user = await user_repo.get_user_by_email(email)
    if not user:
        raise NotFoundException("User not found.")

    if user.is_approved:
        raise AlreadyConfirmedException("User already confirmed.")

    token = generate_token(user.id, ActionEnum.CONFIRMATION.value)
    send_confirmation_email(email=user.email, token=token)

    return {"detail": "Confirmation email sent."}


async def request_password_reset(email: str, uow: UnitOfWork) -> dict:
    user_repo = uow.users

    user = await user_repo.get_user_by_email(email)
    if not user:
        raise NotFoundException("User not found.")

    token = generate_token(user.id, ActionEnum.RESET.value)
    send_password_reset_email(email=user.email, token=token)

    return {"detail": "Password reset email successfully sent."}


async def reset_password(token: str, new_password: str, uow: UnitOfWork) -> dict:
    user_repo = uow.users

    user_id = verify_token(token, ActionEnum.RESET.value)

    user = await user_repo.get_user_by_id(user_id)
    if not user:
        raise NotFoundException("User not found.")

    hashed_password = hash_password(new_password)
    user.password = hashed_password

    await uow.commit()
    return {"detail": "Password successfully reset."}
