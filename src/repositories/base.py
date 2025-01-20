from typing import Generic, Optional, Type, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import asc, desc, func
from sqlalchemy.future import select
from sqlalchemy.orm import DeclarativeBase

from auth.exceptions import NotFoundException

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
            return self.response_schema.model_validate(obj, from_attributes=True)
        return None

    async def get_all(self) -> list[ResponseSchemaType]:

        stmt = select(self.model)
        result = await self.uow.execute(stmt)

        return [
            self.response_schema.model_validate(obj, from_attributes=True)
            for obj in result.scalars().unique().all()
        ]

    async def get_all_paginated(
        self,
        page: int,
        page_size: int,
        sort_by: str | None,
        order: str | None,
        role: str | None,
    ) -> list[ResponseSchemaType]:
        stmt = select(self.model)

        if role:
            stmt = stmt.where(self.model.role.has(name=role))

        if sort_by:
            sort_column = getattr(self.model, sort_by, None)
            if sort_column is not None:
                stmt = stmt.order_by(asc(sort_column) if order == "asc" else desc(sort_column))

        offset = (page - 1) * page_size
        stmt = stmt.offset(offset).limit(page_size)

        result = await self.uow.execute(stmt)
        users = [
            self.response_schema.model_validate(obj, from_attributes=True)
            for obj in result.scalars().unique().all()
        ]

        total_stmt = select(func.count(self.model.id))
        if role:
            total_stmt = total_stmt.where(self.model.role.has(name=role))
        total_result = await self.uow.execute(total_stmt)
        total = total_result.scalar_one()

        return users, total

    async def create(self, data: CreateSchemaType) -> ResponseSchemaType:

        obj = self.model(**data.model_dump())
        self.uow.add(obj)
        await self.uow.flush()
        return self.response_schema.model_validate(obj, from_attributes=True)

    async def update(
        self, data: UpdateSchemaType, entity_id: UUID | None = None
    ) -> Optional[ResponseSchemaType]:

        target_id = entity_id if entity_id else data.id
        stmt = select(self.model).where(self.model.id == target_id)
        result = await self.uow.execute(stmt)
        obj = result.scalars().first()

        if not obj:
            raise NotFoundException("Entity not found")

        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(obj, key, value)

        await self.uow.flush()

        return self.response_schema.model_validate(obj, from_attributes=True)

    async def delete(self, entity_id: UUID) -> ResponseSchemaType:

        stmt = select(self.model).where(self.model.id == entity_id)
        result = await self.uow.execute(stmt)
        obj = result.scalars().first()

        if not obj:
            raise NotFoundException(f"Entity with id {entity_id} not found.")

        await self.uow.delete(obj)
        await self.uow.flush()
        return self.response_schema.model_validate(obj, from_attributes=True)
