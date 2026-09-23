import logging
from typing import Any, Dict, List, Optional
from uuid import uuid4

from api_response import API_PREFIX, envelope
from errors import ConflictError, ForbiddenError, NotFoundError
from group_permissions import Caller, GroupAccess, GroupPermissions
from models import Comment, CommentCreate, CommentUpdate, Link
from repositories.post_comment_repository import PostCommentRepository
from repositories.post_stats_repository import PostStatsRepository
from repositories.reaction_repository import ReactionRepository
from services.post_service import DELETED, PostService, author_name, now_iso

COMMENT_NOT_FOUND = "Comment not found"

logger = logging.getLogger(__name__)


class PostCommentService:
    """
    Comments and replies on a post, and likes on them (docs/social-groups.md).

    Every call first loads the post through PostService.get_post, which loads
    its group through GroupService.get_visible, so the group's visibility is
    checked on every request. Adding or deleting a comment refreshes the
    post's post_stats row (comments count 2 towards its score).
    """

    def __init__(
        self,
        comments: PostCommentRepository,
        stats: PostStatsRepository,
        reactions: ReactionRepository,
        post_service: PostService,
        permissions: Optional[GroupPermissions] = None,
    ) -> None:
        self.comments = comments
        self.stats = stats
        self.reactions = reactions
        self.post_service = post_service
        self.permissions = permissions or GroupPermissions()

    async def _index(self, comment_id: str, body: str, group_id: str) -> None:
        """Best effort, like posts: the search index never fails a write."""
        search = self.post_service.search
        if not search:
            return
        try:
            await search.index_comment(comment_id, body, group_id)
        except Exception:
            logger.exception("failed to index comment %s for search", comment_id)

    async def _unindex(self, comment_id: str) -> None:
        search = self.post_service.search
        if not search:
            return
        try:
            await search.remove_comment(comment_id)
        except Exception:
            logger.exception("failed to remove comment %s from search", comment_id)

    async def _mark_liked(self, caller: Caller, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        liked = await self.reactions.liked_ids(caller.id, "comment", (row["id"] for row in rows))
        for row in rows:
            row["liked_by_me"] = row["id"] in liked
        return rows

    async def _comment(self, caller: Caller, post_id: str, comment_id: str) -> Dict[str, Any]:
        comment = await self.comments.get(post_id, comment_id)
        if comment is None or comment["deleted_date"]:
            raise NotFoundError(COMMENT_NOT_FOUND)
        await self._mark_liked(caller, [comment])
        return comment

    async def list_comments(self, caller: Caller, group_id: str, post_id: str):
        access, post = await self.post_service.get_post(caller, group_id, post_id)
        return access, post, await self._mark_liked(caller, await self.comments.list_for_post(post_id))

    async def create_comment(self, caller: Caller, group_id: str, post_id: str, payload: CommentCreate):
        access, post = await self.post_service.get_post(caller, group_id, post_id)
        if post["deleted_date"]:
            raise ConflictError("Can't comment on a deleted post")
        if not self.permissions.can_post(caller, access):
            raise ForbiddenError("Only members can comment in this group")

        if payload.parentCommentId:
            parent = await self.comments.get(post_id, payload.parentCommentId)
            if parent is None:  # also catches a parent from a different post
                raise NotFoundError("The comment you are replying to was not found on this post")
            if parent["deleted_date"]:
                raise ConflictError("Can't reply to a deleted comment")

        comment_id = str(uuid4())
        now = now_iso()
        await self.comments.create(comment_id, post_id, payload.parentCommentId, caller.id, payload.body.strip(), now)
        await self.stats.refresh(post_id, now)
        await self._index(comment_id, payload.body.strip(), post["group_id"])
        return access, post, await self._comment(caller, post_id, comment_id)

    async def update_comment(
        self, caller: Caller, group_id: str, post_id: str, comment_id: str, payload: CommentUpdate
    ):
        access, post = await self.post_service.get_post(caller, group_id, post_id)
        comment = await self._comment(caller, post_id, comment_id)
        if comment["author_id"] != caller.id:  # nobody edits someone else's words, not even admins
            raise ForbiddenError("Only the author can edit a comment")

        await self.comments.update(comment_id, payload.body.strip(), now_iso())
        await self._index(comment_id, payload.body.strip(), post["group_id"])
        return access, post, await self._comment(caller, post_id, comment_id)

    async def delete_comment(self, caller: Caller, group_id: str, post_id: str, comment_id: str) -> None:
        access, _ = await self.post_service.get_post(caller, group_id, post_id)
        comment = await self._comment(caller, post_id, comment_id)
        if not self.permissions.can_delete_content(caller, access, comment["author_id"]):
            raise ForbiddenError("Only the author, the group owner or an admin can delete a comment")

        now = now_iso()
        await self.comments.soft_delete(comment_id, now)
        await self.stats.refresh(post_id, now)
        await self._unindex(comment_id)

    # --- likes (a comment's likes don't change its post's score)

    async def like(self, caller: Caller, group_id: str, post_id: str, comment_id: str):
        access, post = await self._likeable(caller, group_id, post_id, comment_id)
        await self.reactions.add(caller.id, "comment", comment_id, now_iso())
        return access, post, await self._comment(caller, post_id, comment_id)

    async def unlike(self, caller: Caller, group_id: str, post_id: str, comment_id: str):
        access, post = await self._likeable(caller, group_id, post_id, comment_id)
        await self.reactions.remove(caller.id, "comment", comment_id)
        return access, post, await self._comment(caller, post_id, comment_id)

    async def _likeable(self, caller: Caller, group_id: str, post_id: str, comment_id: str):
        access, post = await self.post_service.get_post(caller, group_id, post_id)
        await self._comment(caller, post_id, comment_id)
        if not self.permissions.can_post(caller, access):
            raise ForbiddenError("Only members can like comments in this group")
        return access, post

    # --- responses

    def to_comment(self, caller: Caller, access: GroupAccess, post: Dict[str, Any], row: Dict[str, Any]) -> Comment:
        deleted = bool(row.get("deleted_date"))
        base = f"{API_PREFIX}/groups/{post['group_id']}/posts/{post['id']}/comments"
        links: Dict[str, Link] = {}
        if not deleted:
            if self.permissions.can_post(caller, access):
                if not post.get("deleted_date"):
                    links["reply"] = Link(href=base, method="POST")
                if row.get("liked_by_me"):
                    links["unlike"] = Link(href=f"{base}/{row['id']}/like", method="DELETE")
                else:
                    links["like"] = Link(href=f"{base}/{row['id']}/like", method="PUT")
            if row.get("author_id") == caller.id:
                links["update"] = Link(href=f"{base}/{row['id']}", method="PUT")
            if self.permissions.can_delete_content(caller, access, row.get("author_id")):
                links["delete"] = Link(href=f"{base}/{row['id']}", method="DELETE")
        return Comment(
            id=row["id"],
            postId=row["post_id"],
            parentCommentId=row.get("parent_comment_id"),
            authorId=None if deleted else row.get("author_id"),
            authorName=author_name(row),
            body=DELETED if deleted else row["body"],
            isDeleted=deleted,
            likeCount=row.get("like_count", 0),
            likedByMe=bool(row.get("liked_by_me")),
            created_date=row["created_date"],
            updated_date=row["updated_date"],
            links=links,
        )

    def build_comment_response(
        self, caller: Caller, access: GroupAccess, post: Dict[str, Any], row: Dict[str, Any]
    ) -> Dict[str, Any]:
        return envelope(data_name="comment", data=self.to_comment(caller, access, post, row), metadata={}, meta_links={})

    def build_comments_response(
        self, caller: Caller, access: GroupAccess, post: Dict[str, Any], rows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        meta_links = {}
        if not post.get("deleted_date") and self.permissions.can_post(caller, access):
            meta_links["addComment"] = Link(
                href=f"{API_PREFIX}/groups/{post['group_id']}/posts/{post['id']}/comments", method="POST"
            )
        return envelope(
            data_name="comments",
            data=[self.to_comment(caller, access, post, row) for row in rows],
            metadata={"body": {"mandatory": True, "maxLength": 5000}},
            meta_links=meta_links,
        )
