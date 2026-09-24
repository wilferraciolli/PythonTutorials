import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from core.ai.ai import AI
from core.common.api_response import API_PREFIX, envelope
from chats.schemas import Chat, ChatMessage
from core.ai.ai import ChatProvider
from core.common.base_dto import Link
from chats.chat_repository import ChatRepository
from chats.chat_search_service import SearchService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = "You are a friendly, helpful assistant."

TITLE_MAX_LENGTH = 60
DEFAULT_TITLE = "New chat"


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

    Talks to Workers AI through the portable `AI` protocol (ai.py) exactly
    the way user_service.py talks to the database through `Database` —
    nothing here knows whether that's the REST API or the native env.AI
    binding (see ai.get_ai()).
    """

    def __init__(
        self,
        chat_repository: ChatRepository,
        ai_factory: Callable[[ChatProvider], AI],
        models: Dict[ChatProvider, str],
        search_service: Optional["SearchService"] = None,
    ) -> None:
        self.chat_repository = chat_repository
        self.ai_factory = ai_factory
        self.models = models
        self.search_service = search_service

    async def list_chats(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.chat_repository.list_chats_for_user(user_id, list(self.models))

    async def create_chat(self, user_id: str, provider: ChatProvider) -> Dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        chat = await self.chat_repository.create_chat(
            chat_id=str(uuid4()),
            user_id=user_id,
            title=DEFAULT_TITLE,
            provider=provider,
            model=self.models[provider],
            created_date=now,
        )
        chat["messages"] = []
        return chat

    async def get_chat_with_messages(self, chat_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        chat = await self._get_owned_chat(chat_id, user_id)
        if not chat:
            return None

        chat["messages"] = await self.chat_repository.list_messages(chat_id)
        return chat

    async def send_message(self, chat_id: str, user_id: str, content: str) -> Optional[Dict[str, Any]]:
        chat = await self._get_owned_chat(chat_id, user_id)
        if not chat:
            return None

        history = await self.chat_repository.list_messages(chat_id)
        sent_at = datetime.now(timezone.utc).isoformat()

        user_message = await self.chat_repository.add_message(
            message_id=str(uuid4()),
            chat_id=chat_id,
            role="user",
            content=content,
            created_date=sent_at,
        )

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        messages.extend({"role": message["role"], "content": message["content"]} for message in history)
        messages.append({"role": "user", "content": content})

        provider = chat["provider"]
        result = await self.ai_factory(provider).run(self.models[provider], {"messages": messages})
        reply = self._extract_reply(result)

        replied_at = datetime.now(timezone.utc).isoformat()
        assistant_message = await self.chat_repository.add_message(
            message_id=str(uuid4()),
            chat_id=chat_id,
            role="assistant",
            content=reply,
            created_date=replied_at,
        )
        await self._index_messages(user_id, [user_message, assistant_message])

        if chat["title"] == DEFAULT_TITLE:
            await self.chat_repository.update_title(chat_id, _derive_title(content))

        await self.chat_repository.touch(chat_id, replied_at)

        return await self.get_chat_with_messages(chat_id, user_id)

    async def delete_chat(self, chat_id: str, user_id: str) -> bool:
        chat = await self._get_owned_chat(chat_id, user_id)
        if not chat:
            return False

        if self.search_service:
            await self.search_service.remove_chat(chat_id)

        return await self.chat_repository.delete_chat(chat_id)

    async def update_title(self, chat_id: str, user_id: str, title: str) -> Optional[Dict[str, Any]]:
        chat = await self._get_owned_chat(chat_id, user_id)
        if not chat:
            return None

        normalized_title = " ".join(title.split())
        if not normalized_title:
            return None

        await self.chat_repository.update_title(chat_id, normalized_title)
        await self.chat_repository.touch(chat_id, datetime.now(timezone.utc).isoformat())
        return await self.get_chat_with_messages(chat_id, user_id)

    async def _index_messages(self, user_id: str, messages: List[Dict[str, Any]]) -> None:
        # Best effort: search indexing must never break sending a message.
        # Anything missed here is picked up by the search reindex endpoint.
        if not self.search_service:
            return

        try:
            await self.search_service.index_messages(user_id, messages)
        except Exception:
            logger.exception("failed to index messages for search")

    async def _get_owned_chat(self, chat_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        # Chats aren't nested under /users/{id}/... in the URL (unlike
        # fastapi-cloudflare-d1's todos), so ownership has to be checked
        # here instead of being implicit in the route — a chat that exists
        # but belongs to someone else reads as 404, not 403, so its
        # existence isn't leaked to a caller who shouldn't see it.
        chat = await self.chat_repository.get_chat(chat_id)
        if not chat or chat["user_id"] != user_id or chat["provider"] not in self.models:
            return None
        return chat

    def _extract_reply(self, result: Dict[str, Any]) -> str:
        # Workers AI text-generation models return {"response": "..."} per
        # Cloudflare's documented API; fall back to the raw result if a
        # different model shape ever comes back (see README's "Known Beta
        # Caveats" — the same defensive posture database.py takes with D1
        # row shapes).
        response = result.get("response")
        return response if isinstance(response, str) else str(result)

    def to_chat(self, row: Dict[str, Any]) -> Chat:
        return Chat(
            id=row["id"],
            user_id=row["user_id"],
            title=row["title"],
            provider=row["provider"],
            model=row["model"],
            created_date=row["created_date"],
            updated_date=row["updated_date"],
            messages=[self.to_message(message) for message in row.get("messages", [])],
            links=self.build_chat_links(row["user_id"], row["id"]),
        )

    def to_message(self, row: Dict[str, Any]) -> ChatMessage:
        return ChatMessage(
            id=row["id"],
            chat_id=row["chat_id"],
            role=row["role"],
            content=row["content"],
            created_date=row["created_date"],
        )

    def build_chat_links(self, user_id: str, chat_id: str) -> Dict[str, Link]:
        base = f"{API_PREFIX}/users/{user_id}/chats/{chat_id}"
        return {
            "self": Link(href=base, method="GET"),
            "updateTitle": Link(href=base, method="PUT"),
            "sendMessage": Link(href=f"{base}/messages", method="POST"),
            "delete": Link(href=base, method="DELETE"),
        }

    def build_response(self, row: Dict[str, Any]) -> Dict[str, Any]:
        chat = self.to_chat(row)
        return envelope(
            data_name="chat",
            data=chat,
            metadata={
                "title": {"maxLength": TITLE_MAX_LENGTH},
            },
            meta_links={},
        )

    def build_list_response(self, user_id: str, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        chats = [self.to_chat(row) for row in rows]
        return envelope(
            data_name="chats",
            data=chats,
            metadata={},
            meta_links={
                "createChat": Link(href=f"{API_PREFIX}/users/{user_id}/chats", method="POST"),
            },
        )
