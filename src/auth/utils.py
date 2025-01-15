from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
import jwt

from auth.exceptions import (
    InvalidActionException,
    InvalidTokenException,
    TokenExpiredException,
)
from config import BasicConfig, JWTConfig
from send_email import send_email

jwt_config = JWTConfig()
basic_config = BasicConfig()


def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a password by comparing it with the stored hash."""
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def generate_token(user_id: UUID, action: str) -> str:
    """Generates a token for a specific action using HS256."""
    payload = {
        "user_id": str(user_id),
        "action": action,
        "exp": datetime.now(UTC) + timedelta(minutes=jwt_config.ACCESS_TOKEN_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, jwt_config.SECRET_KEY, algorithm=jwt_config.ALGORITHM)


def verify_token(token: str, action: str) -> UUID:
    """Verifies and decodes a token for a specific action using HS256."""
    try:
        payload = jwt.decode(token, jwt_config.SECRET_KEY, algorithms=[jwt_config.ALGORITHM])
        if payload["action"] != action:
            raise InvalidActionException("Invalid action in token")
        return UUID(payload["user_id"])
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException("Token has expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenException("Invalid token")


def send_confirmation_email(email: str | list[str], token: str):
    """Sends an email for email confirmation."""
    url = f"{basic_config.URL}/confirm-email?token={token}"
    subject = "Email Confirmation"
    body = f"Click the link to confirm your email: {url}"
    send_email(subject=subject, body=body, recipients=email)


def send_password_reset_email(email: str | list[str], token: str):
    """Sends an email for password reset."""
    url = f"{basic_config.URL}/reset-password/confirm?token={token}"
    subject = "Password Reset"
    body = f"Click the link to reset your password: {url}"
    send_email(subject=subject, body=body, recipients=email)
