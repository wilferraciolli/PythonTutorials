from fastapi import APIRouter, Depends, Request

from admin.analytics.constants import DEFAULT_DAYS
from admin.analytics.engagement_repository import EngagementRepository
from admin.analytics.engagement_service import EngagementAnalyticsService
from admin.analytics.schemas import EngagementResponse
from core.config.database import get_database
from core.security.authorization import require_admin

# Engagement analytics API: social activity insights for the admin area.
# Admins only; the admin hub links here as `engagementAnalytics`.
router = APIRouter(prefix="/admin/analytics", tags=["admin"], dependencies=[Depends(require_admin)])


def get_engagement_service(request: Request) -> EngagementAnalyticsService:
    return EngagementAnalyticsService(EngagementRepository(get_database(request)))


@router.get("/engagement")
async def engagement(
    days: int = DEFAULT_DAYS,
    service: EngagementAnalyticsService = Depends(get_engagement_service),
) -> EngagementResponse:
    """Groups, posts, comments and likes created per day over the last `days` (7-90, default 30)."""
    return service.build_response(await service.engagement(days))
