import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional
from uuid import uuid4

from core.common.api_response import API_PREFIX
from core.common.base_dto import EmbeddedRef, FieldMetadata, Link
from core.common.errors import ConflictError, ForbiddenError, InvalidInputError, NotFoundError
from core.security.authorization import Caller
from groups.group_permissions import GroupAccess, GroupPermissions
from groups.group_service import GroupService
from groups.posts.constants import (
    BODY_MAX_LENGTH,
    DEFAULT_LIMIT,
    DELETED,
    DELETED_USER,
    LINK_ADD_COMMENT,
    LINK_ADD_MEDIA,
    LINK_COMMENTS,
    LINK_CREATE_POST,
    LINK_DELETE,
    LINK_GROUP,
    LINK_LIKE,
    LINK_REMOVE_MEDIA,
    LINK_SELF,
    LINK_UNLIKE,
    LINK_UPDATE,
    MAX_LIMIT,
    MAX_TAGGED_PEOPLE,
    POST_DATA_NAME,
    POST_NOT_FOUND,
    POSTS_DATA_NAME,
    SYSTEM_AUTHOR,
    TITLE_MAX_LENGTH,
)
from groups.posts.models import PostModel
from groups.posts.post_people_tag_repository import PostPeopleTagRepository
from groups.posts.post_repository import PostRepository
from groups.posts.post_stats_repository import PostStatsRepository
from groups.posts.reaction_repository import ReactionRepository
from groups.posts.schemas import (
    PostCreateRequest,
    PostDTO,
    PostListResponse,
    PostMediaDTO,
    PostMetadata,
    PostResponse,
    PostUpdateRequest,
)
from media.enums import MediaType
from media.media_providers import MediaLookup, ResolvedMedia
from media.schemas import MediaRefRequest

if TYPE_CHECKING:
    from groups.posts.post_search_service import PostSearchService

logger = logging.getLogger(__name__)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def display_author(deleted_date: Optional[datetime], author_id: Optional[str], author_name: Optional[str]) -> Optional[str]:
    """"System" for seeded content, "[deleted user]" for a removed author, None once the content is deleted."""
    if deleted_date:
        return None
    if author_id is None:
        return SYSTEM_AUTHOR
    return author_name or DELETED_USER


