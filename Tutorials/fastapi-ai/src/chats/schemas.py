from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from chats.enums import ChatMessageRole
from core.ai.ai import ChatProvider
from core.common.base_dto import LinkedResource
from core.common.serializers import format_utc_datetime


class ChatMessageCreate(BaseModel):
    content: str


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
