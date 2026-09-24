from typing import Any, Dict, List, Optional

from core.config.database import Database

# tag_resource_view joins tags to the resource they're attached to (see
# migrations/003_create_tag_resource_view.sql). Reads go through it so every
# row already carries resource_name; the tag_id/tag_name columns are aliased
# back to id/tag so the rest of the repository (and TagService._row_to_tag)
# doesn't need to know the view exists.
_SELECT_TAG = (
    "SELECT tag_id AS id, tag_name AS tag, resource_id, resource_name, created_date "
    "FROM tag_resource_view"
)


class TagRepository:
    """
    Repository for Tag database operations.

    It depends on the project Database protocol, not a concrete backend.
    That keeps the repository portable across SQLite, Cloudflare D1 bindings,
    and D1 over HTTP.
    """

    def __init__(self, db: Database) -> None:
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

        created = await self.get_by_id(id)
        if created is None:
            raise RuntimeError(f"created tag was not found: {id}")
        return created

    async def get_all_by_resource_id(self, resource_id: str) -> List[Dict[str, Any]]:
        return await self.db.fetch_all(f"{_SELECT_TAG} WHERE resource_id = ?", (resource_id,))

    async def search_tags(self, term: Optional[str] = None) -> List[Dict[str, Any]]:
        if term:
            like = f"%{term}%"
            return await self.db.fetch_all(
                f"{_SELECT_TAG} WHERE tag_name LIKE ? OR resource_name LIKE ?",
                (like, like),
            )

        return await self.db.fetch_all(_SELECT_TAG)

    async def get_all(self) -> List[Dict[str, Any]]:
        return await self.db.fetch_all(_SELECT_TAG)

    async def get_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        return await self.db.fetch_one(f"{_SELECT_TAG} WHERE id = ?", (id,))

    async def delete(self, id: str) -> bool:
        existing = await self.get_by_id(id)

        if not existing:
            return False

        await self.db.execute("DELETE FROM tags WHERE id = ?", (id,))

        return True

    async def get_by_resource_and_tag(self, resource_id: str, tag: str) -> Optional[Dict[str, Any]]:
        """Find a specific tag on a resource by name (used to avoid duplicates)."""
        return await self.db.fetch_one(
            f"{_SELECT_TAG} WHERE resource_id = ? AND tag_name = ?",
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
