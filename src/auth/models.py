import uuid

from sqlalchemy import Boolean
from sqlalchemy import Enum as sqlalchemy_Enum
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from auth.enums import RoleEnum
from models import Base, ModelBase, TimeFieldBase


class Role(ModelBase, TimeFieldBase, Base):
    name: Mapped[RoleEnum] = mapped_column(sqlalchemy_Enum(RoleEnum), nullable=False, unique=True)

    users = relationship("User", back_populates="role", lazy="selectin")

    permissions = relationship(
        "Permission",
        secondary="role_permissions",
        back_populates="roles",
        lazy="joined",
    )


class User(ModelBase, TimeFieldBase, Base):
    username: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password: Mapped[str] = mapped_column(String, nullable=False)
    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("role.id"), nullable=False)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_globally_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blocked_by: Mapped[uuid.UUID | None] = mapped_column(default=None, nullable=True)

    role = relationship("Role", back_populates="users", lazy="joined")

    permissions = relationship(
        "Permission",
        secondary="user_permissions",
        back_populates="users",
        lazy="joined",
    )


class Permission(ModelBase, TimeFieldBase, Base):
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    roles = relationship(
        "Role",
        secondary="role_permissions",
        back_populates="permissions",
        lazy="joined",
    )

    users = relationship(
        "User",
        secondary="user_permissions",
        back_populates="permissions",
        lazy="selectin",
    )


class RolePermission(TimeFieldBase, Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("role.id"), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("permission.id"), primary_key=True)


class UserPermission(TimeFieldBase, Base):
    __tablename__ = "user_permissions"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("user.id"), primary_key=True)
    permission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("permission.id"), primary_key=True)
