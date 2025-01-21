import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

import bcrypt
import jwt
from cryptography.fernet import Fernet

from auth.exceptions import InvalidTokenException, TokenExpiredException
from auth.schemas import TokensResponse
from config import BasicConfig, EncryptionConfig, JWTConfig
from send_email import send_email

encryption_config = EncryptionConfig()
jwt_config = JWTConfig()
basic_config = BasicConfig()
fernet = Fernet(encryption_config.KEY)


def hash_password(password: str) -> str:
    """Hashes a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode(), salt)
    return hashed.decode()


def verify_password(password: str, hashed_password: str) -> bool:
    """Verifies a password by comparing it with the stored hash."""
    return bcrypt.checkpw(password.encode(), hashed_password.encode())


def generate_tokens(user_id: UUID, role: str, only_access: bool = False) -> TokensResponse:
    """Generates access and refresh tokens."""
    access_token_payload = {
        "user_id": str(user_id),
        "exp": datetime.now(UTC) + timedelta(minutes=jwt_config.ACCESS_TOKEN_EXPIRE_MINUTES),
        "role": role,
    }
    access_token = jwt.encode(
        access_token_payload, jwt_config.SECRET_KEY, algorithm=jwt_config.ALGORITHM
    )

    refresh_token_payload = {
        "user_id": str(user_id),
        "exp": datetime.now(UTC) + timedelta(minutes=jwt_config.REFRESH_TOKEN_EXPIRE),
        "role": role,
    }
    refresh_token = jwt.encode(
        refresh_token_payload, jwt_config.SECRET_KEY, algorithm=jwt_config.ALGORITHM
    )

    return TokensResponse(
        access_token=access_token,
        refresh_token=refresh_token if not only_access else None,
        token_type="bearer",
        role=role,
    )


def verify_token(token: str) -> UUID:
    """Verifies and decodes a token."""
    try:
        payload = jwt.decode(token, jwt_config.SECRET_KEY, algorithms=[jwt_config.ALGORITHM])
        return UUID(payload["user_id"])
    except jwt.ExpiredSignatureError:
        raise TokenExpiredException("Token has expired")
    except jwt.InvalidTokenError:
        raise InvalidTokenException("Invalid token")


def send_confirmation_email(email: str | list[str], code: str, encrypted_user_id: str):
    """Sends an email for email confirmation."""
    url = f"{basic_config.URL}/confirm-email?code={code}&user_id={encrypted_user_id}"
    subject = "Email Confirmation"
    body = f"Click the link to confirm your email: {url}"
    send_email(subject=subject, body=body, recipients=email)


def send_password_reset_email(email: str | list[str], code: str, encrypted_user_id: str):
    """Sends an email for password reset."""
    url = f"{basic_config.URL}/reset-password/confirm?code={code}&user_id={encrypted_user_id}"
    subject = "Password Reset"
    body = f"Click the link to reset your password: {url}"
    send_email(subject=subject, body=body, recipients=email)


def generate_code() -> str:
    return str(uuid.uuid4())


def encrypt_user_id(user_id: str) -> str:
    return fernet.encrypt(user_id.encode()).decode()


def decrypt_user_id(encrypted_user_id: str) -> str:
    return fernet.decrypt(encrypted_user_id.encode()).decode()
