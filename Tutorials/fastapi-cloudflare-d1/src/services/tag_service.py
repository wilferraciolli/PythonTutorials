from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models import Tag, TagCreate
from repositories.tag_repository import TagRepository


class TagService:
    """Business logic for Tags, sitting between the router and the D1 repository."""

    def __init__(self, repository: TagRepository):
        self.repository = repository


    async def search_tags(self, term: Optional[str] = None) -> List[Tag]:
        rows = await self.repository.search_tags(term)

        return [self._row_to_tag(row) for row in rows]


    async def create_tag(
            self,
            tag_create: TagCreate) -> Tag:
        row = await self.repository.create(
            tag=tag_create.tag,
            resource_id=tag_create.resource_id,
            created_date=datetime.now(timezone.utc).isoformat(),
        )

        return self._row_to_tag(row)


    async def get_tag(self, id: int) -> Optional[Tag]:
        row = await self.repository.get_by_id(id)
        if not row:
            return None

        return self._row_to_tag(row)


    async def get_all_tags(self, resource_id : Optional[int] = None) -> List[Tag]:
        if resource_id:
            rows = await self.repository.get_all_by_resource_id(resource_id)
        else:
            rows = await self.repository.get_all()

        return [self._row_to_tag(row) for row in rows]


    async def delete_tag(self, id: int) -> bool:
       return await self.repository.delete(id)

    async def add_tag_if_missing(self, resource_id: int, tag_name: str) -> Tag:
        """Add a tag to a resource, or return the existing one if it's already there."""
        existing = await self.repository.get_by_resource_and_tag(resource_id, tag_name)
        if existing:
            return self._row_to_tag(existing)

        row = await self.repository.create(
            tag=tag_name,
            resource_id=resource_id,
            created_date=datetime.now(timezone.utc).isoformat(),
        )
        return self._row_to_tag(row)

    async def remove_tag_by_name(self, resource_id: int, tag_name: str) -> bool:
        """Remove a tag from a resource by name, if present."""
        return await self.repository.delete_by_resource_and_tag(resource_id, tag_name)

    async def delete_all_tags_for_resource(self, resource_id: int) -> None:
        """Remove every tag attached to a resource (e.g. when the resource is deleted)."""
        await self.repository.delete_all_for_resource(resource_id)

    @staticmethod
    def _row_to_tag(row: Dict[str, Any]) -> Tag:
        return Tag(
            id=row["id"],
            tag=row["tag"],
            resource_id=row["resource_id"],
            created_date=datetime.fromisoformat(row["created_date"]),
        )
