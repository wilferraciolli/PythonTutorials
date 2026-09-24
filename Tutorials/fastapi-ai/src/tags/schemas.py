from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from core.common.api_response import ApiResponse
from core.common.base_dto import EmbeddedRef, FieldMetadata, LinkedResource
from core.common.serializers import format_utc_datetime


# --- Request: what the client sends -----------------------------------------

class TagCreateRequest(BaseModel):
    """
    Body of `POST /tags`. Also the `_data` of `GET /tags/template`, filled
    with blanks, so a create form starts from the same shape it sends.
    """
    resource_id: str = Field(..., min_length=1)
    tag: str = Field(..., min_length=1, max_length=50)


# --- DTO: what the application service returns ------------------------------

class TagDTO(LinkedResource):
    """A tag plus the links the caller may follow from it."""
    id: str
    resource_id: str
    # The resource_id's display name, embedded from tag_resource_view —
    # None when the resource can't be resolved (e.g. it's been deleted).
    resource: Optional[EmbeddedRef] = None
    tag: str
    created_date: datetime

    @field_serializer("created_date")
    def serialize_datetime(self, value: datetime) -> str:
        return format_utc_datetime(value)


class TagMetadata(BaseModel):
    """How the client should treat each field of `TagDTO`."""
    id: FieldMetadata
    resource_id: FieldMetadata
    tag: FieldMetadata
    created_date: FieldMetadata


class TagTemplateMetadata(BaseModel):
    """How the client should treat each field of the create template."""
    resource_id: FieldMetadata
    tag: FieldMetadata


# --- Response: the envelopes the service builds -----------------------------

TagResponse = ApiResponse[TagDTO, TagMetadata]
TagListResponse = ApiResponse[list[TagDTO], TagMetadata]
TagTemplateResponse = ApiResponse[TagCreateRequest, TagTemplateMetadata]
