from enum import Enum


class TimelineType(str, Enum):
    ALL = "ALL"
    FOLLOWING = "FOLLOWING"
    POPULAR = "POPULAR"
