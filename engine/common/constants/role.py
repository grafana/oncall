from enum import IntEnum


class Role(IntEnum):
    ADMIN = 0
    EDITOR = 1
    VIEWER = 2

    @classmethod
    def choices(cls):
        return tuple((option.value, option.name) for option in cls)
