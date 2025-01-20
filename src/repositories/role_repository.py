from sqlalchemy.future import select

from auth import Role
from auth.schemas import RoleResponse
from repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role, None, None, RoleResponse]):
    def __init__(self, uow):
        super().__init__(uow, Role, RoleResponse)

    async def get_role_by_name(self, name: str) -> RoleResponse | None:
        stmt = select(self.model).where(self.model.name == name)
        result = await self.uow.execute(stmt)
        role = result.scalars().first()
        if role:
            return self.response_schema.model_validate(role, from_attributes=True)
        return None
