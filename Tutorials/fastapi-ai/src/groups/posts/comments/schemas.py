from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from core.common.base_dto import LinkedResource
from core.common.serializers import format_utc_datetime


class CommentCreate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)
    parentCommentId: Optional[str] = None  # set to reply to a comment


class CommentUpdate(BaseModel):
    body: str = Field(min_length=1, max_length=5000)


class Comment(LinkedResource):
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
