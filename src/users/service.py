from sqlalchemy.exc import NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from roles.enums import RoleEnum
from roles.models import Role
from users.exceptions import (
    AlreadyConfirmedException,
    AlreadyRegisteredException,
    NotFoundException,
    ServerErrorException,
)
from users.models import User
from users.schemas import UserCreate, UserResponse
from users.utils import (
    generate_token,
    hash_password,
    send_confirmation_email,
    send_password_reset_email,
    verify_token,
)


async def register_user(user_data: UserCreate, session: AsyncSession) -> UserResponse:
    """
    Registers a new user and sends a confirmation email.
    """
    try:
        stmt = select(User).where(User.email == user_data.email)
        result = await session.execute(stmt)
        db_user = result.scalars().first()

        if db_user:
            raise AlreadyRegisteredException("User with this email already exists.")

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

        token = generate_token(user.id, "confirmation")
        send_confirmation_email(email=user.email, token=token)

        return UserResponse.model_validate(user)

    except NoResultFound:
        raise ServerErrorException("An error occurred while registering the user.")


async def confirm_user(token: str, session: AsyncSession) -> UserResponse:
    """
    Confirms a user using the provided token.
    """
    user_id = verify_token(token, "confirmation")
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user: User = result.scalars().first()

    if not user:
        raise NotFoundException("User not found.")

    if user.is_approved:
        raise AlreadyConfirmedException("User already confirmed.")

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
        raise NotFoundException("User not found.")

    if user.is_approved:
        raise AlreadyConfirmedException("User already confirmed.")

    token = generate_token(user.id, "confirmation")
    send_confirmation_email(email=user.email, token=token)

    return {"detail": "Confirmation email sent."}


async def request_password_reset(email: str, session: AsyncSession) -> dict:
    """
    Sends a password reset email to the user.
    """
    stmt = select(User).where(User.email == email)
    result = await session.execute(stmt)
    user: User = result.scalars().first()

    if not user:
        raise NotFoundException("User not found.")

    token = generate_token(user.id, "reset")
    send_password_reset_email(email=user.email, token=token)

    return {"detail": "Password reset email successfully sent."}


async def reset_password(token: str, new_password: str, session: AsyncSession) -> dict:
    """
    Resets the user's password using the provided token.
    """
    user_id = verify_token(token, "reset")

    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user: User = result.scalars().first()

    if not user:
        raise NotFoundException("User not found.")

    hashed_password = hash_password(new_password)
    user.password = hashed_password
    await session.commit()

    return {"detail": "Password successfully reset."}
