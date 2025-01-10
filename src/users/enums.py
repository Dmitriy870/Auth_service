from enum import Enum


class ActionEnum(str, Enum):
    RESET = "reset"
    CONFIRMATION = "confirmation"


class Expire_time_Enum(int, Enum):
    RESET = 15
    CONFIRMATION = 60
