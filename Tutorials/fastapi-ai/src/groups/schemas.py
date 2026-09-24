from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from core.common.api_response import ApiResponse
from core.common.base_dto import FieldMetadata, LinkedResource, NoMetadata
from core.common.serializers import format_utc_datetime
from groups.constants import DESCRIPTION_MAX_LENGTH, NAME_MAX_LENGTH
from groups.enums import GroupVisibility


# --- Request: what the client sends -----------------------------------------

class GroupCreateRequest(BaseModel):
    """Body of `POST /groups`."""
    name: str = Field(min_length=1, max_length=NAME_MAX_LENGTH)
    description: Optional[str] = Field(None, max_length=DESCRIPTION_MAX_LENGTH)
    visibility: GroupVisibility = GroupVisibility.PUBLIC


class GroupUpdateRequest(BaseModel):
    """Body of `PUT /groups/{group_id}`. Only the fields sent are changed."""
    name: Optional[str] = Field(None, min_length=1, max_length=NAME_MAX_LENGTH)
    description: Optional[str] = Field(None, max_length=DESCRIPTION_MAX_LENGTH)
    visibility: Optional[GroupVisibility] = None


class GroupOwnerUpdateRequest(BaseModel):
    """Body of `PUT /groups/{group_id}/owner`."""
    userId: str = Field(min_length=1)


# --- DTO: what the application service returns ------------------------------

class GroupDTO(LinkedResource):
    """A group, the caller's place in it, and the links they may follow."""
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
    def serialize_created_date(self, value: datetime) -> str:
        return format_utc_datetime(value)


class GroupMemberDTO(LinkedResource):
    """A member of a group, with what the caller may do to them."""
    userId: str
    name: Optional[str] = None
    isOwner: bool = False
    joined_date: datetime

    @field_serializer("joined_date")
    def serialize_joined_date(self, value: datetime) -> str:
        return format_utc_datetime(value)


class GroupFollowerDTO(BaseModel):
    """Someone following a group."""
    userId: str
    name: Optional[str] = None
    created_date: datetime

    @field_serializer("created_date")
    def serialize_created_date(self, value: datetime) -> str:
        return format_utc_datetime(value)


class GroupMetadata(BaseModel):
    """How the client should treat the fields of `GroupDTO`."""
    name: FieldMetadata
    visibility: FieldMetadata
    ownerId: FieldMetadata


# --- Response: the envelopes the service builds -----------------------------

GroupResponse = ApiResponse[GroupDTO, GroupMetadata]
GroupListResponse = ApiResponse[list[GroupDTO], GroupMetadata]
GroupMemberListResponse = ApiResponse[list[GroupMemberDTO], NoMetadata]
GroupFollowerListResponse = ApiResponse[list[GroupFollowerDTO], NoMetadata]
