from sqlalchemy.future import select

from auth import User
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
