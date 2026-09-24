from typing import Optional

from pydantic import BaseModel

from core.common.serializers import UtcDateTime


class TagModel(BaseModel):
    """A `tag_resource_view` row: a tag plus the name of the resource it is on."""
    id: str
    resource_id: str
    # None when the resource can't be resolved (e.g. it's been deleted).
    resource_name: Optional[str] = None
    tag: str
    created_date: UtcDateTime
