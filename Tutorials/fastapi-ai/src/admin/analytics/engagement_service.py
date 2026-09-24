from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, List

from core.common.api_response import API_PREFIX, envelope
from core.common.base_dto import Link
from admin.analytics.engagement_repository import METRICS, EngagementRepository

DEFAULT_DAYS = 30
MIN_DAYS = 7
MAX_DAYS = 90

LABELS = {"groups": "Groups created", "posts": "Posts", "comments": "Comments", "likes": "Likes"}


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

    async def engagement(self, days: int = DEFAULT_DAYS) -> Dict[str, Any]:
        days = max(MIN_DAYS, min(days, MAX_DAYS))
        last = self.today()
        first = last - timedelta(days=days - 1)
        previous_first = first - timedelta(days=days)

        # One query per metric covers both windows.
        counts = await self.repository.daily_counts(previous_first.isoformat(), (last + timedelta(days=1)).isoformat())

        window = [first + timedelta(days=offset) for offset in range(days)]
        previous = [previous_first + timedelta(days=offset) for offset in range(days)]
        daily: List[Dict[str, Any]] = [
            {"date": day.isoformat(), **{metric: counts[metric].get(day.isoformat(), 0) for metric in METRICS}}
            for day in window
        ]
        return {
            "from": first.isoformat(),
            "to": last.isoformat(),
            "days": days,
            "totals": {metric: sum(entry[metric] for entry in daily) for metric in METRICS},
            "previousTotals": {
                metric: sum(counts[metric].get(day.isoformat(), 0) for day in previous) for metric in METRICS
            },
            "daily": daily,
        }

    @staticmethod
    def build_response(engagement: Dict[str, Any]) -> Dict[str, Any]:
        href = f"{API_PREFIX}/admin/analytics/engagement"
        return envelope(
            data_name="engagement",
            data=engagement,
            metadata={
                "metric": {"values": [{"id": metric, "value": LABELS[metric]} for metric in METRICS]},
                "days": {"min": MIN_DAYS, "max": MAX_DAYS, "default": DEFAULT_DAYS},
            },
            meta_links={
                "self": Link(href=f"{href}?days={engagement['days']}", method="GET"),
                "admin": Link(href=f"{API_PREFIX}/admin", method="GET"),
            },
        )
