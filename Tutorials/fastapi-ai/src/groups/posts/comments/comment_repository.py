from typing import Any, Dict, List, Optional

from core.config.database import Database

_SELECT_COMMENT = (
    "SELECT c.*, u.name AS author_name, "
    "(SELECT COUNT(*) FROM reactions r WHERE r.target_type = 'comment' AND r.target_id = c.id) AS like_count "
    "FROM comments c LEFT JOIN users u ON u.id = c.author_id"
)


class PostCommentRepository:
    """Comments and replies on posts. No permission logic here (see group_permissions.py)."""

    def __init__(self, db: Database) -> None:
        self.db = db

    async def create(
        self,
        comment_id: str,
        post_id: str,
        parent_comment_id: Optional[str],
        author_id: Optional[str],
        body: str,
        created_date: str,
    ) -> None:
        await self.db.execute(
            "INSERT INTO comments (id, post_id, parent_comment_id, author_id, body, created_date, updated_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (comment_id, post_id, parent_comment_id, author_id, body, created_date, created_date),
        )

    async def get(self, post_id: str, comment_id: str) -> Optional[Dict[str, Any]]:
        # Always looked up within its post (and the post within its group).
        return await self.db.fetch_one(f"{_SELECT_COMMENT} WHERE c.post_id = ? AND c.id = ?", (post_id, comment_id))

    async def list_for_post(self, post_id: str) -> List[Dict[str, Any]]:
        # Deleted ones are kept (shown as "[deleted]") so their replies keep a parent.
        return await self.db.fetch_all(f"{_SELECT_COMMENT} WHERE c.post_id = ? ORDER BY c.created_date ASC", (post_id,))

    async def update(self, comment_id: str, body: str, updated_date: str) -> None:
        await self.db.execute(
            "UPDATE comments SET body = ?, updated_date = ? WHERE id = ?", (body, updated_date, comment_id)
        )

    async def soft_delete(self, comment_id: str, deleted_date: str) -> None:
        await self.db.execute("UPDATE comments SET deleted_date = ? WHERE id = ?", (deleted_date, comment_id))
