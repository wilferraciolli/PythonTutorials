from datetime import datetime

from pydantic import BaseModel, Field, field_serializer

from chats.constants import TITLE_MAX_LENGTH
from chats.enums import ChatMessageRole
from core.ai.ai import ChatProvider
from core.ai.schemas import ReindexDTO
from core.common.api_response import ApiResponse
from core.common.base_dto import FieldMetadata, LinkedResource, NoMetadata
from core.common.serializers import format_utc_datetime


# --- Request: what the client sends -----------------------------------------

class ChatCreateRequest(BaseModel):
    """Body of `POST /users/{user_id}/chats`."""
    provider: ChatProvider = "cloudflare"


class ChatMessageCreateRequest(BaseModel):
    """Body of `POST .../chats/{chat_id}/messages`."""
    content: str


class ChatTitleUpdateRequest(BaseModel):
    """Body of `PUT .../chats/{chat_id}`."""
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)


# --- DTO: what the application services return ------------------------------

class ChatMessageDTO(BaseModel):
    """One message in a chat."""
    id: str
    chat_id: str
    role: ChatMessageRole
    content: str
    created_date: datetime

    @field_serializer("created_date")
    def serialize_created_date(self, value: datetime) -> str:
        return format_utc_datetime(value)


class ChatDTO(LinkedResource):
    """A chat with its messages, plus the links the caller may follow."""
    id: str
    user_id: str
    title: str
    provider: ChatProvider
    model: str
    created_date: datetime
    updated_date: datetime
    messages: list[ChatMessageDTO] = Field(default_factory=list)

    @field_serializer("created_date", "updated_date")
    def serialize_dates(self, value: datetime) -> str:
        return format_utc_datetime(value)


class ChatSearchHitDTO(LinkedResource):
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


class ChatMetadata(BaseModel):
    """How the client should treat each field of `ChatDTO`."""
    title: FieldMetadata


# --- Response: the envelopes the services build -----------------------------

ChatResponse = ApiResponse[ChatDTO, ChatMetadata]
ChatListResponse = ApiResponse[list[ChatDTO], NoMetadata]
ChatSearchResponse = ApiResponse[list[ChatSearchHitDTO], NoMetadata]
ChatReindexResponse = ApiResponse[ReindexDTO, NoMetadata]
