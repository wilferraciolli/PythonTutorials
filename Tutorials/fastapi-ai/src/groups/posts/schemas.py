from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_serializer

from core.common.api_response import ApiResponse
from core.common.base_dto import FieldMetadata, LinkedResource
from core.common.serializers import format_utc_datetime
from groups.posts.constants import BODY_MAX_LENGTH, MAX_TAGGED_PEOPLE, TITLE_MAX_LENGTH
from media.enums import MediaType
from media.schemas import MediaRefRequest


# --- Request: what the client sends -----------------------------------------

class PostCreateRequest(BaseModel):
    """Body of `POST /groups/{group_id}/posts`."""
    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    body: str = Field(min_length=1, max_length=BODY_MAX_LENGTH)
    media: Optional[MediaRefRequest] = None
    # User ids of the people tagged in the post; names come back in _metadata.
    taggedUserIds: List[str] = Field(default_factory=list, max_length=MAX_TAGGED_PEOPLE)


class PostUpdateRequest(BaseModel):
    """Body of `PUT .../posts/{post_id}`. Only the fields sent are changed."""
    # Media isn't edited here: remove it and add another (PUT/DELETE .../media).
    title: Optional[str] = Field(None, min_length=1, max_length=TITLE_MAX_LENGTH)
    body: Optional[str] = Field(None, min_length=1, max_length=BODY_MAX_LENGTH)
    # None leaves the tagged people as they are; [] removes them all.
    taggedUserIds: Optional[List[str]] = Field(None, max_length=MAX_TAGGED_PEOPLE)


# --- DTO: what the application service returns ------------------------------

class PostMediaDTO(BaseModel):
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


class PostDTO(LinkedResource):
    """A post as the caller sees it, with the links they may follow."""
    id: str
    groupId: str
    groupName: str
    authorId: Optional[str] = None
    authorName: Optional[str] = None  # "System" for seeded posts, "[deleted user]", None when deleted
    title: str
    body: str
    media: Optional[PostMediaDTO] = None
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


class PostSearchHitDTO(BaseModel):
    """A post matching a search (for the assistant), with the comment that matched, if any."""
    id: str
    group_id: str
    group: str
    title: str
    author: Optional[str] = None
    created_date: datetime
    likes: int
    comments: int
    snippet: str
    matching_comment: Optional[str] = None
    keywordMatch: bool
    score: float

    @field_serializer("created_date")
    def serialize_created_date(self, value: datetime) -> str:
        return format_utc_datetime(value)


class PostIndexCountsDTO(BaseModel):
    """How many posts and comments a search backfill embedded."""
    posts: int
    comments: int


class PostMetadata(BaseModel):
    """How the client should treat the fields of `PostDTO`."""
    taggedUserIds: FieldMetadata
    title: FieldMetadata
    body: FieldMetadata
    media: FieldMetadata
    authorName: FieldMetadata


# --- Response: the envelopes the service builds -----------------------------

PostResponse = ApiResponse[PostDTO, PostMetadata]
PostListResponse = ApiResponse[list[PostDTO], PostMetadata]
