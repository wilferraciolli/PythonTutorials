from fastapi import APIRouter, Depends, Request

from core.config.database import get_database
from core.security.authorization import Caller, get_caller
from groups.posts.post_router import get_post_service
from timeline.constants import DEFAULT_LIMIT
from timeline.enums import TimelineType
from timeline.schemas import TimelineResponse
from timeline.timeline_repository import TimelineRepository
from timeline.timeline_service import TimelineService

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
) -> TimelineResponse:
    """Your feed from the last year: ALL (newest), FOLLOWING (groups you follow, newest) or POPULAR (by score)."""
    posts = await service.list_posts(caller, type, limit)
    return await service.build_response(caller, type, posts)
