from pydantic import BaseModel

from core.common.api_response import ApiResponse
from core.common.base_dto import FieldMetadata
from groups.posts.schemas import PostDTO


class TimelineMetadata(BaseModel):
    """The timeline types to switch between, and the names of the people tagged in these posts."""
    type: FieldMetadata
    taggedUserIds: FieldMetadata


TimelineResponse = ApiResponse[list[PostDTO], TimelineMetadata]
