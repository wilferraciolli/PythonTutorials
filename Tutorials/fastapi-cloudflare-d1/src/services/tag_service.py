from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models import Tag, TagCreate
from repositories.tag_repository import TagRepository


class TagService:
    """Business logic for Tags, sitting between the router and the D1 repository."""

    def __init__(self, repository: TagRepository):
        self.repository = repository

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

    async def get_all_tags_for_resource(self, resource_id: int) -> List[Tag]:
        rows = await self.repository.get_all_by_resource_id(resource_id)

        return [self._row_to_tag(row) for row in rows]

    async def search_tags(self, term: Optional[str] = None) -> List[Tag]:
        rows = await self.repository.search_tags(term)

        return [self._row_to_tag(row) for row in rows]

    async def get_all_tags(self) -> List[Tag]:
        rows = await self.repository.get_all()

        return [self._row_to_tag(row) for row in rows]

    async def delete_tag(self, id: int) -> None:
        await self.repository.delete(id)

    @staticmethod
    def _row_to_tag(row: Dict[str, Any]) -> Tag:
        return Tag(
            id=row["id"],
            tag=row["tag"],
            resource_id=row["resource_id"],
            created_date=datetime.fromisoformat(row["created_date"]),
        )
