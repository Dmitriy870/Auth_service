from sqlalchemy.ext.asyncio import AsyncSession

from repositories.role_repository import RoleRepository
from repositories.user_repository import UserRepository


class UnitOfWork:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self.users: UserRepository
        self.roles: RoleRepository

    @property
    def session(self) -> AsyncSession:
        return self._session

    async def __aenter__(self) -> "UnitOfWork":
        self.users = UserRepository(self._session)
        self.roles = RoleRepository(self._session)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if exc_type:
            await self.rollback()
        else:
            await self.commit()

    async def commit(self):
        await self._session.commit()

    async def rollback(self):
        await self._session.rollback()
