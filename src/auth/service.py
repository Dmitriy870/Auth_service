import logging
from uuid import UUID

import httpx
from cryptography.fernet import InvalidToken
from dependency_injector.wiring import Provide, inject
from redis.asyncio import Redis

from auth.enums import RoleEnum
from auth.exceptions import (
    AlreadyConfirmedException,
    AlreadyRegisteredException,
    ErrorCallingFileService,
    InvalidTokenException,
    NotFoundException,
    ServerErrorException,
    TokenExpiredException,
    UnauthorizedException,
)
from auth.logging_conf import configurate_logging
from auth.schemas import (
    LoginRequest,
    TokensResponse,
    UserConfirm,
    UserCreate,
    UserResponse,
    UserResponseWithRoleName,
    UserUpdate,
    UserUpdatePassword,
)
from auth.utils import (
    decrypt_user_id,
    encrypt_user_id,
    generate_code,
    generate_tokens,
    hash_password,
    send_confirmation_email,
    send_password_reset_email,
    verify_password,
    verify_token,
)
from config import VersionConfig
from containers.version_config import VersionContainer
from repositories.uow import UnitOfWork

logger = configurate_logging(logging.INFO)


class UserService:
    def __init__(self, uow: UnitOfWork, redis_client: Redis):
        self.uow = uow
        self.redis_client = redis_client

    async def register_user(self, user_data: UserCreate) -> UserResponse:
        existing_user = await self.uow.users.get_user_by_email(user_data.email)
        if existing_user:
            raise AlreadyRegisteredException("User with this email already exists.")

        existing_user = await self.uow.users.get_user_by_username(user_data.username)
        if existing_user:
            raise AlreadyRegisteredException("Username already exists.")

        hashed_password = hash_password(user_data.password)
        user_data.password = hashed_password

        role = await self.uow.roles.get_role_by_name(RoleEnum.USER.value)
        if not role:
            raise ServerErrorException("Role not found.")

        user_data.role_id = role.id
        user = await self.uow.users.create(user_data)

        code = generate_code()
        encrypted_user_id = encrypt_user_id(str(user.id))

        send_confirmation_email(
            email=user.email,
            code=code,
            encrypted_user_id=encrypted_user_id,
        )
        await self.redis_client.set(f"ecnfrm: {code}", str(user.id), ex=900)
        await self.uow.commit()

        return user

    async def login_user(self, data: LoginRequest) -> TokensResponse:
        logger.info("login user")
        user = await self.uow.users.get_user_by_email(data.email)
        if not user:
            raise NotFoundException("User not found.")
        if not verify_password(data.password, user.password):
            raise UnauthorizedException("Invalid email or password.")

        role = await self.uow.roles.get_role_by_id(user.role_id)
        tokens = generate_tokens(user.id, role.name)

        return tokens

    async def refresh_access_token(self, refresh_token: str) -> TokensResponse:
        try:
            user_id = verify_token(refresh_token)
        except TokenExpiredException:
            raise TokenExpiredException("Refresh token has expired.")
        except InvalidTokenException:
            raise InvalidTokenException("Invalid refresh token.")
        user = await self.uow.users.get_by_id(user_id)
        role = await self.uow.roles.get_role_by_id(user.role_id)

        tokens = generate_tokens(user_id, role.name, True)
        return tokens

    async def confirm_user(self, code: str, encrypted_user_id: str) -> UserResponse:
        try:
            user_id_from_query = decrypt_user_id(encrypted_user_id)
        except InvalidToken:
            raise UnauthorizedException("Invalid user identifier.")
        except ValueError:
            raise UnauthorizedException("Malformed user identifier.")

        user_id_from_redis = await self.redis_client.get(f"ecnfrm: {code}")
        if not user_id_from_redis:
            raise UnauthorizedException("Invalid or expired confirmation code.")
        if user_id_from_redis != str(user_id_from_query):
            raise UnauthorizedException("Invalid user identifier.")

        user_confirm = UserConfirm(id=user_id_from_query, is_approved=True)
        user = await self.uow.users.update(user_confirm)

        await self.uow.commit()
        await self.redis_client.delete(f"ecnfrm: {code}")

        return user

    async def resend_confirmation_email(self, email: str) -> dict:
        user = await self.uow.users.get_user_by_email(email)
        if not user:
            raise NotFoundException("User not found.")

        if user.is_approved:
            raise AlreadyConfirmedException("User already confirmed.")

        code = generate_code()
        encrypted_user_id = encrypt_user_id(str(user.id))

        send_confirmation_email(
            email=user.email,
            code=code,
            encrypted_user_id=encrypted_user_id,
        )
        await self.redis_client.set(f"ecnfrm: {code}", str(user.id), ex=900)

        return {"detail": "Confirmation email sent."}

    async def request_password_reset(self, email: str) -> dict:
        user = await self.uow.users.get_user_by_email(email)
        if not user:
            raise NotFoundException("User not found.")

        code = generate_code()
        encrypted_user_id = encrypt_user_id(str(user.id))

        send_password_reset_email(
            email=user.email,
            code=code,
            encrypted_user_id=encrypted_user_id,
        )
        await self.redis_client.set(f"password_reset: {code}", str(user.id), ex=900)

        return {"detail": "Password reset email successfully sent."}

    async def reset_password(self, code: str, new_password: str, encrypted_user_id: str) -> dict:
        try:
            user_id_from_query = decrypt_user_id(encrypted_user_id)
        except InvalidToken:
            raise UnauthorizedException("Invalid user identifier.")
        except ValueError:
            raise UnauthorizedException("Malformed user identifier.")

        user_id_from_redis = await self.redis_client.get(f"password_reset: {code}")
        if not user_id_from_redis:
            raise UnauthorizedException("Invalid or expired reset code.")

        if str(user_id_from_redis) != str(user_id_from_query):
            raise UnauthorizedException("Invalid user identifier.")

        hashed_password = hash_password(new_password)
        update_pass = UserUpdatePassword(id=user_id_from_query, password=hashed_password)

        await self.uow.users.update(update_pass)
        await self.redis_client.delete(f"password_reset: {code}")
        await self.uow.session.commit()

        return {"detail": "Password successfully reset."}

    async def get_all_user(
        self,
        page: int,
        page_size: int,
        sort_by: str | None,
        order: str | None,
        role: str | None,
    ):
        users, total = await self.uow.users.get_all_paginated(page, page_size, sort_by, order, role)

        return {
            "users": users,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total // page_size) + (1 if total % page_size > 0 else 0),
        }

    async def update_user(self, data: UserUpdate, user_id: UUID):
        if data.email:
            check_email = await self.uow.users.get_user_by_email(data.email)
            if check_email:
                raise AlreadyRegisteredException("User with this email already exists.")

        user = await self.uow.users.get_by_id(user_id)
        if user is None:
            raise NotFoundException("User not found.")

        email_db = user.email
        user_update: UserUpdate = await self.uow.users.update(data, user_id)

        if data.email and data.email.strip().lower() != email_db.strip().lower():
            code = generate_code()
            encrypted_user_id = encrypt_user_id(str(user.id))

            send_confirmation_email(
                email=user_update.email,
                code=code,
                encrypted_user_id=encrypted_user_id,
            )
            user_update = await self.uow.users.set_false_email(user_id)
            await self.redis_client.set(f"ecnfrm: {code}", str(user_id), ex=900)

        return user_update

    async def get_me(self, current_user):
        role_id = current_user.role_id
        role = await self.uow.roles.get_role_by_id(role_id)
        role_name = role.name
        user_with_role = UserResponseWithRoleName(**current_user.model_dump(), role=role_name)
        return user_with_role

    @inject
    async def load_file(
        self,
        user_id,
        file,
        version_config: VersionConfig = Provide[VersionContainer.version_config],
    ) -> dict:
        try:
            async with httpx.AsyncClient() as client:
                files = {"file": (file.filename, file.file, file.content_type)}
                response = await client.post(version_config.FILE_URL_POST, files=files)
            if response.status_code != 200:
                raise ErrorCallingFileService("Error calling file service")
            data = response.json()
            slug = data["slug"]
            old_file_slug = await self.uow.users.check_avatar(user_id)
            await self.uow.users.insert_slug(user_id, slug)
            if old_file_slug:
                try:
                    async with httpx.AsyncClient() as client:
                        delete_url = f"{version_config.FILE_URL_DELETE}{old_file_slug}"
                        await client.delete(delete_url)
                except httpx.RequestError as e:
                    logger.error(f"Network error when deleting old avatar: {str(e)}")
                return {
                    "message": "Start loading,old avatar was successfully deleted",
                    "slug_of_file": slug,
                }
            return {"message": "Start loading", "slug_of_file": slug}

        except httpx.RequestError as e:
            logger.error(f"Network error when calling the file service: {str(e)}")
            raise ErrorCallingFileService("The file service is unavailable")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error {e.response.status_code} from the file service")
            raise ErrorCallingFileService(f"File service error: {e.response.status_code}")

        except ValueError as e:
            logger.error(f"Invalid JSON response from the file service: {str(e)}")
            raise ErrorCallingFileService("Invalid response from the file service")
