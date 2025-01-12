from typing import TYPE_CHECKING

from sqlalchemy import Enum as sqlalchemy_Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base
from roles.enums import RoleEnum

if TYPE_CHECKING:
    from user_permissions import RolePermission
    from users import User


class Role(Base):
    name: Mapped[RoleEnum] = mapped_column(sqlalchemy_Enum(RoleEnum), nullable=False, unique=True)

    users: Mapped["User"] = relationship(back_populates="role")
    role_permissions: Mapped["RolePermission"] = relationship(back_populates="role")
