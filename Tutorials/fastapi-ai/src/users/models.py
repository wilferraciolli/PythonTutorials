from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from core.security.roles import UserRole


class UserModel(BaseModel):
    """A `user_detail_view` row: a user plus their roles."""
    id: str
    external_user_id: Optional[str] = None
    name: str
    email: str
    created_date: datetime
    role_ids: list[UserRole]
