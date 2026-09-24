from typing import Optional

from core.common.base_dto import LinkedResource
from users.enums import UserRole


class UserProfile(LinkedResource):
    id: str
    externalId: Optional[str] = None
    name: str
    email: Optional[str] = None
    roleIds: list[UserRole]


class Me(LinkedResource):
    id: str
    name: str
    email: Optional[str] = None
    roleIds: list[str]
