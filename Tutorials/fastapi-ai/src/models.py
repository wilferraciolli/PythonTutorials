from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, Literal, Optional
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


class EmbeddedRef(BaseModel):
    """
    An embedded reference to another resource — `id` plus its display
    `value` — so a client can render a human-readable name without a
    second round trip to look it up. Same `id`/`value` shape the API
    already uses for metadata option lists (e.g. Todo's `state` values).
    """
    id: str
    value: str


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
    external_user_id: Optional[str] = None
    name: str
    email: str
    roleIds: list[UserRole]
    created_date: datetime

    @field_serializer("created_date")
    def serialize_created_date(self, value: datetime) -> str:
        return format_utc_datetime(value)


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


class ChatMessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessageCreate(BaseModel):
    content: str


ChatProvider = Literal["cloudflare", "groq"]


class ChatCreate(BaseModel):
    provider: ChatProvider = "cloudflare"


class ChatTitleUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=60)


class ChatMessage(BaseModel):
    id: str
    chat_id: str
    role: ChatMessageRole
    content: str
    created_date: datetime

    @field_serializer("created_date")
    def serialize_created_date(self, value: datetime) -> str:
        return format_utc_datetime(value)


class AssistantAsk(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    provider: Literal["groq", "cloudflare"] = "groq"


class ToolCallTrace(BaseModel):
    """One tool the assistant ran to answer, kept so the UI can show its working."""
    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    result: Any = None


class AssistantAnswer(BaseModel):
    question: str
    answer: str
    provider: str
    model: str
    toolCalls: list[ToolCallTrace] = Field(default_factory=list)


class ChatSearchHit(LinkedResource):
    """One message matching a search, with enough context to show and open it."""
    messageId: str
    chatId: str
    chatTitle: str
    role: ChatMessageRole
    snippet: str
    score: float
    keywordMatch: bool
    created_date: datetime

    @field_serializer("created_date")
    def serialize_created_date(self, value: datetime) -> str:
        return format_utc_datetime(value)


class Chat(LinkedResource):
    id: str
    user_id: str
    title: str
    provider: ChatProvider
    model: str
    created_date: datetime
    updated_date: datetime
    messages: list[ChatMessage] = Field(default_factory=list)

    @field_serializer("created_date")
    def serialize_created_date(self, value: datetime) -> str:
        return format_utc_datetime(value)

    @field_serializer("updated_date")
    def serialize_updated_date(self, value: datetime) -> str:
        return format_utc_datetime(value)


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
    user_id: str
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
    # The resource_id's display name, embedded from tag_resource_view —
    # None when the resource can't be resolved (e.g. it's been deleted).
    resource: Optional[EmbeddedRef] = None
    tag: str
    created_date: datetime
    class Config:
        from_attributes = True

    @field_serializer("created_date")
    def serialize_datetime(self, value: datetime) -> str:
        return format_utc_datetime(value)
