from typing import Any, Dict, List, Optional

from models import TodoState


class TodoRepository:
    """
    Repository for TODO database operations, backed by a Cloudflare D1 binding.

    D1 has no connection string - it is accessed via a binding object (env.DB)
    injected by the Workers runtime. All methods here are async because every
    D1 call crosses into the Workers runtime asynchronously.

    NOTE: D1's Python binding API is in beta. Row objects returned by
    `.first()` / `.all().results` behave like dicts (`row["id"]`). If the
    exact attribute names differ in your installed `workers-py` version,
    adjust `_get()` below - everything else stays the same.
    """

    def __init__(self, db):
        # `db` is the D1 binding (e.g. env.DB), passed in per-request.
        self.db = db

    @staticmethod
    def _get(row: Any, key: str, default=None):
        """Safely read a field whether the row is dict-like or attribute-like."""
        if row is None:
            return default
        try:
            return row[key]
        except (TypeError, KeyError):
            return getattr(row, key, default)

    async def create(
        self,
        title: str,
        description: Optional[str],
        complete_by: str,
        state: TodoState,
        created_date: str,
    ) -> Dict[str, Any]:
        """Insert a new TODO and return the full row."""
        result = await self.db.prepare(
            "INSERT INTO todos (title, description, complete_by, state, created_date) "
            "VALUES (?, ?, ?, ?, ?)"
        ).bind(title, description, complete_by, state.value, created_date).run()

        new_id = self._get(self._get(result, "meta"), "last_row_id")
        return await self.get_by_id(new_id)

    async def get_by_id(self, todo_id: int) -> Optional[Dict[str, Any]]:
        """Fetch a single TODO row by id, or None if not found."""
        row = await self.db.prepare("SELECT * FROM todos WHERE id = ?").bind(todo_id).first()
        return row

    async def get_all(self, state: Optional[TodoState] = None) -> List[Dict[str, Any]]:
        """Fetch all TODO rows, optionally filtered by state."""
        if state:
            result = await self.db.prepare(
                "SELECT * FROM todos WHERE state = ? ORDER BY id"
            ).bind(state.value).all()
        else:
            result = await self.db.prepare("SELECT * FROM todos ORDER BY id").all()

        return self._get(result, "results", [])

    async def update(self, todo_id: int, **fields) -> Optional[Dict[str, Any]]:
        """Update only the provided fields on a TODO, then return the fresh row."""
        updatable = {k: v for k, v in fields.items() if v is not None}
        if not updatable:
            return await self.get_by_id(todo_id)

        # TodoState -> raw string value for storage
        if "state" in updatable and isinstance(updatable["state"], TodoState):
            updatable["state"] = updatable["state"].value

        set_clause = ", ".join(f"{key} = ?" for key in updatable)
        values = list(updatable.values()) + [todo_id]

        await self.db.prepare(f"UPDATE todos SET {set_clause} WHERE id = ?").bind(*values).run()
        return await self.get_by_id(todo_id)

    async def delete(self, todo_id: int) -> bool:
        """Delete a TODO. Returns True if a row existed and was removed."""
        existing = await self.get_by_id(todo_id)
        if not existing:
            return False

        await self.db.prepare("DELETE FROM todos WHERE id = ?").bind(todo_id).run()
        return True
