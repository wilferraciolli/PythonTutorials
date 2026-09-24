from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from core.common.api_response import API_PREFIX
from core.common.base_dto import EmbeddedRef, FieldMetadata, Link
from tags.constants import LINK_CREATE_TAG, LINK_DELETE, LINK_SELF, TAG_DATA_NAME, TAGS_DATA_NAME
from tags.models import TagModel
from tags.schemas import (
    TagCreateRequest,
    TagDTO,
    TagListResponse,
    TagMetadata,
    TagResponse,
    TagTemplateMetadata,
    TagTemplateResponse,
)
from tags.tag_repository import TagRepository


class TagService:
    """Business logic for Tags, sitting between the router and the repository."""

    def __init__(self, repository: TagRepository):
        self.repository = repository

    async def search_tags(self, term: Optional[str] = None) -> List[TagDTO]:
        return [self.to_dto(model) for model in await self.repository.search_tags(term)]

    async def create_tag(self, request: TagCreateRequest) -> TagDTO:
        model = await self.repository.create(
            tag_id=str(uuid4()),
            tag=request.tag,
            resource_id=request.resource_id,
            created_date=datetime.now(timezone.utc).isoformat(),
        )
        return self.to_dto(model)

    async def get_tag(self, tag_id: str) -> Optional[TagDTO]:
        model = await self.repository.get_by_id(tag_id)
        return self.to_dto(model) if model else None

    async def get_all_tags(self, resource_id: Optional[str] = None) -> List[TagDTO]:
        if resource_id:
            models = await self.repository.get_all_by_resource_id(resource_id)
        else:
            models = await self.repository.get_all()

        return [self.to_dto(model) for model in models]

    async def delete_tag(self, tag_id: str) -> bool:
        return await self.repository.delete(tag_id)

    async def add_tag_if_missing(self, resource_id: str, tag_name: str) -> TagDTO:
        """Add a tag to a resource, or return the existing one if it's already there."""
        existing = await self.repository.get_by_resource_and_tag(resource_id, tag_name)
        if existing:
            return self.to_dto(existing)

        model = await self.repository.create(
            tag_id=str(uuid4()),
            tag=tag_name,
            resource_id=resource_id,
            created_date=datetime.now(timezone.utc).isoformat(),
        )
        return self.to_dto(model)

    async def remove_tag_by_name(self, resource_id: str, tag_name: str) -> bool:
        """Remove a tag from a resource by name, if present."""
        return await self.repository.delete_by_resource_and_tag(resource_id, tag_name)

    async def delete_all_tags_for_resource(self, resource_id: str) -> None:
        """Remove every tag attached to a resource (e.g. when the resource is deleted)."""
        await self.repository.delete_all_for_resource(resource_id)

    # --- responses

    def to_dto(self, model: TagModel) -> TagDTO:
        return TagDTO(
            id=model.id,
            resource_id=model.resource_id,
            resource=EmbeddedRef(id=model.resource_id, value=model.resource_name) if model.resource_name else None,
            tag=model.tag,
            created_date=model.created_date,
            links=self.build_links(model.id),
        )

    @staticmethod
    def build_links(tag_id: str) -> dict[str, Link]:
        """Resource-level Tag links, calculated per request."""
        url = f"{API_PREFIX}/tags/{tag_id}"
        return {
            LINK_SELF: Link(href=url, method="GET"),
            LINK_DELETE: Link(href=url, method="DELETE"),
        }

    @staticmethod
    def build_meta_links() -> dict[str, Link]:
        return {LINK_CREATE_TAG: Link(href=f"{API_PREFIX}/tags", method="POST")}

    @staticmethod
    def build_metadata() -> TagMetadata:
        return TagMetadata(
            id=FieldMetadata(readOnly=True, hidden=True),
            resource_id=FieldMetadata(mandatory=True),
            tag=FieldMetadata(mandatory=True),
            created_date=FieldMetadata(readOnly=True),
        )

    def build_response(self, tag: TagDTO) -> TagResponse:
        return TagResponse.of(TAG_DATA_NAME, tag, self.build_metadata(), self.build_meta_links())

    def build_list_response(self, tags: List[TagDTO]) -> TagListResponse:
        return TagListResponse.of(TAGS_DATA_NAME, tags, self.build_metadata(), self.build_meta_links())

    def build_template_response(self) -> TagTemplateResponse:
        # Blank values, so skip the create validation (min_length) on purpose.
        return TagTemplateResponse.of(
            TAG_DATA_NAME,
            TagCreateRequest.model_construct(resource_id="", tag=""),
            TagTemplateMetadata(
                resource_id=FieldMetadata(mandatory=True),
                tag=FieldMetadata(mandatory=True),
            ),
            self.build_meta_links(),
        )
