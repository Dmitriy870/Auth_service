from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from auth.enums import ActionEnum
from auth.exceptions import (
    InvalidTokenException,
    NotFoundException,
    TokenExpiredException,
    UnauthorizedException,
)
from auth.schemas import UserResponse
from auth.utils import verify_token
from database import get_unit_of_work
from repositories.uow import UnitOfWork

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    uow: UnitOfWork = Depends(get_unit_of_work),
) -> UserResponse:
    token = credentials.credentials
    try:
        user_id = verify_token(token, ActionEnum.ACCESS.value)
    except (InvalidTokenException, TokenExpiredException):
        raise UnauthorizedException("Unauthorized")

    user = await uow.users.get_by_id(user_id)
    if not user:
        raise NotFoundException("User not found")

    return user
