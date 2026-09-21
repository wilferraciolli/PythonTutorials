from typing import Any, Dict, List, Optional

from database import Database
from models import TodoState


class TodoRepository:
    """
    Repository for TODO database operations.

    It depends on the project Database protocol, not a concrete backend.
    That keeps the repository portable across SQLite, Cloudflare D1 bindings,
    and D1 over HTTP.
    """

    def __init__(self, db: Database):
        self.db = db

    async def create(
        self,
        todo_id: str,
        title: str,
        description: Optional[str],
        complete_by: str,
        state: TodoState,
        created_date: str,
    ) -> Dict[str, Any]:
        """Insert a new TODO and return the full row."""
        await self.db.execute(
            "INSERT INTO todos (id, title, description, complete_by, state, created_date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (todo_id, title, description, complete_by, state.value, created_date),
        )

        return await self.get_by_id(todo_id)

    async def get_by_id(self, todo_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single TODO row by id, or None if not found."""
        return await self.db.fetch_one("SELECT * FROM todos WHERE id = ?", (todo_id,))

    async def get_all(self, state: Optional[TodoState] = None) -> List[Dict[str, Any]]:
        """Fetch all TODO rows, optionally filtered by state."""
        if state:
            return await self.db.fetch_all(
                "SELECT * FROM todos WHERE state = ? ORDER BY id",
                (state.value,),
            )

        return await self.db.fetch_all("SELECT * FROM todos ORDER BY id")

    async def update(self, todo_id: str, **fields) -> Optional[Dict[str, Any]]:
        """Update only the provided fields on a TODO, then return the fresh row."""
        updatable = {k: v for k, v in fields.items() if v is not None}
        if not updatable:
            return await self.get_by_id(todo_id)

        # TodoState -> raw string value for storage
        if "state" in updatable and isinstance(updatable["state"], TodoState):
            updatable["state"] = updatable["state"].value

        set_clause = ", ".join(f"{key} = ?" for key in updatable)
        values = list(updatable.values()) + [todo_id]

        await self.db.execute(f"UPDATE todos SET {set_clause} WHERE id = ?", tuple(values))
        return await self.get_by_id(todo_id)

    async def delete(self, todo_id: str) -> bool:
        """Delete a TODO. Returns True if a row existed and was removed."""
        existing = await self.get_by_id(todo_id)
        if not existing:
            return False

        await self.db.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        return True
