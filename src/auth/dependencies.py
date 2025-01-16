from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.asyncio import Redis

from auth.enums import RoleEnum
from auth.exceptions import (
    InvalidOrExpiredTokenException,
    InvalidTokenException,
    PermissionDeniedException,
    TokenExpiredException,
    UnauthorizedException,
)
from auth.schemas import UserResponse
from auth.service import UserService
from auth.utils import verify_token
from config import RedisConfig
from database import get_unit_of_work
from repositories.uow import UnitOfWork

redis_config = RedisConfig()

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> UserResponse:
    token = credentials.credentials
    try:
        user_id = verify_token(token)
    except (InvalidTokenException, TokenExpiredException):
        raise InvalidOrExpiredTokenException

    user = await uow.users.get_by_id(user_id)
    if not user:
        raise UnauthorizedException("Unauthorized(user)")
    return user


CurrentUser = Annotated[UserResponse, Depends(get_current_user)]


async def get_current_admin(current_user: CurrentUser, uow: UnitOfWork = Depends(get_unit_of_work)):
    role = await uow.roles.get_by_id(current_user.role_id)
    if role.name != RoleEnum.ADMIN:
        raise PermissionDeniedException("Permission denied, you do not have admin role.")
    return current_user


CurrentAdmin = Annotated[UserResponse, Depends(get_current_admin)]


async def get_user_service(uow: UnitOfWork = Depends(get_unit_of_work)) -> UserService:
    return UserService(uow)


async def get_redis_client() -> Redis:
    client = Redis.from_url(str(redis_config.URL), decode_responses=True)
    try:
        yield client
    finally:
        await client.close()
