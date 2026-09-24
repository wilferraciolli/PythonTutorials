from typing import Dict, Iterable, List, Set

from core.config.database import Database
from groups.posts.models import TaggedPersonModel


def _placeholders(values: List[str]) -> str:
    return ", ".join("?" for _ in values)


class PostPeopleTagRepository:
    """People tagged in posts. No permission logic here (see PostService)."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def replace(self, post_id: str, user_ids: List[str], created_date: str) -> None:
        """Set the post's tagged people to exactly `user_ids`."""
        await self.db.execute("DELETE FROM post_people_tags WHERE post_id = ?", (post_id,))
        for user_id in user_ids:
            await self.db.execute(
                "INSERT OR IGNORE INTO post_people_tags (post_id, user_id, created_date) VALUES (?, ?, ?)",
                (post_id, user_id, created_date),
            )

    async def for_posts(self, post_ids: Iterable[str]) -> Dict[str, List[TaggedPersonModel]]:
        """post id -> the people tagged in it, in tagging order. Users who no longer exist are left out."""
        ids = list(post_ids)
        if not ids:
            return {}
        rows = await self.db.fetch_all(
            "SELECT t.post_id, t.user_id, u.name FROM post_people_tags t "
            "JOIN users u ON u.id = t.user_id "
            f"WHERE t.post_id IN ({_placeholders(ids)}) ORDER BY t.created_date, t.rowid",
            tuple(ids),
        )
        tagged: Dict[str, List[TaggedPersonModel]] = {}
        for row in rows:
            tagged.setdefault(row["post_id"], []).append(TaggedPersonModel(user_id=row["user_id"], name=row["name"]))
        return tagged

    async def existing_user_ids(self, user_ids: List[str]) -> Set[str]:
        if not user_ids:
            return set()
        rows = await self.db.fetch_all(
            f"SELECT id FROM users WHERE id IN ({_placeholders(user_ids)})", tuple(user_ids)
        )
        return {row["id"] for row in rows}
