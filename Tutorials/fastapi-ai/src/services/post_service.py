from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from api_response import API_PREFIX, envelope
from errors import ConflictError, ForbiddenError, NotFoundError
from group_permissions import Caller, GroupAccess, GroupPermissions
from models import Link, Post, PostCreate, PostUpdate
from repositories.post_repository import PostRepository
from repositories.post_stats_repository import PostStatsRepository
from repositories.reaction_repository import ReactionRepository
from services.group_service import GroupService

DEFAULT_LIMIT = 50
MAX_LIMIT = 100

DELETED = "[deleted]"
SYSTEM_AUTHOR = "System"
DELETED_USER = "[deleted user]"

POST_NOT_FOUND = "Post not found"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def author_name(row: Dict[str, Any]) -> Optional[str]:
    """ "System" for seeded content, "[deleted user]" for a removed author, None once deleted."""
    if row.get("deleted_date"):
        return None
    if row.get("author_id") is None:
        return SYSTEM_AUTHOR
    return row.get("author_name") or DELETED_USER


class PostService:
    """
    Posts inside a group, and likes on them (docs/social-groups.md).

    Every call first loads the group through GroupService.get_visible, so a
    private group's posts 404 for non-members exactly like the group itself.
    Comments live in PostCommentService.
    """

    def __init__(
        self,
        posts: PostRepository,
        stats: PostStatsRepository,
        reactions: ReactionRepository,
        group_service: GroupService,
        permissions: Optional[GroupPermissions] = None,
    ) -> None:
        self.posts = posts
        self.stats = stats
        self.reactions = reactions
        self.group_service = group_service
        self.permissions = permissions or GroupPermissions()

    async def get_post(self, caller: Caller, group_id: str, post_id: str):
        """The group access and the post (deleted ones included), or NotFoundError."""
        access = await self.group_service.get_visible(caller, group_id)
        post = await self.posts.get(group_id, post_id)
        if post is None:
            raise NotFoundError(POST_NOT_FOUND)
        await self.mark_liked(caller, [post])
        return access, post

    async def mark_liked(self, caller: Caller, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        liked = await self.reactions.liked_ids(caller.id, "post", (row["id"] for row in rows))
        for row in rows:
            row["liked_by_me"] = row["id"] in liked
        return rows

    async def list_posts(self, caller: Caller, group_id: str, limit: int = DEFAULT_LIMIT):
        access = await self.group_service.get_visible(caller, group_id)
        rows = await self.posts.list_for_group(group_id, max(1, min(limit, MAX_LIMIT)))
        return access, await self.mark_liked(caller, rows)

    async def create_post(self, caller: Caller, group_id: str, payload: PostCreate):
        access = await self.group_service.get_visible(caller, group_id)
        if not self.permissions.can_post(caller, access):
            raise ForbiddenError("Only members can post in this group")

        post_id = str(uuid4())
        now = now_iso()
        await self.posts.create(post_id, group_id, caller.id, payload.title.strip(), payload.body.strip(), now)
        await self.stats.refresh(post_id, now)
        return await self.get_post(caller, group_id, post_id)

    async def update_post(self, caller: Caller, group_id: str, post_id: str, payload: PostUpdate):
        _, post = await self.get_post(caller, group_id, post_id)
        if post["deleted_date"]:
            raise NotFoundError(POST_NOT_FOUND)
        if post["author_id"] != caller.id:  # nobody edits someone else's words, not even admins
            raise ForbiddenError("Only the author can edit a post")

        await self.posts.update(
            post_id,
            now_iso(),
            title=payload.title.strip() if payload.title is not None else None,
            body=payload.body.strip() if payload.body is not None else None,
        )
        return await self.get_post(caller, group_id, post_id)

    async def delete_post(self, caller: Caller, group_id: str, post_id: str) -> None:
        access, post = await self.get_post(caller, group_id, post_id)
        if post["deleted_date"]:
            raise NotFoundError(POST_NOT_FOUND)
        if not self.permissions.can_delete_content(caller, access, post["author_id"]):
            raise ForbiddenError("Only the author, the group owner or an admin can delete a post")
        await self.posts.soft_delete(post_id, now_iso())

    # --- likes

    async def like(self, caller: Caller, group_id: str, post_id: str):
        access, post = await self._likeable(caller, group_id, post_id)
        now = now_iso()
        await self.reactions.add(caller.id, "post", post_id, now)
        await self.stats.refresh(post_id, now)
        return await self.get_post(caller, group_id, post_id)

    async def unlike(self, caller: Caller, group_id: str, post_id: str):
        await self._likeable(caller, group_id, post_id)
        await self.reactions.remove(caller.id, "post", post_id)
        await self.stats.refresh(post_id, now_iso())
        return await self.get_post(caller, group_id, post_id)

    async def _likeable(self, caller: Caller, group_id: str, post_id: str):
        access, post = await self.get_post(caller, group_id, post_id)
        if post["deleted_date"]:
            raise ConflictError("Can't like a deleted post")
        if not self.permissions.can_post(caller, access):
            raise ForbiddenError("Only members can like posts in this group")
        return access, post

    # --- responses

    def to_post(self, caller: Caller, access: GroupAccess, row: Dict[str, Any]) -> Post:
        deleted = bool(row.get("deleted_date"))
        return Post(
            id=row["id"],
            groupId=row["group_id"],
            groupName=row.get("group_name") or access.group["name"],
            authorId=None if deleted else row.get("author_id"),
            authorName=author_name(row),
            title=DELETED if deleted else row["title"],
            body=DELETED if deleted else row["body"],
            isDeleted=deleted,
            likeCount=row.get("like_count", 0),
            commentCount=row.get("comment_count", 0),
            likedByMe=bool(row.get("liked_by_me")),
            created_date=row["created_date"],
            updated_date=row["updated_date"],
            links=self.build_post_links(caller, access, row),
        )

    def build_post_links(self, caller: Caller, access: GroupAccess, row: Dict[str, Any]) -> Dict[str, Link]:
        group = f"{API_PREFIX}/groups/{row['group_id']}"
        base = f"{group}/posts/{row['id']}"
        links = {
            "self": Link(href=base, method="GET"),
            "group": Link(href=group, method="GET"),
            "comments": Link(href=f"{base}/comments", method="GET"),
        }
        if row.get("deleted_date"):
            return links
        if self.permissions.can_post(caller, access):
            links["addComment"] = Link(href=f"{base}/comments", method="POST")
            if row.get("liked_by_me"):
                links["unlike"] = Link(href=f"{base}/like", method="DELETE")
            else:
                links["like"] = Link(href=f"{base}/like", method="PUT")
        if row.get("author_id") == caller.id:
            links["update"] = Link(href=base, method="PUT")
        if self.permissions.can_delete_content(caller, access, row.get("author_id")):
            links["delete"] = Link(href=base, method="DELETE")
        return links

    def build_post_response(self, caller: Caller, access: GroupAccess, row: Dict[str, Any]) -> Dict[str, Any]:
        return envelope(data_name="post", data=self.to_post(caller, access, row), metadata=self._metadata(), meta_links={})

    def build_posts_response(self, caller: Caller, access: GroupAccess, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        meta_links = {}
        if self.permissions.can_post(caller, access):
            meta_links["createPost"] = Link(href=f"{API_PREFIX}/groups/{access.group['id']}/posts", method="POST")
        return envelope(
            data_name="posts",
            data=[self.to_post(caller, access, row) for row in rows],
            metadata=self._metadata(),
            meta_links=meta_links,
        )

    def _metadata(self) -> Dict[str, Any]:
        return {
            "title": {"mandatory": True, "maxLength": 200},
            "body": {"mandatory": True, "maxLength": 10000},
            "authorName": {"readOnly": True},
        }
