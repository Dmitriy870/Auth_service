from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
import jwt

from config import AppConfig
from send_email import send_email
from users.enums import ActionEnum
from users.exceptions import ActionException, TokenException

config = AppConfig()


def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a password by comparing it with the stored hash."""
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def generate_token(user_id: UUID, action: str, expire_minutes: int) -> str:
    """Generates a token for a specific action (email confirmation or password reset)."""
    payload = {
        "user_id": str(user_id),
        "action": action,
        "exp": datetime.now(UTC) + timedelta(minutes=expire_minutes),
    }
    return jwt.encode(payload, config.jwt.secret_key, algorithm=config.jwt.algorithm)


def verify_token(token: str, action: str) -> UUID:
    """Verifies and decodes a token for a specific action."""
    try:
        payload = jwt.decode(token, config.jwt.secret_key, algorithms=[config.jwt.algorithm])
        if payload["action"] != action:
            raise ActionException.invalid_action
        return UUID(payload["user_id"])
    except jwt.ExpiredSignatureError:
        raise TokenException.token_expired_exception
    except jwt.InvalidTokenError:
        raise TokenException.invalid_token


def send_action_email(email: str | list[str], token: str, action: str):
    """
    Sends an email for a specific action.
    """
    base_url = config.basic.url
    if action == ActionEnum.CONFIRMATION.value:
        url = f"{base_url}/confirm-email?token={token}"
        subject = "Email Confirmation"
        body = f"Click the link to confirm your email: {url}"
    elif action == ActionEnum.RESET.value:
        url = f"{base_url}/reset-password?token={token}"
        subject = "Password Reset"
        body = f"Click the link to reset your password: {url}"
    else:
        raise ValueError("Invalid action. Use 'confirmation' or 'reset'.")

    send_email(subject=subject, body=body, recipients=email)
