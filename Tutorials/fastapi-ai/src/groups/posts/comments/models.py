from typing import Optional

from pydantic import BaseModel

from core.common.serializers import UtcDateTime


class CommentModel(BaseModel):
    """
    A `comments` row with its author's name and like count. Deleting is a
    soft delete (deleted_date), so replies keep their parent.
    """
    id: str
    post_id: str
    parent_comment_id: Optional[str] = None
    author_id: Optional[str] = None
    body: str
    created_date: UtcDateTime
    updated_date: UtcDateTime
    deleted_date: Optional[UtcDateTime] = None
    author_name: Optional[str] = None
    like_count: int = 0

    # Not a column: CommentService fills it in for the caller.
    liked_by_me: bool = False
