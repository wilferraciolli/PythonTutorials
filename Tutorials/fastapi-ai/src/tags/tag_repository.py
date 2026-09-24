from typing import Any, List, Mapping, Optional

from core.config.database import Database
from tags.models import TagModel

# tag_resource_view joins tags to the resource they're attached to (see
# migrations/006_create_tags_and_resource_view.sql). Reads go through it so
# every row already carries resource_name; the tag_id/tag_name columns are
# aliased back to id/tag to match TagModel.
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

    async def create(self, tag_id: str, tag: str, resource_id: str, created_date: str) -> TagModel:
        await self.db.execute(
            "INSERT INTO tags (id, tag, resource_id, created_date) VALUES (?, ?, ?, ?)",
            (tag_id, tag, resource_id, created_date),
        )

        created = await self.get_by_id(tag_id)
        if created is None:
            raise RuntimeError(f"created tag was not found: {tag_id}")
        return created

    async def get_all_by_resource_id(self, resource_id: str) -> List[TagModel]:
        rows = await self.db.fetch_all(f"{_SELECT_TAG} WHERE resource_id = ?", (resource_id,))
        return [self._to_model(row) for row in rows]

    async def search_tags(self, term: Optional[str] = None) -> List[TagModel]:
        if not term:
            return await self.get_all()

        like = f"%{term}%"
        rows = await self.db.fetch_all(
            f"{_SELECT_TAG} WHERE tag_name LIKE ? OR resource_name LIKE ?",
            (like, like),
        )
        return [self._to_model(row) for row in rows]

    async def get_all(self) -> List[TagModel]:
        return [self._to_model(row) for row in await self.db.fetch_all(_SELECT_TAG)]

    async def get_by_id(self, tag_id: str) -> Optional[TagModel]:
        return self._to_model(await self.db.fetch_one(f"{_SELECT_TAG} WHERE id = ?", (tag_id,)))

    async def delete(self, tag_id: str) -> bool:
        if await self.get_by_id(tag_id) is None:
            return False

        await self.db.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
        return True

    async def get_by_resource_and_tag(self, resource_id: str, tag: str) -> Optional[TagModel]:
        """Find a specific tag on a resource by name (used to avoid duplicates)."""
        row = await self.db.fetch_one(
            f"{_SELECT_TAG} WHERE resource_id = ? AND tag_name = ?",
            (resource_id, tag),
        )
        return self._to_model(row)

    async def delete_by_resource_and_tag(self, resource_id: str, tag: str) -> bool:
        """Remove a specific tag from a resource by name, if it exists."""
        if await self.get_by_resource_and_tag(resource_id, tag) is None:
            return False

        await self.db.execute("DELETE FROM tags WHERE resource_id = ? AND tag = ?", (resource_id, tag))
        return True

    async def delete_all_for_resource(self, resource_id: str) -> None:
        """Remove every tag attached to a resource (used when the resource itself is deleted)."""
        await self.db.execute("DELETE FROM tags WHERE resource_id = ?", (resource_id,))

    @staticmethod
    def _to_model(row: Optional[Mapping[str, Any]]) -> Optional[TagModel]:
        return TagModel(**row) if row else None
