from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Enum as sqlalchemy_Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base

if TYPE_CHECKING:
    from permissions.models import RolePermission
    from users.models import User


class RoleEnum(str, Enum):
    ADMIN = "admin"
    USER = "user"


class Role(Base):
    name: Mapped[RoleEnum] = mapped_column(sqlalchemy_Enum(RoleEnum), nullable=False, unique=True)

    users: Mapped["User"] = relationship(back_populates="role")
    role_permissions: Mapped["RolePermission"] = relationship(back_populates="role")
