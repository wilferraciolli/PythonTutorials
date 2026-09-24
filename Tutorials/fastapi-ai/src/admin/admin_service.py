from datetime import datetime, timezone
from typing import Dict, Optional

from admin.constants import (
    ADMIN_DATA_NAME,
    LINK_ENGAGEMENT_ANALYTICS,
    LINK_REBUILD_POST_STATS,
    LINK_REINDEX_POST_SEARCH,
    LINK_SELF,
    POST_STATS_DATA_NAME,
    REINDEX_POST_SEARCH_DATA_NAME,
)
from admin.schemas import (
    AdminDTO,
    AdminResponse,
    AdminToolDTO,
    PostSearchReindexDTO,
    PostSearchReindexResponse,
    PostStatsRebuildDTO,
    PostStatsRebuildResponse,
)
from core.common.api_response import API_PREFIX
from core.common.base_dto import Link, NoMetadata
from groups.posts.post_search_service import PostSearchService
from groups.posts.post_stats_repository import PostStatsRepository

TOOLS = [
    AdminToolDTO(
        id=LINK_REBUILD_POST_STATS,
        name="Recalculate post stats",
        description="Recount every post's likes and comments and recompute its popularity score.",
    ),
    AdminToolDTO(
        id=LINK_REINDEX_POST_SEARCH,
        name="Index posts for AI search",
        description=(
            "Embed every post and comment that isn't searchable yet (e.g. the seeded News posts, "
            "or anything written while Workers AI was unavailable)."
        ),
    ),
]


class AdminService:
    """
    The admin area: system ADMINs only (the router requires it). The user
    profile links here (`admin`) only for admins, and the hub lists every
    tool as a meta link. New admin tools add a method here, a route, and a
    link in `build_meta_links`.
    """

    def __init__(self, post_stats: PostStatsRepository, post_search: Optional[PostSearchService]) -> None:
        self.post_stats = post_stats
        self.post_search = post_search

    @staticmethod
    def get_admin() -> AdminDTO:
        return AdminDTO(tools=TOOLS)

    async def rebuild_post_stats(self) -> PostStatsRebuildDTO:
        """Recompute every post's likes, comments and score from the source tables."""
        return PostStatsRebuildDTO(rebuilt=await self.post_stats.rebuild_all(datetime.now(timezone.utc).isoformat()))

    async def reindex_post_search(self) -> PostSearchReindexDTO:
        """Backfill search vectors for posts and comments that have none."""
        if self.post_search is None:
            raise RuntimeError("post search is not available")
        return PostSearchReindexDTO(indexed=await self.post_search.reindex_missing())

    # --- responses

    @staticmethod
    def build_meta_links() -> Dict[str, Link]:
        base = f"{API_PREFIX}/admin"
        return {
            LINK_SELF: Link(href=base, method="GET"),
            LINK_REBUILD_POST_STATS: Link(href=f"{base}/post-stats/rebuild", method="POST"),
            LINK_REINDEX_POST_SEARCH: Link(href=f"{base}/post-search/reindex", method="POST"),
            # Insights, not a tool: admin/analytics.
            LINK_ENGAGEMENT_ANALYTICS: Link(href=f"{base}/analytics/engagement", method="GET"),
        }

    def build_admin_response(self, admin: AdminDTO) -> AdminResponse:
        return AdminResponse.of(ADMIN_DATA_NAME, admin, NoMetadata(), self.build_meta_links())

    def build_post_stats_response(self, result: PostStatsRebuildDTO) -> PostStatsRebuildResponse:
        return PostStatsRebuildResponse.of(POST_STATS_DATA_NAME, result, NoMetadata(), self.build_meta_links())

    def build_reindex_response(self, result: PostSearchReindexDTO) -> PostSearchReindexResponse:
        return PostSearchReindexResponse.of(
            REINDEX_POST_SEARCH_DATA_NAME, result, NoMetadata(), self.build_meta_links()
        )
