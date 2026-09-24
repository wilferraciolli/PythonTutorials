from enum import Enum
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
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


# --- social groups (docs/social-groups.md)

class GroupVisibility(str, Enum):
    PUBLIC = "PUBLIC"
    PRIVATE = "PRIVATE"


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


class MediaType(str, Enum):
    UNSPLASH = "UNSPLASH"
    GIPHY = "GIPHY"
    YOUTUBE = "YOUTUBE"


class MediaRef(BaseModel):
    """What a client sends: the provider and its id. The server looks up the rest."""
    type: MediaType
    id: str = Field(min_length=1, max_length=100)


class PostMedia(BaseModel):
    """
    A post's media. `url` is the image or GIF to show (None for YouTube: build
    the embed from `id`). `title` is the image's alt text. The author fields are
    the Unsplash photographer, for the attribution Unsplash requires.
    """
    type: MediaType
    id: str
    url: Optional[str] = None
    title: Optional[str] = None
    authorName: Optional[str] = None
    authorUrl: Optional[str] = None


class MediaSearchResult(BaseModel):
    """One Unsplash photo or Giphy GIF from a search; send {type, id} back to attach it."""
    type: MediaType
    id: str
    title: Optional[str] = None
    previewUrl: str
    url: str
    authorName: Optional[str] = None
    authorUrl: Optional[str] = None


MAX_TAGGED_PEOPLE = 20


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10000)
    media: Optional[MediaRef] = None
    # User ids of the people tagged in the post; names come back in _metadata.
    taggedUserIds: List[str] = Field(default_factory=list, max_length=MAX_TAGGED_PEOPLE)


class PostUpdate(BaseModel):
    # Media isn't edited here: remove it and add another (PUT/DELETE .../media).
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    body: Optional[str] = Field(None, min_length=1, max_length=10000)
    # None leaves the tagged people as they are; [] removes them all.
    taggedUserIds: Optional[List[str]] = Field(None, max_length=MAX_TAGGED_PEOPLE)


class Post(LinkedResource):
    id: str
    groupId: str
    groupName: str
    authorId: Optional[str] = None
    authorName: Optional[str] = None  # "System" for seeded posts, "[deleted user]", None when deleted
    title: str
    body: str
    media: Optional[PostMedia] = None
    # Ids of the people tagged in the post; their names are in _metadata.taggedUserIds.values.
    taggedUserIds: List[str] = Field(default_factory=list)
    isDeleted: bool = False
    likeCount: int = 0
    commentCount: int = 0
    likedByMe: bool = False
    created_date: datetime
    updated_date: datetime

    @field_serializer("created_date", "updated_date")
    def serialize_post_dates(self, value: datetime) -> str:
        return format_utc_datetime(value)


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    parentCommentId: Optional[str] = None  # set to reply to a comment


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class Comment(LinkedResource):
    id: str
    postId: str
    parentCommentId: Optional[str] = None
    authorId: Optional[str] = None
    authorName: Optional[str] = None
    body: str
    isDeleted: bool = False
    likeCount: int = 0
    likedByMe: bool = False
    created_date: datetime
    updated_date: datetime

    @field_serializer("created_date", "updated_date")
    def serialize_comment_dates(self, value: datetime) -> str:
        return format_utc_datetime(value)
