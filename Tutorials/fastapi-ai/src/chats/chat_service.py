import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from chats.chat_repository import ChatRepository
from chats.chat_search_service import ChatSearchService
from chats.constants import (
    CHAT_DATA_NAME,
    CHATS_DATA_NAME,
    DEFAULT_TITLE,
    LINK_CREATE_CHAT,
    LINK_DELETE,
    LINK_SELF,
    LINK_SEND_MESSAGE,
    LINK_UPDATE_TITLE,
    TITLE_MAX_LENGTH,
)
from chats.enums import ChatMessageRole
from chats.models import ChatMessageModel, ChatModel
from chats.schemas import ChatDTO, ChatListResponse, ChatMessageDTO, ChatMetadata, ChatResponse
from core.ai.ai import AI, ChatProvider
from core.common.api_response import API_PREFIX
from core.common.base_dto import FieldMetadata, Link, NoMetadata

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a friendly, helpful assistant."


def _derive_title(content: str) -> str:
    stripped = " ".join(content.split())
    if not stripped:
        return DEFAULT_TITLE
    if len(stripped) <= TITLE_MAX_LENGTH:
        return stripped
    return stripped[: TITLE_MAX_LENGTH - 1].rstrip() + "…"


class ChatService:
    """
    Application service for AI chats.

    Talks to Workers AI through the portable `AI` protocol (core/ai/ai.py)
    exactly the way the repositories talk to the database through `Database`
    — nothing here knows whether that's the REST API or the native env.AI
    binding (see get_ai()).

    Chats are personal: the router only lets the user in the path through
    (require_owner).
    """

    def __init__(
        self,
        chat_repository: ChatRepository,
        ai_factory: Callable[[ChatProvider], AI],
        models: Dict[ChatProvider, str],
        search_service: Optional[ChatSearchService] = None,
    ) -> None:
        self.chat_repository = chat_repository
        self.ai_factory = ai_factory
        self.models = models
        self.search_service = search_service

    async def list_chats(self, user_id: str) -> List[ChatDTO]:
        chats = await self.chat_repository.list_chats_for_user(user_id, list(self.models))
        return [self.to_dto(chat) for chat in chats]

    async def create_chat(self, user_id: str, provider: ChatProvider) -> ChatDTO:
        chat = await self.chat_repository.create_chat(
            chat_id=str(uuid4()),
            user_id=user_id,
            title=DEFAULT_TITLE,
            provider=provider,
            model=self.models[provider],
            created_date=datetime.now(timezone.utc).isoformat(),
        )
        return self.to_dto(chat)

    async def get_chat_with_messages(self, chat_id: str, user_id: str) -> Optional[ChatDTO]:
        chat = await self._get_owned_chat(chat_id, user_id)
        if not chat:
            return None

        return self.to_dto(chat, await self.chat_repository.list_messages(chat_id))

    async def send_message(self, chat_id: str, user_id: str, content: str) -> Optional[ChatDTO]:
        chat = await self._get_owned_chat(chat_id, user_id)
        if not chat:
            return None

        history = await self.chat_repository.list_messages(chat_id)

        user_message = await self.chat_repository.add_message(
            message_id=str(uuid4()),
            chat_id=chat_id,
            role=ChatMessageRole.USER.value,
            content=content,
            created_date=datetime.now(timezone.utc).isoformat(),
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend({"role": message.role.value, "content": message.content} for message in history)
        messages.append({"role": "user", "content": content})

        result = await self.ai_factory(chat.provider).run(self.models[chat.provider], {"messages": messages})
        reply = self._extract_reply(result)

        replied_at = datetime.now(timezone.utc).isoformat()
        assistant_message = await self.chat_repository.add_message(
            message_id=str(uuid4()),
            chat_id=chat_id,
            role=ChatMessageRole.ASSISTANT.value,
            content=reply,
            created_date=replied_at,
        )
        await self._index_messages(user_id, [user_message, assistant_message])

        if chat.title == DEFAULT_TITLE:
            await self.chat_repository.update_title(chat_id, _derive_title(content))

        await self.chat_repository.touch(chat_id, replied_at)

        return await self.get_chat_with_messages(chat_id, user_id)

    async def delete_chat(self, chat_id: str, user_id: str) -> bool:
        if not await self._get_owned_chat(chat_id, user_id):
            return False

        if self.search_service:
            await self.search_service.remove_chat(chat_id)

        return await self.chat_repository.delete_chat(chat_id)

    async def update_title(self, chat_id: str, user_id: str, title: str) -> Optional[ChatDTO]:
        if not await self._get_owned_chat(chat_id, user_id):
            return None

        normalized_title = " ".join(title.split())
        if not normalized_title:
            return None

        await self.chat_repository.update_title(chat_id, normalized_title)
        await self.chat_repository.touch(chat_id, datetime.now(timezone.utc).isoformat())
        return await self.get_chat_with_messages(chat_id, user_id)

    async def _index_messages(self, user_id: str, messages: List[ChatMessageModel]) -> None:
        # Best effort: search indexing must never break sending a message.
        # Anything missed here is picked up by the search reindex endpoint.
        if not self.search_service:
            return

        try:
            await self.search_service.index_messages(user_id, messages)
        except Exception:
            logger.exception("failed to index messages for search")

    async def _get_owned_chat(self, chat_id: str, user_id: str) -> Optional[ChatModel]:
        # The chat id alone doesn't say whose it is, so ownership is checked
        # here too: a chat that exists but belongs to someone else reads as
        # 404, not 403, so its existence isn't leaked to a caller who
        # shouldn't see it. So does another project's chat (provider).
        chat = await self.chat_repository.get_chat(chat_id)
        if not chat or chat.user_id != user_id or chat.provider not in self.models:
            return None
        return chat

    @staticmethod
    def _extract_reply(result: Dict[str, Any]) -> str:
        # Workers AI text-generation models return {"response": "..."} per
        # Cloudflare's documented API; fall back to the raw result if a
        # different model shape ever comes back (see README's "Known Beta
        # Caveats" — the same defensive posture the D1 adapters take with
        # row shapes).
        response = result.get("response")
        return response if isinstance(response, str) else str(result)

    # --- responses

    def to_dto(self, chat: ChatModel, messages: Optional[List[ChatMessageModel]] = None) -> ChatDTO:
        return ChatDTO(
            **chat.model_dump(),
            messages=[ChatMessageDTO(**message.model_dump()) for message in messages or []],
            links=self.build_links(chat.user_id, chat.id),
        )

    @staticmethod
    def build_links(user_id: str, chat_id: str) -> Dict[str, Link]:
        base = f"{API_PREFIX}/users/{user_id}/chats/{chat_id}"
        return {
            LINK_SELF: Link(href=base, method="GET"),
            LINK_UPDATE_TITLE: Link(href=base, method="PUT"),
            LINK_SEND_MESSAGE: Link(href=f"{base}/messages", method="POST"),
            LINK_DELETE: Link(href=base, method="DELETE"),
        }

    @staticmethod
    def build_response(chat: ChatDTO) -> ChatResponse:
        return ChatResponse.of(CHAT_DATA_NAME, chat, ChatMetadata(title=FieldMetadata(maxLength=TITLE_MAX_LENGTH)))

    @staticmethod
    def build_list_response(user_id: str, chats: List[ChatDTO]) -> ChatListResponse:
        return ChatListResponse.of(
            CHATS_DATA_NAME,
            chats,
            NoMetadata(),
            {LINK_CREATE_CHAT: Link(href=f"{API_PREFIX}/users/{user_id}/chats", method="POST")},
        )
