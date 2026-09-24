from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from core.common.base_dto import EmbeddedRef, LinkedResource
from core.common.serializers import format_utc_datetime


class TagCreate(BaseModel):
    resource_id: str = Field(..., min_length=1)
    tag: str = Field(..., min_length=1, max_length=50)


class Tag(LinkedResource):
    id: str
    resource_id: str
    # The resource_id's display name, embedded from tag_resource_view —
    # None when the resource can't be resolved (e.g. it's been deleted).
    resource: Optional[EmbeddedRef] = None
    tag: str
    created_date: datetime
    class Config:
        from_attributes = True

    @field_serializer("created_date")
    def serialize_datetime(self, value: datetime) -> str:
        return format_utc_datetime(value)
