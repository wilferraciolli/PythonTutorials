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

    @staticmethod
    def _row_to_tag(row: Dict[str, Any]) -> Tag:
        return Tag(
            id=row["id"],
            tag=row["tag"],
            resource_id=row["resource_id"],
            created_date=datetime.fromisoformat(row["created_date"]),
        )
