from typing import Iterable, Set

from core.config.database import Database


class ReactionRepository:
    """Likes on posts and comments: one row per user per target."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def add(self, user_id: str, target_type: str, target_id: str, created_date: str) -> None:
        await self.db.execute(
            "INSERT OR IGNORE INTO reactions (user_id, target_type, target_id, created_date) VALUES (?, ?, ?, ?)",
            (user_id, target_type, target_id, created_date),
        )

    async def remove(self, user_id: str, target_type: str, target_id: str) -> None:
        await self.db.execute(
            "DELETE FROM reactions WHERE user_id = ? AND target_type = ? AND target_id = ?",
            (user_id, target_type, target_id),
        )

    async def liked_ids(self, user_id: str, target_type: str, target_ids: Iterable[str]) -> Set[str]:
        """Which of these targets the user has liked."""
        ids = list(target_ids)
        if not ids:
            return set()
        placeholders = ", ".join("?" for _ in ids)
        rows = await self.db.fetch_all(
            f"SELECT target_id FROM reactions WHERE user_id = ? AND target_type = ? AND target_id IN ({placeholders})",
            (user_id, target_type, *ids),
        )
        return {row["target_id"] for row in rows}
