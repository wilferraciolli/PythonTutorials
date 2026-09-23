from database import Database

COMMENT_WEIGHT = 2
LIKE_WEIGHT = 1

# Recomputed from the source tables rather than incremented, so a stats row can
# never drift from the likes and comments it summarises.
_UPSERT = f"""
INSERT OR REPLACE INTO post_stats (post_id, like_count, comment_count, score, updated_date)
SELECT
    p.id,
    (SELECT COUNT(*) FROM reactions r WHERE r.target_type = 'post' AND r.target_id = p.id),
    (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.deleted_date IS NULL),
    (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.deleted_date IS NULL) * {COMMENT_WEIGHT}
      + (SELECT COUNT(*) FROM reactions r WHERE r.target_type = 'post' AND r.target_id = p.id) * {LIKE_WEIGHT},
    ?
FROM posts p
"""


class PostStatsRepository:
    """Each post's like count, comment count and popularity score (post_stats)."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def refresh(self, post_id: str, updated_date: str) -> None:
        """Recompute one post's row; called in the same request as the change behind it."""
        await self.db.execute(f"{_UPSERT} WHERE p.id = ?", (updated_date, post_id))

    async def rebuild_all(self, updated_date: str) -> int:
        """Recompute every row (admin repair job). Returns how many posts were processed."""
        await self.db.execute("DELETE FROM post_stats")
        await self.db.execute(_UPSERT, (updated_date,))
        row = await self.db.fetch_one("SELECT COUNT(*) AS n FROM post_stats")
        return int(row["n"]) if row else 0
