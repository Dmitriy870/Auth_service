from typing import Generic, Optional, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.future import select
from sqlalchemy.orm import DeclarativeBase

ModelType = TypeVar("ModelType", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
ResponseSchemaType = TypeVar("ResponseSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType, ResponseSchemaType]):
    def __init__(self, uow, model: Type[ModelType], response_schema: Type[ResponseSchemaType]):
        self.uow = uow
        self.model = model
        self.response_schema = response_schema

    async def get_by_id(self, entity_id: UUID) -> Optional[ResponseSchemaType]:

        stmt = select(self.model).where(self.model.id == entity_id)
        result = await self.uow.execute(stmt)
        obj = result.scalars().first()
        if obj:
            return self.response_schema.model_validate(obj)
        return None

    async def get_all(self) -> list[ResponseSchemaType]:

        stmt = select(self.model)
        result = await self.uow.execute(stmt)
        return [self.response_schema.model_validate(obj) for obj in result.scalars().all()]

    async def create(self, data: CreateSchemaType) -> ResponseSchemaType:

        obj = self.model(**data.model_dump())  # Используем model_dump() вместо dict()
        self.uow.add(obj)
        await self.uow.flush()
        return self.response_schema.model_validate(obj)

    async def update(self, data: UpdateSchemaType) -> Optional[ResponseSchemaType]:

        obj = await self.get_by_id(data.id)
        if obj:
            for key, value in data.model_dump(exclude_unset=True).items():
                setattr(obj, key, value)
            await self.uow.flush()
            return self.response_schema.model_validate(obj)
        return None

    async def delete(self, entity_id: UUID) -> bool:

        obj = await self.get_by_id(entity_id)
        if obj:
            await self.uow.delete(obj)
            await self.uow.flush()
            return True
        return False
