from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from roles.enums import RoleEnum
from roles.models import Role
from users.enums import ActionEnum, ExpireTimeEnum
from users.exceptions import UserHTTPException
from users.models import User
from users.schemas import UserCreate, UserResponse
from users.utils import generate_token, hash_password, send_action_email, verify_token


async def register_user(user_data: UserCreate, session: AsyncSession) -> UserResponse:
    """
    Registers a new user and sends a confirmation email.
    """
    try:
        stmt = select(User).where(User.email == user_data.email)
        result = await session.execute(stmt)
        db_user = result.scalars().first()

        if db_user:
            raise UserHTTPException.email_already_registered

        hashed_password = hash_password(user_data.password)

        stmt = select(Role).where(Role.name == RoleEnum.USER.value)
        result = await session.execute(stmt)
        role: Role = result.scalars().first()

        user: User = User(
            username=user_data.username.strip(),
            email=user_data.email,
            password=hashed_password,
            role_id=role.id,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        token = generate_token(
            user.id, ActionEnum.CONFIRMATION.value, ExpireTimeEnum.CONFIRMATION.value
        )
        send_action_email(
            email=user.email,
            token=token,
            action=ActionEnum.CONFIRMATION.value,
        )

        return UserResponse.model_validate(user)

    except NoResultFound:
        raise UserHTTPException.server_error


async def confirm_user(
    token: str,
    session: AsyncSession,
) -> UserResponse:
    """
    Confirms a user using the provided token.
    """
    user_id = verify_token(token, ActionEnum.CONFIRMATION.value)
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user: User = result.scalars().first()

    if not user:
        raise UserHTTPException.user_not_found

    if user.is_approved:
        raise UserHTTPException.user_already_confirmed

    user.is_approved = True
    await session.commit()
    return UserResponse.model_validate(user)


async def resend_confirmation_email(email: str, session: AsyncSession) -> dict:
    """
    Resends a confirmation email to the user.
    """
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user: User = result.scalars().first()

    if not user:
        raise UserHTTPException.user_not_found

    if user.is_approved:
        raise UserHTTPException.user_already_confirmed

    token = generate_token(
        user.id, ActionEnum.CONFIRMATION.value, ExpireTimeEnum.CONFIRMATION.value
    )
    send_action_email(
        email=user.email,
        token=token,
        action=ActionEnum.CONFIRMATION.value,
    )

    return {"detail": "Confirmation email sent."}


async def request_password_reset(email: str, session: AsyncSession) -> dict:
    """
    Sends a password reset email to the user.
    """
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user: User = result.scalars().first()

    if not user:
        raise UserHTTPException.user_not_found

    token = generate_token(user.id, ActionEnum.RESET.value, ExpireTimeEnum.RESET.value)
    send_action_email(
        email=user.email,
        token=token,
        action=ActionEnum.RESET.value,
    )

    return {"detail": "Password reset email successfully sent."}


async def reset_password(token: str, new_password: str, session: AsyncSession) -> dict:
    """
    Resets the user's password using the provided token.
    """
    user_id = verify_token(token, ActionEnum.RESET.value)

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user: User = result.scalars().first()

    if not user:
        raise UserHTTPException.user_not_found

    hashed_password = hash_password(new_password)
    user.password = hashed_password
    await session.commit()

    return {"detail": "Password successfully reset."}
