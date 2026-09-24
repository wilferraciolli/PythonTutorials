from typing import Dict

from core.config.database import Database

# What "engagement" counts, and where each lives. Deleted posts and comments
# still count (the activity happened); a removed like doesn't (its row is gone).
# Likes are on posts and comments alike.
_SOURCES = {
    "groups": "SELECT substr(created_date, 1, 10) AS day, COUNT(*) AS n FROM groups",
    "posts": "SELECT substr(created_date, 1, 10) AS day, COUNT(*) AS n FROM posts",
    "comments": "SELECT substr(created_date, 1, 10) AS day, COUNT(*) AS n FROM comments",
    "likes": "SELECT substr(created_date, 1, 10) AS day, COUNT(*) AS n FROM reactions",
}

METRICS = tuple(_SOURCES)


class EngagementRepository:
    """Social activity counted per UTC day. No permission logic here (admins only, see the router)."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def daily_counts(self, first_day: str, day_after_last: str) -> Dict[str, Dict[str, int]]:
        """metric -> {"YYYY-MM-DD": count} for days in [first_day, day_after_last); days with none are absent.

        Dates are stored as ISO-8601 UTC strings, so the day is their first ten
        characters and comparing against a bare date string is a range test.
        """
        counts: Dict[str, Dict[str, int]] = {}
        for metric, select in _SOURCES.items():
            rows = await self.db.fetch_all(
                f"{select} WHERE created_date >= ? AND created_date < ? GROUP BY day",
                (first_day, day_after_last),
            )
            counts[metric] = {row["day"]: row["n"] for row in rows}
        return counts
