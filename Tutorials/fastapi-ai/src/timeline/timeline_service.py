from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List

from core.common.api_response import API_PREFIX, envelope
from core.security.authorization import Caller
from groups.group_permissions import GroupAccess
from core.common.base_dto import Link
from timeline.timeline_repository import TimelineRepository
from groups.posts.post_service import PostService

WINDOW = timedelta(days=365)
DEFAULT_LIMIT = 50
MAX_LIMIT = 100


class TimelineType(str, Enum):
    ALL = "ALL"
    FOLLOWING = "FOLLOWING"
    POPULAR = "POPULAR"


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
    ) -> List[Dict[str, Any]]:
        since = (self.now() - WINDOW).astimezone(timezone.utc).isoformat()
        rows = await self.timeline.list_posts(
            caller.user_id,
            caller.is_admin,
            since,
            following_only=timeline_type == TimelineType.FOLLOWING,
            order_by_score=timeline_type == TimelineType.POPULAR,
            limit=max(1, min(limit, MAX_LIMIT)),
        )
        return await self.post_service.load_details(caller, rows)

    async def build_response(
        self, caller: Caller, timeline_type: TimelineType, rows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        # Each post's links depend on the caller's place in its group, so work that
        # out once for all groups on the page rather than per post.
        members = await self.timeline.member_group_ids(caller.user_id)
        followed = await self.timeline.followed_group_ids(caller.user_id)

        posts = [
            self.post_service.to_post(caller, self._access(row, members, followed), row) for row in rows
        ]
        return envelope(
            data_name="posts",
            data=posts,
            metadata={
                "type": {"values": [{"id": t.value, "value": t.value.title()} for t in TimelineType]},
                "taggedUserIds": self.post_service.people_metadata(rows),
            },
            meta_links={**self.links(), "self": Link(href=self._href(timeline_type), method="GET")},
        )

    @staticmethod
    def _access(row: Dict[str, Any], members: set, followed: set) -> GroupAccess:
        group = {
            "id": row["group_id"],
            "name": row["group_name"],
            "visibility": row["group_visibility"],
            "owner_id": row["group_owner_id"],
            "created_date": row["group_created_date"],
        }
        return GroupAccess(group=group, is_member=row["group_id"] in members, is_following=row["group_id"] in followed)

    @staticmethod
    def _href(timeline_type: TimelineType) -> str:
        return f"{API_PREFIX}/timeline/posts?type={timeline_type.value}"

    @classmethod
    def links(cls) -> Dict[str, Link]:
        return {
            "timelineAll": Link(href=cls._href(TimelineType.ALL), method="GET"),
            "timelineFollowing": Link(href=cls._href(TimelineType.FOLLOWING), method="GET"),
            "timelinePopular": Link(href=cls._href(TimelineType.POPULAR), method="GET"),
        }

