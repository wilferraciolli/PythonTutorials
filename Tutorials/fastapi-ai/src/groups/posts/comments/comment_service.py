import logging
from typing import Dict, List, Optional
from uuid import uuid4

from core.common.api_response import API_PREFIX
from core.common.base_dto import FieldMetadata, Link
from core.common.errors import ConflictError, ForbiddenError, NotFoundError
from core.security.authorization import Caller
from groups.group_permissions import GroupAccess, GroupPermissions
from groups.posts.comments.comment_repository import CommentRepository
from groups.posts.comments.constants import (
    BODY_MAX_LENGTH,
    COMMENT_DATA_NAME,
    COMMENT_NOT_FOUND,
    COMMENTS_DATA_NAME,
    LINK_ADD_COMMENT,
    LINK_DELETE,
    LINK_LIKE,
    LINK_REPLY,
    LINK_UNLIKE,
    LINK_UPDATE,
)
from groups.posts.comments.models import CommentModel
from groups.posts.comments.schemas import (
    CommentCreateRequest,
    CommentDTO,
    CommentListResponse,
    CommentMetadata,
    CommentResponse,
    CommentUpdateRequest,
)
from groups.posts.constants import DELETED
from groups.posts.models import PostModel
from groups.posts.post_service import PostService, display_author, now_iso
from groups.posts.post_stats_repository import PostStatsRepository
from groups.posts.reaction_repository import ReactionRepository

logger = logging.getLogger(__name__)


