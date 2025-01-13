from sqlalchemy import Enum as sqlalchemy_Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models import Base
from roles.enums import RoleEnum


class Role(Base):
    name: Mapped[RoleEnum] = mapped_column(sqlalchemy_Enum(RoleEnum), nullable=False, unique=True)

    users = relationship("User", back_populates="role")

    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
    )
