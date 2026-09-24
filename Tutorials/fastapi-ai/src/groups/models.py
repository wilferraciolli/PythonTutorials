from typing import Optional

from pydantic import BaseModel

from core.common.serializers import UtcDateTime
from groups.enums import GroupVisibility


class GroupModel(BaseModel):
    """A `groups` row with its member and follower counts."""
    id: str
    name: str
    description: Optional[str] = None
    visibility: GroupVisibility
    # None once the owner leaves or is deleted: the group carries on.
    owner_id: Optional[str] = None
    created_by: Optional[str] = None
    created_date: UtcDateTime
    member_count: int = 0
    follower_count: int = 0


class GroupMemberModel(BaseModel):
    """A `group_members` row with the member's name (None if the user is gone)."""
    user_id: str
    name: Optional[str] = None
    joined_date: UtcDateTime


class GroupFollowerModel(BaseModel):
    """A `group_followers` row with the follower's name (None if the user is gone)."""
    user_id: str
    name: Optional[str] = None
    created_date: UtcDateTime


# --- Read models for the AI assistant's questions (social_query_repository.py)

class SocialPostModel(BaseModel):
    """A live post the caller can see, with its group, author and counts."""
    id: str
    group_id: str
    title: str
    body: str
    author_id: Optional[str] = None
    created_date: UtcDateTime
    group_name: str
    author_name: Optional[str] = None
    like_count: int = 0
    comment_count: int = 0
    score: int = 0


class SocialCommentModel(BaseModel):
    """A live comment the caller can see, with the post (and group) it is on."""
    id: str
    post_id: str
    group_id: str
    body: str


class GroupRefModel(BaseModel):
    """Just enough of a group to name it."""
    id: str
    name: str


class MyGroupModel(BaseModel):
    """A group the caller owns, belongs to or follows, with activity counts."""
    id: str
    name: str
    visibility: GroupVisibility
    is_owner: bool
    is_member: bool
    is_following: bool
    member_count: int = 0
    post_count: int = 0
    last_post_date: Optional[UtcDateTime] = None
