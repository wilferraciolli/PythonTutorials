from typing import Any, Dict, List, Optional

from core.config.database import Database
from todos.enums import TodoState


class TodoRepository:
    """
    Repository for TODO database operations.

    It depends on the project Database protocol, not a concrete backend.
    That keeps the repository portable across SQLite, Cloudflare D1 bindings,
    and D1 over HTTP.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def create(
        self,
        todo_id: str,
        user_id: str,
        title: str,
        description: Optional[str],
        complete_by: str,
        state: TodoState,
        created_date: str,
    ) -> Dict[str, Any]:
        """Insert a new TODO and return the full row."""
        await self.db.execute(
            "INSERT INTO todos (id, user_id, title, description, complete_by, state, created_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (todo_id, user_id, title, description, complete_by, state.value, created_date),
        )

        created = await self.get_by_id(todo_id, user_id)
        if created is None:
            raise RuntimeError(f"created todo was not found: {todo_id}")
        return created

    async def get_by_id(self, todo_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single TODO row by id, scoped to its owning user, or None if not found."""
        return await self.db.fetch_one(
            "SELECT * FROM todos WHERE id = ? AND user_id = ?",
            (todo_id, user_id),
        )

    async def get_all(self, user_id: str, state: Optional[TodoState] = None) -> List[Dict[str, Any]]:
        """Fetch all TODO rows for a user, optionally filtered by state."""
        if state:
            return await self.db.fetch_all(
                "SELECT * FROM todos WHERE user_id = ? AND state = ? ORDER BY id",
                (user_id, state.value),
            )

        return await self.db.fetch_all(
            "SELECT * FROM todos WHERE user_id = ? ORDER BY id",
            (user_id,),
        )

    async def update(self, todo_id: str, user_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
        """Update only the provided fields on a TODO, then return the fresh row."""
        updatable = {k: v for k, v in fields.items() if v is not None}
        if not updatable:
            return await self.get_by_id(todo_id, user_id)

        # TodoState -> raw string value for storage
        if "state" in updatable and isinstance(updatable["state"], TodoState):
            updatable["state"] = updatable["state"].value

        set_clause = ", ".join(f"{key} = ?" for key in updatable)
        values = list(updatable.values()) + [todo_id, user_id]

        await self.db.execute(
            f"UPDATE todos SET {set_clause} WHERE id = ? AND user_id = ?",
            tuple(values),
        )
        return await self.get_by_id(todo_id, user_id)

    async def delete(self, todo_id: str, user_id: str) -> bool:
        """Delete a TODO. Returns True if a row existed and was removed."""
        existing = await self.get_by_id(todo_id, user_id)
        if not existing:
            return False

        await self.db.execute(
            "DELETE FROM todos WHERE id = ? AND user_id = ?",
            (todo_id, user_id),
        )
        return True

    async def list_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """Every todo of the user, earliest due first (used by the AI assistant's tools)."""
        return await self.db.fetch_all(
            "SELECT * FROM todos WHERE user_id = ? ORDER BY complete_by ASC",
            (user_id,),
        )

    async def search_by_keyword(self, user_id: str, term: str, limit: int) -> List[Dict[str, Any]]:
        like = f"%{term}%"
        return await self.db.fetch_all(
            "SELECT * FROM todos WHERE user_id = ? AND (title LIKE ? OR description LIKE ?) "
            "ORDER BY complete_by ASC LIMIT ?",
            (user_id, like, like, limit),
        )

    async def ids_with_tag(self, user_id: str, tag: str) -> set[str]:
        """Ids of the user's todos carrying `tag` (case-insensitive)."""
        rows = await self.db.fetch_all(
            "SELECT todos.id AS id FROM todos JOIN tags ON tags.resource_id = todos.id "
            "WHERE todos.user_id = ? AND LOWER(tags.tag) = LOWER(?)",
            (user_id, tag),
        )
        return {row["id"] for row in rows}

    async def tag_counts(self, user_id: str) -> List[Dict[str, Any]]:
        """Each tag on the user's todos with how many todos carry it."""
        return await self.db.fetch_all(
            "SELECT tags.tag AS tag, COUNT(*) AS count FROM todos JOIN tags ON tags.resource_id = todos.id "
            "WHERE todos.user_id = ? GROUP BY tags.tag ORDER BY count DESC, tags.tag ASC",
            (user_id,),
        )
