from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request

from core.common.api_response import API_PREFIX, envelope
from core.config.database import get_database
from core.security.authorization import Caller, require_admin
from core.common.base_dto import Link
from groups.posts.post_stats_repository import PostStatsRepository
from groups.posts.post_router import get_post_search_service
from groups.posts.post_search_service import PostSearchService

# The admin area: system ADMINs only (the Clerk `roles` claim). The user
# profile links here (`admin`) only for admins, and GET /admin is the hub
# listing everything an admin can do. New admin tools (insights, ...) add a
# route here and a link in `admin_links`.
router = APIRouter(prefix="/admin", tags=["admin"])


def admin_links() -> dict[str, Link]:
    return {
        "self": Link(href=f"{API_PREFIX}/admin", method="GET"),
        "rebuildPostStats": Link(href=f"{API_PREFIX}/admin/post-stats/rebuild", method="POST"),
        "reindexPostSearch": Link(href=f"{API_PREFIX}/admin/post-search/reindex", method="POST"),
        # Insights, not a tool: routers/engagement_analytics.py.
        "engagementAnalytics": Link(href=f"{API_PREFIX}/admin/analytics/engagement", method="GET"),
    }


@router.get("")
async def admin_area(caller: Caller = Depends(require_admin)) -> dict[str, Any]:
    """The admin hub: what an admin can do, as links."""
    tools = [
        {
            "id": "rebuildPostStats",
            "name": "Recalculate post stats",
            "description": "Recount every post's likes and comments and recompute its popularity score.",
        },
        {
            "id": "reindexPostSearch",
            "name": "Index posts for AI search",
            "description": (
                "Embed every post and comment that isn't searchable yet (e.g. the seeded News posts, "
                "or anything written while Workers AI was unavailable)."
            ),
        },
    ]
    return envelope(data_name="admin", data={"tools": tools}, metadata={}, meta_links=admin_links())


@router.post("/post-stats/rebuild")
async def rebuild_post_stats(request: Request, caller: Caller = Depends(require_admin)) -> dict[str, Any]:
    """Recompute every post's likes, comments and score from the source tables."""
    rebuilt = await PostStatsRepository(get_database(request)).rebuild_all(datetime.now(timezone.utc).isoformat())
    return envelope(data_name="postStats", data={"rebuilt": rebuilt}, metadata={}, meta_links=admin_links())


@router.post("/post-search/reindex")
async def reindex_post_search(
    caller: Caller = Depends(require_admin),
    search: PostSearchService = Depends(get_post_search_service),
) -> dict[str, Any]:
    """Backfill search vectors for posts and comments that have none."""
    indexed = await search.reindex_missing()
    # Named after the tool id: the admin page reads a tool's result under its id.
    return envelope(data_name="reindexPostSearch", data={"indexed": indexed}, metadata={}, meta_links=admin_links())
