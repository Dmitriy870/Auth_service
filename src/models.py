import uuid
from datetime import datetime

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr, mapped_column


class Base(DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class ModelBase:
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)


class TimeFieldBase:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.utcnow().replace(tzinfo=None)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.utcnow().replace(tzinfo=None),
        onupdate=lambda: datetime.utcnow().replace(tzinfo=None),
    )
