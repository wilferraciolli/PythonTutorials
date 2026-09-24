from datetime import datetime, timezone
from typing import Callable, Dict, List

from core.common.api_response import API_PREFIX
from core.common.base_dto import EmbeddedRef, FieldMetadata, Link
from core.security.authorization import Caller
from groups.group_permissions import GroupAccess
from groups.models import GroupModel
from groups.posts.models import PostModel
from groups.posts.post_service import PostService
from timeline.constants import (
    DEFAULT_LIMIT,
    LINK_SELF,
    LINK_TIMELINE_ALL,
    LINK_TIMELINE_FOLLOWING,
    LINK_TIMELINE_POPULAR,
    MAX_LIMIT,
    POSTS_DATA_NAME,
    WINDOW,
)
from timeline.enums import TimelineType
from timeline.schemas import TimelineMetadata, TimelineResponse
from timeline.timeline_repository import TimelineRepository


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class TimelineService:
    """
    The signed-in user's feed (docs/social-groups.md), always posts from the
    last year that the caller is allowed to see:

    - ALL: every visible post, newest first
    - FOLLOWING: visible posts in groups the caller follows, newest first
    - POPULAR: every visible post, by post_stats.score (comment = 2, like = 1), then newest
    """

    def __init__(
        self,
        timeline: TimelineRepository,
        post_service: PostService,
        now: Callable[[], datetime] = utc_now,
    ) -> None:
        self.timeline = timeline
        self.post_service = post_service
        self.now = now

    async def list_posts(
        self, caller: Caller, timeline_type: TimelineType = TimelineType.ALL, limit: int = DEFAULT_LIMIT
    ) -> List[PostModel]:
        since = (self.now() - WINDOW).astimezone(timezone.utc).isoformat()
        posts = await self.timeline.list_posts(
            caller.user_id,
            caller.is_admin,
            since,
            following_only=timeline_type == TimelineType.FOLLOWING,
            order_by_score=timeline_type == TimelineType.POPULAR,
            limit=max(1, min(limit, MAX_LIMIT)),
        )
        return await self.post_service.load_details(caller, posts)

    async def build_response(
        self, caller: Caller, timeline_type: TimelineType, posts: List[PostModel]
    ) -> TimelineResponse:
        # Each post's links depend on the caller's place in its group, so work that
        # out once for all groups on the page rather than per post.
        members = await self.timeline.member_group_ids(caller.user_id)
        followed = await self.timeline.followed_group_ids(caller.user_id)

        return TimelineResponse.of(
            POSTS_DATA_NAME,
            [self.post_service.to_dto(caller, self._access(post, members, followed), post) for post in posts],
            TimelineMetadata(
                type=FieldMetadata(values=[EmbeddedRef(id=t.value, value=t.value.title()) for t in TimelineType]),
                taggedUserIds=self.post_service.people_metadata(posts),
            ),
            {**self.links(), LINK_SELF: Link(href=self._href(timeline_type), method="GET")},
        )

    @staticmethod
    def _access(post: PostModel, members: set, followed: set) -> GroupAccess:
        group = GroupModel(
            id=post.group_id,
            name=post.group_name,
            visibility=post.group_visibility,
            owner_id=post.group_owner_id,
            created_date=post.group_created_date,
        )
        return GroupAccess(group=group, is_member=post.group_id in members, is_following=post.group_id in followed)

    @staticmethod
    def _href(timeline_type: TimelineType) -> str:
        return f"{API_PREFIX}/timeline/posts?type={timeline_type.value}"

    @classmethod
    def links(cls) -> Dict[str, Link]:
        return {
            LINK_TIMELINE_ALL: Link(href=cls._href(TimelineType.ALL), method="GET"),
            LINK_TIMELINE_FOLLOWING: Link(href=cls._href(TimelineType.FOLLOWING), method="GET"),
            LINK_TIMELINE_POPULAR: Link(href=cls._href(TimelineType.POPULAR), method="GET"),
        }
