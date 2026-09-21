from enum import Enum
from datetime import datetime, timezone
from typing import Dict, Optional
from pydantic import BaseModel, Field, field_serializer


def format_utc_datetime(value: datetime) -> str:
    """Serialize datetimes as UTC seconds: YYYY-MM-DDTHH:MM:SSZ."""
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# Shared HATEOAS-style link, reused by any response DTO
class Link(BaseModel):
    """A single navigation link describing a related action on a resource."""
    href: str
    method: str = "GET"


class LinkedResource(BaseModel):
    """
    Base class adding a `links` map to any response DTO.

    Any model that inherits this gets a `links: Dict[str, Link]` field for free,
    so the same Link shape/behavior is shared across Todo, Tag, and any
    future resource - no copy-pasting the field definition each time.
    """
    links: Dict[str, Link] = Field(default_factory=dict)

# Enum for user role
class UserRole(str, Enum):
    STANDARD = "STANDARD"
    ADMIN = "ADMIN"

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
    name: str
    email: str
    roleIds: list[UserRole]
    created_date: datetime

    @field_serializer("created_date")
    def serialize_created_date(self, value: datetime) -> str:
        return format_utc_datetime(value)


class UserProfile(LinkedResource):
    id: str
    name: str
    roleIds: list[UserRole]


# Enum for todo state
class TodoState(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"

# Request model for creating
class TodoCreate(BaseModel):
    """Model for creating a new TODO"""
    title: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = Field(None)
    complete_by: datetime
    state: TodoState = Field(default=TodoState.NEW)

# Request model for updating
class TodoUpdate(BaseModel):
    """Model for updating a TODO"""
    title: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = Field(None)
    complete_by: Optional[datetime] = None
    state: Optional[TodoState] = None

# Response model
class Todo(LinkedResource):
    """Complete TODO object returned by API"""
    id: str
    title: str
    description: Optional[str] = None
    complete_by: datetime
    state: TodoState
    created_date: datetime

    class Config:
        from_attributes = True

    @field_serializer("complete_by", "created_date")
    def serialize_datetime(self, value: datetime) -> str:
        return format_utc_datetime(value)


# Response model
class TagCreate(BaseModel):
    resource_id: str = Field(..., min_length=1)
    tag: str = Field(..., min_length=1, max_length=50)

class Tag(LinkedResource):
    id: str
    resource_id: str
    tag: str
    created_date: datetime
    class Config:
        from_attributes = True

    @field_serializer("created_date")
    def serialize_datetime(self, value: datetime) -> str:
        return format_utc_datetime(value)
