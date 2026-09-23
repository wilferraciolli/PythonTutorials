from typing import Any, Dict, List

from database import Database


class TodoRepository:
    """
    Read-only access to the `todos` table.

    Todos are owned by fastapi-cloudflare-d1 (same shared database); this
    project only reads them, for the AI assistant's todo tools.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        return await self.db.fetch_all(
            "SELECT * FROM todos WHERE user_id = ? ORDER BY complete_by ASC",
            (user_id,),
        )
