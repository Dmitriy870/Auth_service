from pydantic import EmailStr
from sqlalchemy.future import select

from auth import Role, User
from auth.enums import RoleEnum
from auth.exceptions import InvalidRoleException, NotFoundException
from auth.schemas import UserCreate, UserResponse, UserUpdate
from repositories.base import BaseRepository


class UserRepository(BaseRepository[User, UserCreate, UserUpdate, UserResponse]):

    def __init__(self, uow):
        super().__init__(uow, User, UserResponse)

    async def get_user_by_email(self, email: str) -> UserResponse | None:

        stmt = select(self.model).where(self.model.email == email)
        result = await self.uow.execute(stmt)
        user: User = result.scalars().first()
        if user:
            return self.response_schema.model_validate(user)
        return None

    async def get_user_by_username(self, username: str) -> UserResponse | None:
        stmt = select(self.model).where(self.model.username == username)
        result = await self.uow.execute(stmt)
        user: User = result.scalars().first()
        if user:
            return self.response_schema.model_validate(user)
        return None

    async def update_user_role(self, email: EmailStr, role: str) -> UserResponse | None:
        stmt = select(self.model).where(self.model.email == email)
        result = await self.uow.execute(stmt)
        user: User = result.scalars().first()

        if not user:
            raise NotFoundException("User not found")
        try:
            valid_role_enum = RoleEnum(role)
        except ValueError:
            raise InvalidRoleException(
                f"Invalid role. Valid roles are: {[r.value for r in RoleEnum]}"
            )

        role_stmt = select(Role).where(Role.name == valid_role_enum.value)
        role_result = await self.uow.execute(role_stmt)
        role_obj = role_result.scalars().first()

        if not role_obj:
            raise InvalidRoleException
        user.role = role_obj
        await self.uow.flush()

        return self.response_schema.model_validate(user)
