from typing import Any, Dict, List, Optional

from core.config.database import Database
from media.media_providers import ResolvedMedia

# author_name is NULL both for System (author_id NULL) and a deleted user
# (author_id set, no users row); the service tells them apart.
# Counts come from post_stats (kept up to date by the services).
_SELECT_POST = (
    "SELECT p.*, u.name AS author_name, g.name AS group_name, "
    "COALESCE(s.like_count, 0) AS like_count, "
    "COALESCE(s.comment_count, 0) AS comment_count, "
    "COALESCE(s.score, 0) AS score "
    "FROM posts p "
    "LEFT JOIN users u ON u.id = p.author_id "
    "LEFT JOIN post_stats s ON s.post_id = p.id "
    "JOIN groups g ON g.id = p.group_id"
)


class PostRepository:
    """Posts in groups. No permission logic here (see group_permissions.py)."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def create(
        self, post_id: str, group_id: str, author_id: Optional[str], title: str, body: str, created_date: str
    ) -> None:
        await self.db.execute(
            "INSERT INTO posts (id, group_id, author_id, title, body, created_date, updated_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (post_id, group_id, author_id, title, body, created_date, created_date),
        )

    async def get(self, group_id: str, post_id: str) -> Optional[Dict[str, Any]]:
        # Always looked up within its group, so a post can't be reached around the group's visibility.
        return await self.db.fetch_one(f"{_SELECT_POST} WHERE p.group_id = ? AND p.id = ?", (group_id, post_id))

    async def list_for_group(self, group_id: str, limit: int) -> List[Dict[str, Any]]:
        return await self.db.fetch_all(
            f"{_SELECT_POST} WHERE p.group_id = ? AND p.deleted_date IS NULL ORDER BY p.created_date DESC LIMIT ?",
            (group_id, limit),
        )

    async def update(self, post_id: str, updated_date: str, **fields: Any) -> None:
        updatable = {key: value for key, value in fields.items() if value is not None}
        if not updatable:
            return
        set_clause = ", ".join(f"{key} = ?" for key in updatable)
        await self.db.execute(
            f"UPDATE posts SET {set_clause}, updated_date = ? WHERE id = ?",
            (*updatable.values(), updated_date, post_id),
        )

    async def set_media(self, post_id: str, media: Optional[ResolvedMedia], updated_date: str) -> None:
        """Attach media, or clear it with None."""
        values = (
            (media.type.value, media.id, media.url, media.title, media.author_name, media.author_url)
            if media
            else (None,) * 6
        )
        await self.db.execute(
            "UPDATE posts SET media_type = ?, media_id = ?, media_url = ?, media_title = ?, "
            "media_author_name = ?, media_author_url = ?, updated_date = ? WHERE id = ?",
            (*values, updated_date, post_id),
        )

    async def soft_delete(self, post_id: str, deleted_date: str) -> None:
        await self.db.execute("UPDATE posts SET deleted_date = ? WHERE id = ?", (deleted_date, post_id))
