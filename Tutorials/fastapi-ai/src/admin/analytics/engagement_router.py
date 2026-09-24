from typing import Any

from fastapi import APIRouter, Depends, Request

from core.config.database import get_database
from core.security.authorization import Caller, require_admin
from admin.analytics.engagement_repository import EngagementRepository
from admin.analytics.engagement_service import DEFAULT_DAYS, EngagementAnalyticsService

# Engagement analytics API: social activity insights for the admin area.
# Admins only; the admin hub links here as `engagementAnalytics`.
router = APIRouter(prefix="/admin/analytics", tags=["admin"])


def get_engagement_service(request: Request) -> EngagementAnalyticsService:
    return EngagementAnalyticsService(EngagementRepository(get_database(request)))


@router.get("/engagement")
async def engagement(
    days: int = DEFAULT_DAYS,
    caller: Caller = Depends(require_admin),
    service: EngagementAnalyticsService = Depends(get_engagement_service),
) -> dict[str, Any]:
    """Groups, posts, comments and likes created per day over the last `days` (7-90, default 30)."""
    return service.build_response(await service.engagement(days))
