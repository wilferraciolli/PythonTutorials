import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import uuid4

from core.common.api_response import API_PREFIX, envelope
from core.common.errors import ConflictError, ForbiddenError, InvalidInputError, NotFoundError
from groups.group_permissions import Caller, GroupAccess, GroupPermissions
from media.media_providers import MediaLookup
from core.common.base_dto import Link
from groups.posts.schemas import MAX_TAGGED_PEOPLE, Post, PostCreate, PostMedia, PostUpdate
from media.enums import MediaType
from media.schemas import MediaRef
from groups.posts.post_people_tag_repository import PostPeopleTagRepository
from groups.posts.post_repository import PostRepository
from groups.posts.post_stats_repository import PostStatsRepository
from groups.posts.reaction_repository import ReactionRepository
from groups.group_service import GroupService

if TYPE_CHECKING:
    from groups.posts.post_search_service import PostSearchService

logger = logging.getLogger(__name__)

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
        media: Optional[MediaLookup] = None,
        search: Optional["PostSearchService"] = None,
        permissions: Optional[GroupPermissions] = None,
        people: Optional[PostPeopleTagRepository] = None,
    ) -> None:
        self.posts = posts
        self.stats = stats
        self.reactions = reactions
        self.group_service = group_service
        self.media = media
        self.search = search
        self.permissions = permissions or GroupPermissions()
        self.people = people or PostPeopleTagRepository(posts.db)

    async def reindex(self, post: Dict[str, Any]) -> None:
        """Best effort: search indexing never fails a write. Admin reindex picks up anything missed."""
        if not self.search:
            return
        try:
            await self.search.index_post(post)
        except Exception:
            logger.exception("failed to index post %s for search", post.get("id"))

    async def unindex(self, post_id: str) -> None:
        if not self.search:
            return
        try:
            await self.search.remove_post(post_id)
        except Exception:
            logger.exception("failed to remove post %s from search", post_id)

    async def get_post(self, caller: Caller, group_id: str, post_id: str):
        """The group access and the post (deleted ones included), or NotFoundError."""
        access = await self.group_service.get_visible(caller, group_id)
        post = await self.posts.get(group_id, post_id)
        if post is None:
            raise NotFoundError(POST_NOT_FOUND)
        await self.load_details(caller, [post])
        return access, post

    async def load_details(self, caller: Caller, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """What each post row needs for a response beyond the posts table: likes and tagged people."""
        await self.mark_liked(caller, rows)
        tagged = await self.people.for_posts(row["id"] for row in rows)
        for row in rows:
            row["tagged_people"] = tagged.get(row["id"], [])
        return rows

    async def mark_liked(self, caller: Caller, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        liked = await self.reactions.liked_ids(caller.id, "post", (row["id"] for row in rows))
        for row in rows:
            row["liked_by_me"] = row["id"] in liked
        return rows

    async def list_posts(self, caller: Caller, group_id: str, limit: int = DEFAULT_LIMIT):
        access = await self.group_service.get_visible(caller, group_id)
        rows = await self.posts.list_for_group(group_id, max(1, min(limit, MAX_LIMIT)))
        return access, await self.load_details(caller, rows)

    async def create_post(self, caller: Caller, group_id: str, payload: PostCreate):
        access = await self.group_service.get_visible(caller, group_id)
        if not self.permissions.can_post(caller, access):
            raise ForbiddenError("Only members can post in this group")
        # Looked up before anything is saved, so a bad media id doesn't leave a post behind.
        media = await self._resolve(payload.media) if payload.media else None
        people = await self._known_people(payload.taggedUserIds)

        post_id = str(uuid4())
        now = now_iso()
        await self.posts.create(post_id, group_id, caller.id, payload.title.strip(), payload.body.strip(), now)
        if media:
            await self.posts.set_media(post_id, media, now)
        if people:
            await self.people.replace(post_id, people, now)
        await self.stats.refresh(post_id, now)
        access, row = await self.get_post(caller, group_id, post_id)
        await self.reindex(row)
        return access, row

    async def update_post(self, caller: Caller, group_id: str, post_id: str, payload: PostUpdate):
        await self._own_post(caller, group_id, post_id)
        people = await self._known_people(payload.taggedUserIds) if payload.taggedUserIds is not None else None
        now = now_iso()
        await self.posts.update(
            post_id,
            now,
            title=payload.title.strip() if payload.title is not None else None,
            body=payload.body.strip() if payload.body is not None else None,
        )
        if people is not None:
            await self.people.replace(post_id, people, now)
        access, row = await self.get_post(caller, group_id, post_id)
        await self.reindex(row)
        return access, row

    async def delete_post(self, caller: Caller, group_id: str, post_id: str) -> None:
        access, post = await self.get_post(caller, group_id, post_id)
        if post["deleted_date"]:
            raise NotFoundError(POST_NOT_FOUND)
        if not self.permissions.can_delete_content(caller, access, post["author_id"]):
            raise ForbiddenError("Only the author, the group owner or an admin can delete a post")
        await self.posts.soft_delete(post_id, now_iso())
        await self.unindex(post_id)

    # --- media: one per post. Changing it is remove, then add another.

    async def set_media(self, caller: Caller, group_id: str, post_id: str, ref: MediaRef):
        await self._own_post(caller, group_id, post_id)
        await self.posts.set_media(post_id, await self._resolve(ref), now_iso())
        return await self.get_post(caller, group_id, post_id)

    async def remove_media(self, caller: Caller, group_id: str, post_id: str):
        await self._own_post(caller, group_id, post_id)
        await self.posts.set_media(post_id, None, now_iso())
        return await self.get_post(caller, group_id, post_id)

    async def _known_people(self, user_ids: List[str]) -> List[str]:
        """The ids in order without duplicates, or InvalidInputError naming the ones that aren't users."""
        unique = list(dict.fromkeys(user_id.strip() for user_id in user_ids if user_id.strip()))
        known = await self.people.existing_user_ids(unique)
        unknown = [user_id for user_id in unique if user_id not in known]
        if unknown:
            raise InvalidInputError(f"Can't tag unknown users: {', '.join(unknown)}")
        return unique

    async def _resolve(self, ref: MediaRef):
        if self.media is None:
            raise ConflictError("Media isn't available")
        return await self.media.resolve(ref)

    async def _own_post(self, caller: Caller, group_id: str, post_id: str):
        _, post = await self.get_post(caller, group_id, post_id)
        if post["deleted_date"]:
            raise NotFoundError(POST_NOT_FOUND)
        if post["author_id"] != caller.id:  # nobody edits someone else's words, not even admins
            raise ForbiddenError("Only the author can edit a post")
        return post

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
            media=None if deleted else self.to_media(row),
            taggedUserIds=[] if deleted else [person["user_id"] for person in row.get("tagged_people", [])],
            isDeleted=deleted,
            likeCount=row.get("like_count", 0),
            commentCount=row.get("comment_count", 0),
            likedByMe=bool(row.get("liked_by_me")),
            created_date=row["created_date"],
            updated_date=row["updated_date"],
            links=self.build_post_links(caller, access, row),
        )

    @staticmethod
    def to_media(row: Dict[str, Any]) -> Optional[PostMedia]:
        if not row.get("media_type"):
            return None
        return PostMedia(
            type=row["media_type"],
            id=row["media_id"],
            url=row.get("media_url"),
            title=row.get("media_title"),
            authorName=row.get("media_author_name"),
            authorUrl=row.get("media_author_url"),
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
            if row.get("media_type"):
                links["removeMedia"] = Link(href=f"{base}/media", method="DELETE")
            else:
                links["addMedia"] = Link(href=f"{base}/media", method="PUT")
        if self.permissions.can_delete_content(caller, access, row.get("author_id")):
            links["delete"] = Link(href=base, method="DELETE")
        return links

    def build_post_response(self, caller: Caller, access: GroupAccess, row: Dict[str, Any]) -> Dict[str, Any]:
        return envelope(
            data_name="post", data=self.to_post(caller, access, row), metadata=self._metadata([row]), meta_links={}
        )

    def build_posts_response(self, caller: Caller, access: GroupAccess, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        meta_links = {}
        if self.permissions.can_post(caller, access):
            meta_links["createPost"] = Link(href=f"{API_PREFIX}/groups/{access.group['id']}/posts", method="POST")
        return envelope(
            data_name="posts",
            data=[self.to_post(caller, access, row) for row in rows],
            metadata=self._metadata(rows),
            meta_links=meta_links,
        )

    @staticmethod
    def people_metadata(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Every person tagged in these posts as {id, value: full name}, for resolving taggedUserIds."""
        people: Dict[str, str] = {}
        for row in rows:
            if row.get("deleted_date"):
                continue
            for person in row.get("tagged_people", []):
                people.setdefault(person["user_id"], person["name"])
        return {
            "mandatory": False,
            "maxItems": MAX_TAGGED_PEOPLE,
            "values": [{"id": user_id, "value": name} for user_id, name in people.items()],
        }

    def _metadata(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "taggedUserIds": self.people_metadata(rows),
            "title": {"mandatory": True, "maxLength": 200},
            "body": {"mandatory": True, "maxLength": 10000},
            "media": {
                "mandatory": False,
                "values": [{"id": t.value, "value": t.value.title()} for t in MediaType],
            },
            "authorName": {"readOnly": True},
        }
