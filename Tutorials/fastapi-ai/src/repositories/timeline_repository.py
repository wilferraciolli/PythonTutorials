from typing import Any, Dict, List, Set

from database import Database

_SELECT = (
    "SELECT p.*, u.name AS author_name, g.name AS group_name, "
    "g.visibility AS group_visibility, g.owner_id AS group_owner_id, g.created_date AS group_created_date, "
    "COALESCE(s.like_count, 0) AS like_count, "
    "COALESCE(s.comment_count, 0) AS comment_count, "
    "COALESCE(s.score, 0) AS score "
    "FROM posts p "
    "JOIN groups g ON g.id = p.group_id "
    "LEFT JOIN users u ON u.id = p.author_id "
    "LEFT JOIN post_stats s ON s.post_id = p.id"
)


class TimelineRepository:
    """
    Posts across every group the caller can see. Visibility here is the SQL
    twin of GroupPermissions.can_view: admin, or public, or owner, or member.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def list_posts(
        self,
        user_id: str,
        is_admin: bool,
        since: str,
        following_only: bool,
        order_by_score: bool,
        limit: int,
    ) -> List[Dict[str, Any]]:
        where = ["p.deleted_date IS NULL", "p.created_date >= ?"]
        params: List[Any] = [since]

        if not is_admin:
            where.append(
                "(g.visibility = 'PUBLIC' OR g.owner_id = ? "
                "OR EXISTS (SELECT 1 FROM group_members m WHERE m.group_id = g.id AND m.user_id = ?))"
            )
            params += [user_id, user_id]
        if following_only:
            where.append("EXISTS (SELECT 1 FROM group_followers f WHERE f.group_id = g.id AND f.user_id = ?)")
            params.append(user_id)

        order = "score DESC, p.created_date DESC" if order_by_score else "p.created_date DESC"
        params.append(limit)
        return await self.db.fetch_all(
            f"{_SELECT} WHERE {' AND '.join(where)} ORDER BY {order} LIMIT ?", tuple(params)
        )

    async def member_group_ids(self, user_id: str) -> Set[str]:
        rows = await self.db.fetch_all("SELECT group_id FROM group_members WHERE user_id = ?", (user_id,))
        return {row["group_id"] for row in rows}

    async def followed_group_ids(self, user_id: str) -> Set[str]:
        rows = await self.db.fetch_all("SELECT group_id FROM group_followers WHERE user_id = ?", (user_id,))
        return {row["group_id"] for row in rows}
