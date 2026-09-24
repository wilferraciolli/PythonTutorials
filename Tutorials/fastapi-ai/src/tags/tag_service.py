from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from core.common.api_response import API_PREFIX, envelope
from core.common.base_dto import EmbeddedRef, Link
from tags.schemas import Tag, TagCreate
from tags.tag_repository import TagRepository


class TagService:
    """Business logic for Tags, sitting between the router and the D1 repository."""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    def build_template_response(self) -> Dict[str, Any]:
        """
        Build a create-template response.

        Templates use the create DTO shape, so server-managed fields like id
        and created_date are omitted entirely.
        """
        template = {
            "id": "",
            "resource_id": "",
            "tag": "",
            "created_date": ""
        }

        return envelope(
            "tag",
            template,
            self._template_metadata(),
            self._meta_links(),
        )

    async def search_tags(self, term: Optional[str] = None) -> List[Tag]:
        rows = await self.repository.search_tags(term)

        return [self._row_to_tag(row) for row in rows]


    async def create_tag(
            self,
            tag_create: TagCreate) -> Tag:
        row = await self.repository.create(
            id=str(uuid4()),
            tag=tag_create.tag,
            resource_id=tag_create.resource_id,
            created_date=datetime.now(timezone.utc).isoformat(),
        )

        return self._row_to_tag(row)


    async def get_tag(self, id: str) -> Optional[Tag]:
        row = await self.repository.get_by_id(id)
        if not row:
            return None

        return self._row_to_tag(row)


    async def get_all_tags(self, resource_id : Optional[str] = None) -> List[Tag]:
        if resource_id:
            rows = await self.repository.get_all_by_resource_id(resource_id)
        else:
            rows = await self.repository.get_all()

        return [self._row_to_tag(row) for row in rows]


    async def delete_tag(self, id: str) -> bool:
       return await self.repository.delete(id)

    async def add_tag_if_missing(self, resource_id: str, tag_name: str) -> Tag:
        """Add a tag to a resource, or return the existing one if it's already there."""
        existing = await self.repository.get_by_resource_and_tag(resource_id, tag_name)
        if existing:
            return self._row_to_tag(existing)

        row = await self.repository.create(
            id=str(uuid4()),
            tag=tag_name,
            resource_id=resource_id,
            created_date=datetime.now(timezone.utc).isoformat(),
        )
        return self._row_to_tag(row)

    async def remove_tag_by_name(self, resource_id: str, tag_name: str) -> bool:
        """Remove a tag from a resource by name, if present."""
        return await self.repository.delete_by_resource_and_tag(resource_id, tag_name)

    async def delete_all_tags_for_resource(self, resource_id: str) -> None:
        """Remove every tag attached to a resource (e.g. when the resource is deleted)."""
        await self.repository.delete_all_for_resource(resource_id)

    def build_response(
        self,
        data_name: str,
        data: Any,
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Build the full Tag response envelope for this stateless request.

        Metadata and links are calculated here in the application service,
        because they can depend on business rules and future permissions.
        """
        tag = data if isinstance(data, Tag) else None
        return envelope(
            data_name,
            data,
            self._metadata(tag),
            self._meta_links(),
            messages,
        )

    def _row_to_tag(self, row: Dict[str, Any]) -> Tag:
        tag_id = row["id"]
        resource_name = row.get("resource_name") if hasattr(row, "get") else row["resource_name"]
        tag = Tag(
            id=tag_id,
            tag=row["tag"],
            resource_id=row["resource_id"],
            resource=EmbeddedRef(id=row["resource_id"], value=resource_name) if resource_name else None,
            created_date=datetime.fromisoformat(row["created_date"]),
        )
        tag.links = self._links(tag)
        return tag

    def _links(
        self,
        tag: Tag,
        *,
        can_delete: bool = True,
    ) -> Dict[str, Link]:
        """Resource-level Tag links, calculated per request."""
        links = {
            "self": Link(href=f"{API_PREFIX}/tags/{tag.id}", method="GET"),
        }

        if can_delete:
            links["delete"] = Link(href=f"{API_PREFIX}/tags/{tag.id}", method="DELETE")

        return links

    def _metadata(self, tag: Optional[Tag] = None) -> Dict[str, Any]:
        """Field metadata for Tag payloads, calculated per request."""
        return {
            "id": {
                "readOnly": True,
                "hidden": True,
            },
            "resource_id": {
                "mandatory": True
            },
            "tag": {
                "mandatory": True,
            },
            "created_date": {
                "readOnly": True
            }
        }

    def _template_metadata(self) -> Dict[str, Any]:
        """Metadata for a create template: only fields the client can submit."""
        return {
            "resource_id": {
                "mandatory": True
            },
            "tag": {
                "mandatory": True,
            },
        }

    def _meta_links(self, *, can_create: bool = True) -> Dict[str, Link]:
        """Collection-level Tag links, calculated per request."""
        if not can_create:
            return {}

        return {
            "createTag": Link(href=f"{API_PREFIX}/tags", method="POST"),
        }
