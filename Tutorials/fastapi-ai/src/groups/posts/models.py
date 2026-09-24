from typing import List, Optional

from pydantic import BaseModel, Field

from core.common.serializers import UtcDateTime
from groups.enums import GroupVisibility
from media.enums import MediaType


class TaggedPersonModel(BaseModel):
    """A `post_people_tags` row with the tagged user's name."""
    user_id: str
    name: str


class PostModel(BaseModel):
    """
    A `posts` row, joined with its author's name, its group and its
    post_stats counts. author_id None means "System" (seeded content);
    author_name None with an author_id means the user has been deleted.
    """
    id: str
    group_id: str
    author_id: Optional[str] = None
    title: str
    body: str
    created_date: UtcDateTime
    updated_date: UtcDateTime
    deleted_date: Optional[UtcDateTime] = None
    media_type: Optional[MediaType] = None
    media_id: Optional[str] = None
    media_url: Optional[str] = None
    media_title: Optional[str] = None
    media_author_name: Optional[str] = None
    media_author_url: Optional[str] = None
    author_name: Optional[str] = None
    group_name: str
    group_visibility: GroupVisibility
    group_owner_id: Optional[str] = None
    group_created_date: UtcDateTime
    like_count: int = 0
    comment_count: int = 0
    score: int = 0

    # Not columns: PostService.load_details fills these in for the caller.
    liked_by_me: bool = False
    tagged_people: List[TaggedPersonModel] = Field(default_factory=list)
