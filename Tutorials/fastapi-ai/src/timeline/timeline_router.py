from typing import Any

from fastapi import APIRouter, Depends, Request

from core.config.database import get_database
from groups.group_permissions import Caller
from timeline.timeline_repository import TimelineRepository
from users.dependencies import get_caller
from groups.posts.post_router import get_post_service
from timeline.timeline_service import DEFAULT_LIMIT, TimelineService, TimelineType

# Always the signed-in user's feed, so no user id in the path.
router = APIRouter(prefix="/timeline", tags=["timeline"])


def get_timeline_service(request: Request) -> TimelineService:
    return TimelineService(TimelineRepository(get_database(request)), get_post_service(request, media=None, search=None))


@router.get("/posts")
async def timeline_posts(
    type: TimelineType = TimelineType.ALL,
    limit: int = DEFAULT_LIMIT,
    caller: Caller = Depends(get_caller),
    service: TimelineService = Depends(get_timeline_service),
) -> dict[str, Any]:
    """Your feed from the last year: ALL (newest), FOLLOWING (groups you follow, newest) or POPULAR (by score)."""
    rows = await service.list_posts(caller, type, limit)
    return await service.build_response(caller, type, rows)