class CommentService:
    """
    Comments and replies on a post, and likes on them (docs/social-groups.md).

    Every call first loads the post through PostService.get_post, which loads
    its group through GroupService.get_visible, so the group's visibility is
    checked on every request. Adding or deleting a comment refreshes the
    post's post_stats row (comments count 2 towards its score).
    """

    def __init__(
        self,
        comments: CommentRepository,
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

    async def _mark_liked(self, caller: Caller, comments: List[CommentModel]) -> List[CommentModel]:
        liked = await self.reactions.liked_ids(caller.user_id, "comment", (comment.id for comment in comments))
        for comment in comments:
            comment.liked_by_me = comment.id in liked
        return comments

    async def _comment(self, caller: Caller, post_id: str, comment_id: str) -> CommentModel:
        comment = await self.comments.get(post_id, comment_id)
        if comment is None or comment.deleted_date:
            raise NotFoundError(COMMENT_NOT_FOUND)
        await self._mark_liked(caller, [comment])
        return comment

    async def list_comments(
        self, caller: Caller, group_id: str, post_id: str
    ) -> tuple[GroupAccess, PostModel, List[CommentModel]]:
        access, post = await self.post_service.get_post(caller, group_id, post_id)
        return access, post, await self._mark_liked(caller, await self.comments.list_for_post(post_id))

    async def create_comment(
        self, caller: Caller, group_id: str, post_id: str, request: CommentCreateRequest
    ) -> tuple[GroupAccess, PostModel, CommentModel]:
        access, post = await self.post_service.get_post(caller, group_id, post_id)
        if post.deleted_date:
            raise ConflictError("Can't comment on a deleted post")
        if not self.permissions.can_post(caller, access):
            raise ForbiddenError("Only members can comment in this group")

        if request.parentCommentId:
            parent = await self.comments.get(post_id, request.parentCommentId)
            if parent is None:  # also catches a parent from a different post
                raise NotFoundError("The comment you are replying to was not found on this post")
            if parent.deleted_date:
                raise ConflictError("Can't reply to a deleted comment")

        comment_id = str(uuid4())
        now = now_iso()
        body = request.body.strip()
        await self.comments.create(comment_id, post_id, request.parentCommentId, caller.user_id, body, now)
        await self.stats.refresh(post_id, now)
        await self._index(comment_id, body, post.group_id)
        return access, post, await self._comment(caller, post_id, comment_id)

    async def update_comment(
        self, caller: Caller, group_id: str, post_id: str, comment_id: str, request: CommentUpdateRequest
    ) -> tuple[GroupAccess, PostModel, CommentModel]:
        access, post = await self.post_service.get_post(caller, group_id, post_id)
        comment = await self._comment(caller, post_id, comment_id)
        if comment.author_id != caller.user_id:  # nobody edits someone else's words, not even admins
            raise ForbiddenError("Only the author can edit a comment")

        body = request.body.strip()
        await self.comments.update(comment_id, body, now_iso())
        await self._index(comment_id, body, post.group_id)
        return access, post, await self._comment(caller, post_id, comment_id)

    async def delete_comment(self, caller: Caller, group_id: str, post_id: str, comment_id: str) -> None:
        access, _ = await self.post_service.get_post(caller, group_id, post_id)
        comment = await self._comment(caller, post_id, comment_id)
        if not self.permissions.can_delete_content(caller, access, comment.author_id):
            raise ForbiddenError("Only the author, the group owner or an admin can delete a comment")

        now = now_iso()
        await self.comments.soft_delete(comment_id, now)
        await self.stats.refresh(post_id, now)
        await self._unindex(comment_id)

    # --- likes (a comment's likes don't change its post's score)

    async def like(
        self, caller: Caller, group_id: str, post_id: str, comment_id: str
    ) -> tuple[GroupAccess, PostModel, CommentModel]:
        access, post = await self._likeable(caller, group_id, post_id, comment_id)
        await self.reactions.add(caller.user_id, "comment", comment_id, now_iso())
        return access, post, await self._comment(caller, post_id, comment_id)

    async def unlike(
        self, caller: Caller, group_id: str, post_id: str, comment_id: str
    ) -> tuple[GroupAccess, PostModel, CommentModel]:
        access, post = await self._likeable(caller, group_id, post_id, comment_id)
        await self.reactions.remove(caller.user_id, "comment", comment_id)
        return access, post, await self._comment(caller, post_id, comment_id)

    async def _likeable(
        self, caller: Caller, group_id: str, post_id: str, comment_id: str
    ) -> tuple[GroupAccess, PostModel]:
        access, post = await self.post_service.get_post(caller, group_id, post_id)
        await self._comment(caller, post_id, comment_id)
        if not self.permissions.can_post(caller, access):
            raise ForbiddenError("Only members can like comments in this group")
        return access, post

    # --- responses

    def to_dto(self, caller: Caller, access: GroupAccess, post: PostModel, comment: CommentModel) -> CommentDTO:
        deleted = bool(comment.deleted_date)
        return CommentDTO(
            id=comment.id,
            postId=comment.post_id,
            parentCommentId=comment.parent_comment_id,
            authorId=None if deleted else comment.author_id,
            authorName=display_author(comment.deleted_date, comment.author_id, comment.author_name),
            body=DELETED if deleted else comment.body,
            isDeleted=deleted,
            likeCount=comment.like_count,
            likedByMe=comment.liked_by_me,
            created_date=comment.created_date,
            updated_date=comment.updated_date,
            links=self.build_links(caller, access, post, comment),
        )

    def build_links(
        self, caller: Caller, access: GroupAccess, post: PostModel, comment: CommentModel
    ) -> Dict[str, Link]:
        base = f"{API_PREFIX}/groups/{post.group_id}/posts/{post.id}/comments"
        links: Dict[str, Link] = {}
        if comment.deleted_date:
            return links
        if self.permissions.can_post(caller, access):
            if not post.deleted_date:
                links[LINK_REPLY] = Link(href=base, method="POST")
            if comment.liked_by_me:
                links[LINK_UNLIKE] = Link(href=f"{base}/{comment.id}/like", method="DELETE")
            else:
                links[LINK_LIKE] = Link(href=f"{base}/{comment.id}/like", method="PUT")
        if comment.author_id == caller.user_id:
            links[LINK_UPDATE] = Link(href=f"{base}/{comment.id}", method="PUT")
        if self.permissions.can_delete_content(caller, access, comment.author_id):
            links[LINK_DELETE] = Link(href=f"{base}/{comment.id}", method="DELETE")
        return links

    @staticmethod
    def build_metadata() -> CommentMetadata:
        return CommentMetadata(body=FieldMetadata(mandatory=True, maxLength=BODY_MAX_LENGTH))

    def build_comment_response(
        self, caller: Caller, access: GroupAccess, post: PostModel, comment: CommentModel
    ) -> CommentResponse:
        return CommentResponse.of(
            COMMENT_DATA_NAME, self.to_dto(caller, access, post, comment), self.build_metadata()
        )

    def build_comments_response(
        self, caller: Caller, access: GroupAccess, post: PostModel, comments: List[CommentModel]
    ) -> CommentListResponse:
        meta_links = {}
        if not post.deleted_date and self.permissions.can_post(caller, access):
            meta_links[LINK_ADD_COMMENT] = Link(
                href=f"{API_PREFIX}/groups/{post.group_id}/posts/{post.id}/comments", method="POST"
            )
        return CommentListResponse.of(
            COMMENTS_DATA_NAME,
            [self.to_dto(caller, access, post, comment) for comment in comments],
            self.build_metadata(),
            meta_links,
        )
