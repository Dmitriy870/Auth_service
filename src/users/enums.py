from enum import Enum


class ActionEnum(str, Enum):
    RESET = "reset"
    CONFIRMATION = "confirmation"


class ExpireTimeEnum(int, Enum):
    RESET = 15
    CONFIRMATION = 60
