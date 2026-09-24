from typing import Any, List, Mapping, Optional

from core.config.database import Database
from todos.enums import TodoState
from todos.models import TodoModel, TodoTagCountModel


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
    ) -> TodoModel:
        """Insert a new TODO and return it."""
        await self.db.execute(
            "INSERT INTO todos (id, user_id, title, description, complete_by, state, created_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (todo_id, user_id, title, description, complete_by, state.value, created_date),
        )

        created = await self.get_by_id(todo_id, user_id)
        if created is None:
            raise RuntimeError(f"created todo was not found: {todo_id}")
        return created

    async def get_by_id(self, todo_id: str, user_id: str) -> Optional[TodoModel]:
        """Fetch a single TODO by id, scoped to its owning user, or None if not found."""
        row = await self.db.fetch_one(
            "SELECT * FROM todos WHERE id = ? AND user_id = ?",
            (todo_id, user_id),
        )
        return self._to_model(row)

    async def get_all(self, user_id: str, state: Optional[TodoState] = None) -> List[TodoModel]:
        """Fetch all TODOs for a user, optionally filtered by state."""
        if state:
            rows = await self.db.fetch_all(
                "SELECT * FROM todos WHERE user_id = ? AND state = ? ORDER BY id",
                (user_id, state.value),
            )
        else:
            rows = await self.db.fetch_all(
                "SELECT * FROM todos WHERE user_id = ? ORDER BY id",
                (user_id,),
            )
        return [self._to_model(row) for row in rows]

    async def update(
        self,
        todo_id: str,
        user_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        complete_by: Optional[str] = None,
        state: Optional[TodoState] = None,
    ) -> Optional[TodoModel]:
        """Change only the arguments that are not None, then return the fresh todo."""
        updatable = {
            key: value
            for key, value in (
                ("title", title),
                ("description", description),
                ("complete_by", complete_by),
                ("state", state.value if state else None),
            )
            if value is not None
        }

        if updatable:
            set_clause = ", ".join(f"{key} = ?" for key in updatable)
            await self.db.execute(
                f"UPDATE todos SET {set_clause} WHERE id = ? AND user_id = ?",
                (*updatable.values(), todo_id, user_id),
            )

        return await self.get_by_id(todo_id, user_id)

    async def delete(self, todo_id: str, user_id: str) -> bool:
        """Delete a TODO. Returns True if a row existed and was removed."""
        if await self.get_by_id(todo_id, user_id) is None:
            return False

        await self.db.execute(
            "DELETE FROM todos WHERE id = ? AND user_id = ?",
            (todo_id, user_id),
        )
        return True

    async def list_for_user(self, user_id: str) -> List[TodoModel]:
        """Every todo of the user, earliest due first (used by the AI assistant's tools)."""
        rows = await self.db.fetch_all(
            "SELECT * FROM todos WHERE user_id = ? ORDER BY complete_by ASC",
            (user_id,),
        )
        return [self._to_model(row) for row in rows]

    async def search_by_keyword(self, user_id: str, term: str, limit: int) -> List[TodoModel]:
        like = f"%{term}%"
        rows = await self.db.fetch_all(
            "SELECT * FROM todos WHERE user_id = ? AND (title LIKE ? OR description LIKE ?) "
            "ORDER BY complete_by ASC LIMIT ?",
            (user_id, like, like, limit),
        )
        return [self._to_model(row) for row in rows]

    async def ids_with_tag(self, user_id: str, tag: str) -> set[str]:
        """Ids of the user's todos carrying `tag` (case-insensitive)."""
        rows = await self.db.fetch_all(
            "SELECT todos.id AS id FROM todos JOIN tags ON tags.resource_id = todos.id "
            "WHERE todos.user_id = ? AND LOWER(tags.tag) = LOWER(?)",
            (user_id, tag),
        )
        return {row["id"] for row in rows}

    async def tag_counts(self, user_id: str) -> List[TodoTagCountModel]:
        """Each tag on the user's todos with how many todos carry it."""
        rows = await self.db.fetch_all(
            "SELECT tags.tag AS tag, COUNT(*) AS count FROM todos JOIN tags ON tags.resource_id = todos.id "
            "WHERE todos.user_id = ? GROUP BY tags.tag ORDER BY count DESC, tags.tag ASC",
            (user_id,),
        )
        return [TodoTagCountModel(**row) for row in rows]

    @staticmethod
    def _to_model(row: Optional[Mapping[str, Any]]) -> Optional[TodoModel]:
        return TodoModel(**row) if row else None
