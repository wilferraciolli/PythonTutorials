from datetime import date, datetime, timedelta, timezone
from typing import Callable, Dict

from admin.analytics.constants import (
    DEFAULT_DAYS,
    ENGAGEMENT_DATA_NAME,
    LABELS,
    LINK_ADMIN,
    LINK_SELF,
    MAX_DAYS,
    MIN_DAYS,
)
from admin.analytics.engagement_repository import METRICS, EngagementRepository
from admin.analytics.schemas import (
    EngagementCountsDTO,
    EngagementDayDTO,
    EngagementDTO,
    EngagementMetadata,
    EngagementResponse,
)
from core.common.api_response import API_PREFIX
from core.common.base_dto import EmbeddedRef, FieldMetadata, Link


def utc_today() -> date:
    return datetime.now(timezone.utc).date()


class EngagementAnalyticsService:
    """
    Social engagement for the admin area: how many groups, posts, comments and
    likes were created over the last N days (today included, UTC), per day and
    in total, with the same totals for the N days before for comparison.
    """

    def __init__(self, repository: EngagementRepository, today: Callable[[], date] = utc_today) -> None:
        self.repository = repository
        self.today = today

    async def engagement(self, days: int = DEFAULT_DAYS) -> EngagementDTO:
        days = max(MIN_DAYS, min(days, MAX_DAYS))
        last = self.today()
        first = last - timedelta(days=days - 1)
        previous_first = first - timedelta(days=days)

        # One query per metric covers both windows.
        counts = await self.repository.daily_counts(previous_first.isoformat(), (last + timedelta(days=1)).isoformat())

        def on(day: date) -> Dict[str, int]:
            return {metric: counts[metric].get(day.isoformat(), 0) for metric in METRICS}

        def total(start: date) -> EngagementCountsDTO:
            window = [on(start + timedelta(days=offset)) for offset in range(days)]
            return EngagementCountsDTO(**{metric: sum(day[metric] for day in window) for metric in METRICS})

        return EngagementDTO(
            from_=first,
            to=last,
            days=days,
            totals=total(first),
            previousTotals=total(previous_first),
            daily=[
                EngagementDayDTO(date=first + timedelta(days=offset), **on(first + timedelta(days=offset)))
                for offset in range(days)
            ],
        )

    @staticmethod
    def build_response(engagement: EngagementDTO) -> EngagementResponse:
        href = f"{API_PREFIX}/admin/analytics/engagement"
        return EngagementResponse.of(
            ENGAGEMENT_DATA_NAME,
            engagement,
            EngagementMetadata(
                metric=FieldMetadata(values=[EmbeddedRef(id=metric, value=LABELS[metric]) for metric in METRICS]),
                days=FieldMetadata(min=MIN_DAYS, max=MAX_DAYS, default=DEFAULT_DAYS),
            ),
            {
                LINK_SELF: Link(href=f"{href}?days={engagement.days}", method="GET"),
                LINK_ADMIN: Link(href=f"{API_PREFIX}/admin", method="GET"),
            },
        )
