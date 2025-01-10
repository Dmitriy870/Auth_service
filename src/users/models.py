import uuid

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing_extensions import TYPE_CHECKING

from models import Base

if TYPE_CHECKING:
    from permissions.models import UserPermission
    from roles.models import Role


class User(Base):

    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("role.id"), nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_globally_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blocked_by: Mapped[uuid.UUID | None] = mapped_column(default=None, nullable=True)

    role: Mapped["Role"] = relationship(back_populates="users")
    permissions: Mapped["UserPermission"] = relationship(back_populates="user")
