from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from core.common.api_response import ApiResponse
from core.common.base_dto import FieldMetadata, LinkedResource
from core.common.serializers import format_utc_datetime
from groups.posts.comments.constants import BODY_MAX_LENGTH


# --- Request: what the client sends -----------------------------------------

class CommentCreateRequest(BaseModel):
    """Body of `POST .../comments`. Send `parentCommentId` to reply to a comment."""
    body: str = Field(min_length=1, max_length=BODY_MAX_LENGTH)
    parentCommentId: Optional[str] = None


class CommentUpdateRequest(BaseModel):
    """Body of `PUT .../comments/{comment_id}`."""
    body: str = Field(min_length=1, max_length=BODY_MAX_LENGTH)


# --- DTO: what the application service returns ------------------------------

class CommentDTO(LinkedResource):
    """A comment as the caller sees it, with the links they may follow."""
    id: str
    postId: str
    parentCommentId: Optional[str] = None
    authorId: Optional[str] = None
    authorName: Optional[str] = None
    body: str
    isDeleted: bool = False
    likeCount: int = 0
    likedByMe: bool = False
    created_date: datetime
    updated_date: datetime

    @field_serializer("created_date", "updated_date")
    def serialize_comment_dates(self, value: datetime) -> str:
        return format_utc_datetime(value)


class CommentMetadata(BaseModel):
    """How the client should treat the fields of `CommentDTO`."""
    body: FieldMetadata


# --- Response: the envelopes the service builds -----------------------------

CommentResponse = ApiResponse[CommentDTO, CommentMetadata]
CommentListResponse = ApiResponse[list[CommentDTO], CommentMetadata]
