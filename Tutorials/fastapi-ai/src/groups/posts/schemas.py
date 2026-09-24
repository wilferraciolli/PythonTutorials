from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_serializer

from core.common.base_dto import LinkedResource
from core.common.serializers import format_utc_datetime
from media.enums import MediaType
from media.schemas import MediaRef


class PostMedia(BaseModel):
    """
    A post's media. `url` is the image or GIF to show (None for YouTube: build
    the embed from `id`). `title` is the image's alt text. The author fields are
    the Unsplash photographer, for the attribution Unsplash requires.
    """
    type: MediaType
    id: str
    url: Optional[str] = None
    title: Optional[str] = None
    authorName: Optional[str] = None
    authorUrl: Optional[str] = None


MAX_TAGGED_PEOPLE = 20


class PostCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10000)
    media: Optional[MediaRef] = None
    # User ids of the people tagged in the post; names come back in _metadata.
    taggedUserIds: List[str] = Field(default_factory=list, max_length=MAX_TAGGED_PEOPLE)


class PostUpdate(BaseModel):
    # Media isn't edited here: remove it and add another (PUT/DELETE .../media).
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    body: Optional[str] = Field(None, min_length=1, max_length=10000)
    # None leaves the tagged people as they are; [] removes them all.
    taggedUserIds: Optional[List[str]] = Field(None, max_length=MAX_TAGGED_PEOPLE)


class Post(LinkedResource):
    id: str
    groupId: str
    groupName: str
    authorId: Optional[str] = None
    authorName: Optional[str] = None  # "System" for seeded posts, "[deleted user]", None when deleted
    title: str
    body: str
    media: Optional[PostMedia] = None
    # Ids of the people tagged in the post; their names are in _metadata.taggedUserIds.values.
    taggedUserIds: List[str] = Field(default_factory=list)
    isDeleted: bool = False
    likeCount: int = 0
    commentCount: int = 0
    likedByMe: bool = False
    created_date: datetime
    updated_date: datetime

    @field_serializer("created_date", "updated_date")
    def serialize_post_dates(self, value: datetime) -> str:
        return format_utc_datetime(value)
