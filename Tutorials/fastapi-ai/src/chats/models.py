from pydantic import BaseModel

from chats.enums import ChatMessageRole
from core.common.serializers import UtcDateTime


class ChatModel(BaseModel):
    """A `chats` database row."""
    id: str
    user_id: str
    title: str
    # A plain string: the table is shared with other projects' providers,
    # which ChatService filters out.
    provider: str
    model: str
    created_date: UtcDateTime
    updated_date: UtcDateTime


class ChatMessageModel(BaseModel):
    """A `chat_messages` database row."""
    id: str
    chat_id: str
    role: ChatMessageRole
    content: str
    created_date: UtcDateTime


class ChatMessageHitModel(ChatMessageModel):
    """A chat message joined with its chat, for search results."""
    chat_title: str
    user_id: str
