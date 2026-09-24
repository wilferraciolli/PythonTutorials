from typing import Any, List, Mapping, Optional

from chats.models import ChatMessageHitModel, ChatMessageModel, ChatModel
from core.config.database import Database

_SELECT_MESSAGE_HIT = (
    "SELECT m.*, c.title AS chat_title, c.user_id AS user_id FROM chat_messages m "
    "JOIN chats c ON c.id = m.chat_id"
)


def _placeholders(values: List[str]) -> str:
    return ", ".join("?" for _ in values)


class ChatRepository:
    """
    Repository for chat and chat-message database operations.

    Depends on the portable Database protocol, not SQLite or Cloudflare D1
    directly — same pattern as UserRepository.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def create_chat(
        self,
        chat_id: str,
        user_id: str,
        title: str,
        provider: str,
        model: str,
        created_date: str,
    ) -> ChatModel:
        await self.db.execute(
            "INSERT INTO chats (id, user_id, title, provider, model, created_date, updated_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (chat_id, user_id, title, provider, model, created_date, created_date),
        )

        chat = await self.get_chat(chat_id)
        if chat is None:
            raise RuntimeError(f"created chat was not found: {chat_id}")
        return chat

    async def get_chat(self, chat_id: str) -> Optional[ChatModel]:
        row = await self.db.fetch_one("SELECT * FROM chats WHERE id = ?", (chat_id,))
        return ChatModel(**row) if row else None

    async def list_chats_for_user(self, user_id: str, providers: List[str]) -> List[ChatModel]:
        # The chats table is shared by every python project (same D1), so
        # each project only lists the providers it owns.
        rows = await self.db.fetch_all(
            f"SELECT * FROM chats WHERE user_id = ? AND provider IN ({_placeholders(providers)}) "
            "ORDER BY updated_date DESC",
            (user_id, *providers),
        )
        return [ChatModel(**row) for row in rows]

    async def update_title(self, chat_id: str, title: str) -> None:
        await self.db.execute("UPDATE chats SET title = ? WHERE id = ?", (title, chat_id))

    async def touch(self, chat_id: str, updated_date: str) -> None:
        await self.db.execute("UPDATE chats SET updated_date = ? WHERE id = ?", (updated_date, chat_id))

    async def delete_chat(self, chat_id: str) -> bool:
        if await self.get_chat(chat_id) is None:
            return False

        await self.db.execute("DELETE FROM chat_messages WHERE chat_id = ?", (chat_id,))
        await self.db.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
        return True

    async def add_message(
        self,
        message_id: str,
        chat_id: str,
        role: str,
        content: str,
        created_date: str,
    ) -> ChatMessageModel:
        await self.db.execute(
            "INSERT INTO chat_messages (id, chat_id, role, content, created_date) VALUES (?, ?, ?, ?, ?)",
            (message_id, chat_id, role, content, created_date),
        )

        message = await self.get_message(message_id)
        if message is None:
            raise RuntimeError(f"created message was not found: {message_id}")
        return message

    async def get_message(self, message_id: str) -> Optional[ChatMessageModel]:
        row = await self.db.fetch_one("SELECT * FROM chat_messages WHERE id = ?", (message_id,))
        return ChatMessageModel(**row) if row else None

    async def list_messages(self, chat_id: str) -> List[ChatMessageModel]:
        rows = await self.db.fetch_all(
            "SELECT * FROM chat_messages WHERE chat_id = ? ORDER BY created_date ASC",
            (chat_id,),
        )
        return [ChatMessageModel(**row) for row in rows]

    async def list_messages_for_user(self, user_id: str, providers: List[str]) -> List[ChatMessageHitModel]:
        """Every message in the user's chats (for the providers this project owns), with its chat title."""
        rows = await self.db.fetch_all(
            f"{_SELECT_MESSAGE_HIT} WHERE c.user_id = ? AND c.provider IN ({_placeholders(providers)}) "
            "ORDER BY m.created_date ASC",
            (user_id, *providers),
        )
        return [self._to_hit(row) for row in rows]

    async def get_messages_for_user(self, user_id: str, message_ids: List[str]) -> List[ChatMessageHitModel]:
        if not message_ids:
            return []

        rows = await self.db.fetch_all(
            f"{_SELECT_MESSAGE_HIT} WHERE c.user_id = ? AND m.id IN ({_placeholders(message_ids)})",
            (user_id, *message_ids),
        )
        return [self._to_hit(row) for row in rows]

    async def search_messages_by_keyword(
        self, user_id: str, term: str, providers: List[str], limit: int
    ) -> List[ChatMessageHitModel]:
        rows = await self.db.fetch_all(
            f"{_SELECT_MESSAGE_HIT} WHERE c.user_id = ? AND c.provider IN ({_placeholders(providers)}) "
            "AND m.content LIKE ? ORDER BY m.created_date DESC LIMIT ?",
            (user_id, *providers, f"%{term}%", limit),
        )
        return [self._to_hit(row) for row in rows]

    @staticmethod
    def _to_hit(row: Mapping[str, Any]) -> ChatMessageHitModel:
        return ChatMessageHitModel(**row)
