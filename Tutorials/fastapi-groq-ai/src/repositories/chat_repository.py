from typing import Any, Dict, List, Optional

from database import Database


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
    ) -> Dict[str, Any]:
        await self.db.execute(
            "INSERT INTO chats (id, user_id, title, provider, model, created_date, updated_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (chat_id, user_id, title, provider, model, created_date, created_date),
        )

        chat = await self.get_chat(chat_id)
        if chat is None:
            raise RuntimeError(f"created chat was not found: {chat_id}")
        return chat

    async def get_chat(self, chat_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.fetch_one("SELECT * FROM chats WHERE id = ?", (chat_id,))

    async def list_chats_for_user(self, user_id: str, providers: List[str]) -> List[Dict[str, Any]]:
        # The chats table is shared by every python project (same D1), so
        # each project only lists the providers it owns.
        placeholders = ", ".join("?" for _ in providers)
        return await self.db.fetch_all(
            f"SELECT * FROM chats WHERE user_id = ? AND provider IN ({placeholders}) "
            "ORDER BY updated_date DESC",
            (user_id, *providers),
        )

    async def update_title(self, chat_id: str, title: str) -> None:
        await self.db.execute("UPDATE chats SET title = ? WHERE id = ?", (title, chat_id))

    async def touch(self, chat_id: str, updated_date: str) -> None:
        await self.db.execute("UPDATE chats SET updated_date = ? WHERE id = ?", (updated_date, chat_id))

    async def delete_chat(self, chat_id: str) -> bool:
        existing = await self.get_chat(chat_id)
        if not existing:
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
    ) -> Dict[str, Any]:
        await self.db.execute(
            "INSERT INTO chat_messages (id, chat_id, role, content, created_date) VALUES (?, ?, ?, ?, ?)",
            (message_id, chat_id, role, content, created_date),
        )

        message = await self.get_message(message_id)
        if message is None:
            raise RuntimeError(f"created message was not found: {message_id}")
        return message

    async def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.fetch_one("SELECT * FROM chat_messages WHERE id = ?", (message_id,))

    async def list_messages(self, chat_id: str) -> List[Dict[str, Any]]:
        return await self.db.fetch_all(
            "SELECT * FROM chat_messages WHERE chat_id = ? ORDER BY created_date ASC",
            (chat_id,),
        )
