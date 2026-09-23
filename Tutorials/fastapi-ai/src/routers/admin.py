from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Request

from api_response import API_PREFIX, envelope
from database import get_database
from errors import ForbiddenError
from group_permissions import Caller
from models import Link
from repositories.post_stats_repository import PostStatsRepository
from routers.deps import get_caller

# The admin area: system ADMINs only (the Clerk `roles` claim). The user
# profile links here (`admin`) only for admins, and GET /admin is the hub
# listing everything an admin can do. New admin tools (insights, ...) add a
# route here and a link in `admin_links`.
router = APIRouter(prefix="/admin", tags=["admin"])


def require_admin(caller: Caller = Depends(get_caller)) -> Caller:
    if not caller.is_admin:
        raise ForbiddenError("Admins only")
    return caller


def admin_links() -> dict[str, Link]:
    return {
        "self": Link(href=f"{API_PREFIX}/admin", method="GET"),
        "rebuildPostStats": Link(href=f"{API_PREFIX}/admin/post-stats/rebuild", method="POST"),
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
    ]
    return envelope(data_name="admin", data={"tools": tools}, metadata={}, meta_links=admin_links())


@router.post("/post-stats/rebuild")
async def rebuild_post_stats(request: Request, caller: Caller = Depends(require_admin)) -> dict[str, Any]:
    """Recompute every post's likes, comments and score from the source tables."""
    rebuilt = await PostStatsRepository(get_database(request)).rebuild_all(datetime.now(timezone.utc).isoformat())
    return envelope(data_name="postStats", data={"rebuilt": rebuilt}, metadata={}, meta_links=admin_links())
