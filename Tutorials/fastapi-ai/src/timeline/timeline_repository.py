from typing import Any, List, Set

from core.config.database import Database
from groups.group_repository import visible_group_clause
from groups.posts.models import PostModel
from groups.posts.post_repository import SELECT_POST, to_post_model


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
    ) -> List[PostModel]:
        visible, visible_params = visible_group_clause("g", user_id, is_admin)
        where = ["p.deleted_date IS NULL", "p.created_date >= ?", visible]
        params: List[Any] = [since, *visible_params]

        if following_only:
            where.append("EXISTS (SELECT 1 FROM group_followers f WHERE f.group_id = g.id AND f.user_id = ?)")
            params.append(user_id)

        order = "score DESC, p.created_date DESC" if order_by_score else "p.created_date DESC"
        params.append(limit)
        rows = await self.db.fetch_all(
            f"{SELECT_POST} WHERE {' AND '.join(where)} ORDER BY {order} LIMIT ?", tuple(params)
        )
        return [to_post_model(row) for row in rows]

    async def member_group_ids(self, user_id: str) -> Set[str]:
        rows = await self.db.fetch_all("SELECT group_id FROM group_members WHERE user_id = ?", (user_id,))
        return {row["group_id"] for row in rows}

    async def followed_group_ids(self, user_id: str) -> Set[str]:
        rows = await self.db.fetch_all("SELECT group_id FROM group_followers WHERE user_id = ?", (user_id,))
        return {row["group_id"] for row in rows}
