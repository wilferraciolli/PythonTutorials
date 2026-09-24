from enum import Enum


class TodoState(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"