class PostService:
    """
    Posts inside a group, and likes on them (docs/social-groups.md).

    Every call first loads the group through GroupService.get_visible, so a
    private group's posts 404 for non-members exactly like the group itself.
    Comments live in CommentService.
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

    async def reindex(self, post: PostModel) -> None:
        """Best effort: search indexing never fails a write. Admin reindex picks up anything missed."""
        if not self.search:
            return
        try:
            await self.search.index_post(post)
        except Exception:
            logger.exception("failed to index post %s for search", post.id)

    async def unindex(self, post_id: str) -> None:
        if not self.search:
            return
        try:
            await self.search.remove_post(post_id)
        except Exception:
            logger.exception("failed to remove post %s from search", post_id)

    async def get_post(self, caller: Caller, group_id: str, post_id: str) -> tuple[GroupAccess, PostModel]:
        """The group access and the post (deleted ones included), or NotFoundError."""
        access = await self.group_service.get_visible(caller, group_id)
        post = await self.posts.get(group_id, post_id)
        if post is None:
            raise NotFoundError(POST_NOT_FOUND)
        await self.load_details(caller, [post])
        return access, post

    async def load_details(self, caller: Caller, posts: List[PostModel]) -> List[PostModel]:
        """Fill in what each post needs for a response beyond its row: likes and tagged people."""
        liked = await self.reactions.liked_ids(caller.user_id, "post", (post.id for post in posts))
        tagged = await self.people.for_posts(post.id for post in posts)
        for post in posts:
            post.liked_by_me = post.id in liked
            post.tagged_people = tagged.get(post.id, [])
        return posts

    async def list_posts(
        self, caller: Caller, group_id: str, limit: int = DEFAULT_LIMIT
    ) -> tuple[GroupAccess, List[PostModel]]:
        access = await self.group_service.get_visible(caller, group_id)
        posts = await self.posts.list_for_group(group_id, max(1, min(limit, MAX_LIMIT)))
        return access, await self.load_details(caller, posts)

    async def create_post(
        self, caller: Caller, group_id: str, request: PostCreateRequest
    ) -> tuple[GroupAccess, PostModel]:
        access = await self.group_service.get_visible(caller, group_id)
        if not self.permissions.can_post(caller, access):
            raise ForbiddenError("Only members can post in this group")
        # Looked up before anything is saved, so a bad media id doesn't leave a post behind.
        media = await self._resolve(request.media) if request.media else None
        people = await self._known_people(request.taggedUserIds)

        post_id = str(uuid4())
        now = now_iso()
        await self.posts.create(post_id, group_id, caller.user_id, request.title.strip(), request.body.strip(), now)
        if media:
            await self.posts.set_media(post_id, media, now)
        if people:
            await self.people.replace(post_id, people, now)
        await self.stats.refresh(post_id, now)
        access, post = await self.get_post(caller, group_id, post_id)
        await self.reindex(post)
        return access, post

    async def update_post(
        self, caller: Caller, group_id: str, post_id: str, request: PostUpdateRequest
    ) -> tuple[GroupAccess, PostModel]:
        await self._own_post(caller, group_id, post_id)
        people = await self._known_people(request.taggedUserIds) if request.taggedUserIds is not None else None
        now = now_iso()
        await self.posts.update(
            post_id,
            now,
            title=request.title.strip() if request.title is not None else None,
            body=request.body.strip() if request.body is not None else None,
        )
        if people is not None:
            await self.people.replace(post_id, people, now)
        access, post = await self.get_post(caller, group_id, post_id)
        await self.reindex(post)
        return access, post

    async def delete_post(self, caller: Caller, group_id: str, post_id: str) -> None:
        access, post = await self.get_post(caller, group_id, post_id)
        if post.deleted_date:
            raise NotFoundError(POST_NOT_FOUND)
        if not self.permissions.can_delete_content(caller, access, post.author_id):
            raise ForbiddenError("Only the author, the group owner or an admin can delete a post")
        await self.posts.soft_delete(post_id, now_iso())
        await self.unindex(post_id)

    # --- media: one per post. Changing it is remove, then add another.

    async def set_media(
        self, caller: Caller, group_id: str, post_id: str, ref: MediaRefRequest
    ) -> tuple[GroupAccess, PostModel]:
        await self._own_post(caller, group_id, post_id)
        await self.posts.set_media(post_id, await self._resolve(ref), now_iso())
        return await self.get_post(caller, group_id, post_id)

    async def remove_media(self, caller: Caller, group_id: str, post_id: str) -> tuple[GroupAccess, PostModel]:
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

    async def _resolve(self, ref: MediaRefRequest) -> ResolvedMedia:
        if self.media is None:
            raise ConflictError("Media isn't available")
        return await self.media.resolve(ref)

    async def _own_post(self, caller: Caller, group_id: str, post_id: str) -> PostModel:
        _, post = await self.get_post(caller, group_id, post_id)
        if post.deleted_date:
            raise NotFoundError(POST_NOT_FOUND)
        if post.author_id != caller.user_id:  # nobody edits someone else's words, not even admins
            raise ForbiddenError("Only the author can edit a post")
        return post

    # --- likes

    async def like(self, caller: Caller, group_id: str, post_id: str) -> tuple[GroupAccess, PostModel]:
        await self._likeable(caller, group_id, post_id)
        now = now_iso()
        await self.reactions.add(caller.user_id, "post", post_id, now)
        await self.stats.refresh(post_id, now)
        return await self.get_post(caller, group_id, post_id)

    async def unlike(self, caller: Caller, group_id: str, post_id: str) -> tuple[GroupAccess, PostModel]:
        await self._likeable(caller, group_id, post_id)
        await self.reactions.remove(caller.user_id, "post", post_id)
        await self.stats.refresh(post_id, now_iso())
        return await self.get_post(caller, group_id, post_id)

    async def _likeable(self, caller: Caller, group_id: str, post_id: str) -> tuple[GroupAccess, PostModel]:
        access, post = await self.get_post(caller, group_id, post_id)
        if post.deleted_date:
            raise ConflictError("Can't like a deleted post")
        if not self.permissions.can_post(caller, access):
            raise ForbiddenError("Only members can like posts in this group")
        return access, post

    # --- responses

    def to_dto(self, caller: Caller, access: GroupAccess, post: PostModel) -> PostDTO:
        deleted = bool(post.deleted_date)
        return PostDTO(
            id=post.id,
            groupId=post.group_id,
            groupName=post.group_name,
            authorId=None if deleted else post.author_id,
            authorName=display_author(post.deleted_date, post.author_id, post.author_name),
            title=DELETED if deleted else post.title,
            body=DELETED if deleted else post.body,
            media=None if deleted else self.to_media_dto(post),
            taggedUserIds=[] if deleted else [person.user_id for person in post.tagged_people],
            isDeleted=deleted,
            likeCount=post.like_count,
            commentCount=post.comment_count,
            likedByMe=post.liked_by_me,
            created_date=post.created_date,
            updated_date=post.updated_date,
            links=self.build_post_links(caller, access, post),
        )

    @staticmethod
    def to_media_dto(post: PostModel) -> Optional[PostMediaDTO]:
        if not post.media_type:
            return None
        return PostMediaDTO(
            type=post.media_type,
            id=post.media_id,
            url=post.media_url,
            title=post.media_title,
            authorName=post.media_author_name,
            authorUrl=post.media_author_url,
        )

    def build_post_links(self, caller: Caller, access: GroupAccess, post: PostModel) -> Dict[str, Link]:
        group = f"{API_PREFIX}/groups/{post.group_id}"
        base = f"{group}/posts/{post.id}"
        links = {
            LINK_SELF: Link(href=base, method="GET"),
            LINK_GROUP: Link(href=group, method="GET"),
            LINK_COMMENTS: Link(href=f"{base}/comments", method="GET"),
        }
        if post.deleted_date:
            return links
        if self.permissions.can_post(caller, access):
            links[LINK_ADD_COMMENT] = Link(href=f"{base}/comments", method="POST")
            if post.liked_by_me:
                links[LINK_UNLIKE] = Link(href=f"{base}/like", method="DELETE")
            else:
                links[LINK_LIKE] = Link(href=f"{base}/like", method="PUT")
        if post.author_id == caller.user_id:
            links[LINK_UPDATE] = Link(href=base, method="PUT")
            if post.media_type:
                links[LINK_REMOVE_MEDIA] = Link(href=f"{base}/media", method="DELETE")
            else:
                links[LINK_ADD_MEDIA] = Link(href=f"{base}/media", method="PUT")
        if self.permissions.can_delete_content(caller, access, post.author_id):
            links[LINK_DELETE] = Link(href=base, method="DELETE")
        return links

    @staticmethod
    def people_metadata(posts: List[PostModel]) -> FieldMetadata:
        """Every person tagged in these posts as {id, value: full name}, for resolving taggedUserIds."""
        people: Dict[str, str] = {}
        for post in posts:
            if post.deleted_date:
                continue
            for person in post.tagged_people:
                people.setdefault(person.user_id, person.name)
        return FieldMetadata(
            mandatory=False,
            maxItems=MAX_TAGGED_PEOPLE,
            values=[EmbeddedRef(id=user_id, value=name) for user_id, name in people.items()],
        )

    def build_metadata(self, posts: List[PostModel]) -> PostMetadata:
        return PostMetadata(
            taggedUserIds=self.people_metadata(posts),
            title=FieldMetadata(mandatory=True, maxLength=TITLE_MAX_LENGTH),
            body=FieldMetadata(mandatory=True, maxLength=BODY_MAX_LENGTH),
            media=FieldMetadata(
                mandatory=False,
                values=[EmbeddedRef(id=media.value, value=media.value.title()) for media in MediaType],
            ),
            authorName=FieldMetadata(readOnly=True),
        )

    def build_post_response(self, caller: Caller, access: GroupAccess, post: PostModel) -> PostResponse:
        return PostResponse.of(POST_DATA_NAME, self.to_dto(caller, access, post), self.build_metadata([post]))

    def build_posts_response(self, caller: Caller, access: GroupAccess, posts: List[PostModel]) -> PostListResponse:
        meta_links = {}
        if self.permissions.can_post(caller, access):
            meta_links[LINK_CREATE_POST] = Link(href=f"{API_PREFIX}/groups/{access.group.id}/posts", method="POST")
        return PostListResponse.of(
            POSTS_DATA_NAME,
            [self.to_dto(caller, access, post) for post in posts],
            self.build_metadata(posts),
            meta_links,
        )
