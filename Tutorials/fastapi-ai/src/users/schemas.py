from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from core.common.base_dto import LinkedResource
from core.common.serializers import format_utc_datetime
from core.security.roles import UserRole


class UserCreate(BaseModel):
    name: str
    email: str
    roleIds: Optional[list[UserRole]] = Field(default_factory=lambda: [UserRole.STANDARD])


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    roleIds: Optional[list[UserRole]] = None


class User(LinkedResource):
    id: str
    external_user_id: Optional[str] = None
    name: str
    email: str
    roleIds: list[UserRole]
    created_date: datetime

    @field_serializer("created_date")
    def serialize_created_date(self, value: datetime) -> str:
        return format_utc_datetime(value)
