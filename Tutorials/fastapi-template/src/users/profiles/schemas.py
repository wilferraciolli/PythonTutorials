from typing import Optional

from core.common.base_dto import LinkedResource
from core.security.roles import UserRole


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
