from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from core.common.base_dto import LinkedResource
from core.common.serializers import format_utc_datetime
from groups.enums import GroupVisibility


class GroupCreate(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=500)
    visibility: GroupVisibility = GroupVisibility.PUBLIC


class GroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=500)
    visibility: Optional[GroupVisibility] = None


class GroupOwnerUpdate(BaseModel):
    userId: str = Field(min_length=1)


class Group(LinkedResource):
    id: str
    name: str
    description: Optional[str] = None
    visibility: GroupVisibility
    ownerId: Optional[str] = None
    createdBy: Optional[str] = None
    created_date: datetime
    memberCount: int = 0
    followerCount: int = 0
    isOwner: bool = False
    isMember: bool = False
    isFollowing: bool = False

    @field_serializer("created_date")
    def serialize_group_created_date(self, value: datetime) -> str:
        return format_utc_datetime(value)


class GroupMember(LinkedResource):
    userId: str
    name: Optional[str] = None
    isOwner: bool = False
    joined_date: datetime

    @field_serializer("joined_date")
    def serialize_joined_date(self, value: datetime) -> str:
        return format_utc_datetime(value)


class GroupFollower(BaseModel):
    userId: str
    name: Optional[str] = None
    created_date: datetime

    @field_serializer("created_date")
    def serialize_follower_created_date(self, value: datetime) -> str:
        return format_utc_datetime(value)
