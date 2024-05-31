from enum import Enum

class Role(Enum):
    ADMIN = 'admin'
    USER = 'user'

    @classmethod
    def choices(cls):
        return [(role.value, role.name) for role in cls]
