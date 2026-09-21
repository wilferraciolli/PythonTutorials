from typing import Any, Dict, List, Optional

from database import Database


class TagRepository:
    """
    Repository for Tag database operations.

    It depends on the project Database protocol, not a concrete backend.
    That keeps the repository portable across SQLite, Cloudflare D1 bindings,
    and D1 over HTTP.
    """

    def __init__(self, db: Database):
        self.db = db

    async def create(
            self,
            id: str,
            tag: str,
            resource_id: str,
            created_date: str
    ) -> Dict[str, Any]:
        await self.db.execute(
            "INSERT INTO tags (id, tag, resource_id, created_date) "
            "VALUES (?, ?, ?, ?)",
            (id, tag, resource_id, created_date),
        )

        return await self.get_by_id(id)

    async def get_all_by_resource_id(self, resource_id: str) -> List[Dict[str, Any]]:
        return await self.db.fetch_all("SELECT * FROM tags WHERE resource_id = ?", (resource_id,))

    async def search_tags(self, term: Optional[str] = None) -> List[Dict[str, Any]]:
        if term:
            return await self.db.fetch_all("SELECT * FROM tags WHERE tag LIKE ?", (f"%{term}%",))

        return await self.db.fetch_all("SELECT * FROM tags")

    async def get_all(self) -> List[Dict[str, Any]]:
        return await self.db.fetch_all("SELECT * FROM tags")

    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return await self.db.fetch_one("SELECT * FROM tags WHERE id = ?", (id,))

    async def delete(self, id: str) -> bool:
        existing = await self.get_by_id(id)

        if not existing:
            return False

        await self.db.execute("DELETE FROM tags WHERE id = ?", (id,))

        return True

    async def get_by_resource_and_tag(self, resource_id: str, tag: str) -> Optional[Dict[str, Any]]:
        """Find a specific tag on a resource by name (used to avoid duplicates)."""
        return await self.db.fetch_one(
            "SELECT * FROM tags WHERE resource_id = ? AND tag = ?",
            (resource_id, tag),
        )

    async def delete_by_resource_and_tag(self, resource_id: str, tag: str) -> bool:
        """Remove a specific tag from a resource by name, if it exists."""
        existing = await self.get_by_resource_and_tag(resource_id, tag)

        if not existing:
            return False

        await self.db.execute(
            "DELETE FROM tags WHERE resource_id = ? AND tag = ?",
            (resource_id, tag),
        )

        return True

    async def delete_all_for_resource(self, resource_id: str) -> None:
        """Remove every tag attached to a resource (used when the resource itself is deleted)."""
        await self.db.execute("DELETE FROM tags WHERE resource_id = ?", (resource_id,))
