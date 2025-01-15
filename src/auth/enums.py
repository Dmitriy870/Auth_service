from enum import Enum


class ActionEnum(str, Enum):
    RESET = "reset"
    CONFIRMATION = "confirmation"
    ACCESS = "access"
    REFRESH = "refresh"


class RoleEnum(str, Enum):
    ADMIN = "admin"
    USER = "user"
