from typing import Any, Dict, List, Optional

from core.config.database import Database
from groups.group_repository import visible_group_clause

_POST_COLUMNS = (
    "p.id, p.group_id, p.title, p.body, p.author_id, p.created_date, "
    "g.name AS group_name, u.name AS author_name, "
    "COALESCE(s.like_count, 0) AS like_count, COALESCE(s.comment_count, 0) AS comment_count, "
    "COALESCE(s.score, 0) AS score"
)
_POST_FROM = (
    "FROM posts p JOIN groups g ON g.id = p.group_id "
    "LEFT JOIN users u ON u.id = p.author_id "
    "LEFT JOIN post_stats s ON s.post_id = p.id"
)


class SocialQueryRepository:
    """
    Read-only questions about posts, comments and groups for the AI assistant.

    Every query takes the caller (`user_id`, `is_admin`) and applies the same
    visibility predicate as the API (visible_group_clause), so the assistant
    can only ever count or list what the caller could open themselves.
    Deleted posts and comments are never included.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    def _post_filters(
        self,
        user_id: str,
        is_admin: bool,
        group_id: Optional[str],
        author_id: Optional[str],
        created_from: Optional[str],
        created_to: Optional[str],
    ):
        visible, params = visible_group_clause("g", user_id, is_admin)
        where = ["p.deleted_date IS NULL", visible]
        if group_id:
            where.append("p.group_id = ?")
            params.append(group_id)
        if author_id:
            where.append("p.author_id = ?")
            params.append(author_id)
        if created_from:
            where.append("p.created_date >= ?")
            params.append(created_from)
        if created_to:
            where.append("p.created_date < ?")
            params.append(created_to)
        return " AND ".join(where), params

    async def count_posts(self, user_id: str, is_admin: bool, **filters: Any) -> int:
        where, params = self._post_filters(user_id, is_admin, **filters)
        row = await self.db.fetch_one(
            f"SELECT COUNT(*) AS n FROM posts p JOIN groups g ON g.id = p.group_id WHERE {where}", tuple(params)
        )
        return int(row["n"]) if row else 0

    async def list_posts(
        self, user_id: str, is_admin: bool, order_by_score: bool, limit: int, **filters: Any
    ) -> List[Dict[str, Any]]:
        where, params = self._post_filters(user_id, is_admin, **filters)
        order = "score DESC, p.created_date DESC" if order_by_score else "p.created_date DESC"
        return await self.db.fetch_all(
            f"SELECT {_POST_COLUMNS} {_POST_FROM} WHERE {where} ORDER BY {order} LIMIT ?", (*params, limit)
        )

    async def posts_by_ids(self, user_id: str, is_admin: bool, post_ids: List[str]) -> List[Dict[str, Any]]:
        if not post_ids:
            return []
        visible, params = visible_group_clause("g", user_id, is_admin)
        placeholders = ", ".join("?" for _ in post_ids)
        return await self.db.fetch_all(
            f"SELECT {_POST_COLUMNS} {_POST_FROM} "
            f"WHERE p.deleted_date IS NULL AND {visible} AND p.id IN ({placeholders})",
            (*params, *post_ids),
        )

    async def count_comments(
        self,
        user_id: str,
        is_admin: bool,
        group_id: Optional[str] = None,
        author_id: Optional[str] = None,
        created_from: Optional[str] = None,
        created_to: Optional[str] = None,
    ) -> int:
        visible, params = visible_group_clause("g", user_id, is_admin)
        where = ["c.deleted_date IS NULL", "p.deleted_date IS NULL", visible]
        for column, value in (("p.group_id", group_id), ("c.author_id", author_id)):
            if value:
                where.append(f"{column} = ?")
                params.append(value)
        if created_from:
            where.append("c.created_date >= ?")
            params.append(created_from)
        if created_to:
            where.append("c.created_date < ?")
            params.append(created_to)
        row = await self.db.fetch_one(
            "SELECT COUNT(*) AS n FROM comments c JOIN posts p ON p.id = c.post_id "
            f"JOIN groups g ON g.id = p.group_id WHERE {' AND '.join(where)}",
            tuple(params),
        )
        return int(row["n"]) if row else 0

    async def comments_by_ids(self, user_id: str, is_admin: bool, comment_ids: List[str]) -> List[Dict[str, Any]]:
        """Live, visible comments with their post id (for turning comment search hits into posts)."""
        if not comment_ids:
            return []
        visible, params = visible_group_clause("g", user_id, is_admin)
        placeholders = ", ".join("?" for _ in comment_ids)
        return await self.db.fetch_all(
            "SELECT c.id, c.post_id, c.body FROM comments c JOIN posts p ON p.id = c.post_id "
            f"JOIN groups g ON g.id = p.group_id WHERE c.deleted_date IS NULL AND p.deleted_date IS NULL "
            f"AND {visible} AND c.id IN ({placeholders})",
            (*params, *comment_ids),
        )

    async def keyword_posts(self, user_id: str, is_admin: bool, term: str, group_id: Optional[str], limit: int):
        where, params = self._post_filters(user_id, is_admin, group_id, None, None, None)
        like = f"%{term}%"
        return await self.db.fetch_all(
            f"SELECT p.id {_POST_FROM} WHERE {where} AND (p.title LIKE ? OR p.body LIKE ?) "
            "ORDER BY p.created_date DESC LIMIT ?",
            (*params, like, like, limit),
        )

    async def keyword_comments(self, user_id: str, is_admin: bool, term: str, group_id: Optional[str], limit: int):
        where, params = self._post_filters(user_id, is_admin, group_id, None, None, None)
        return await self.db.fetch_all(
            "SELECT c.id, c.post_id, c.body FROM comments c JOIN posts p ON p.id = c.post_id "
            f"JOIN groups g ON g.id = p.group_id WHERE {where} AND c.deleted_date IS NULL AND c.body LIKE ? "
            "ORDER BY c.created_date DESC LIMIT ?",
            (*params, f"%{term}%", limit),
        )

    async def visible_group_ids(self, user_id: str, is_admin: bool) -> List[str]:
        visible, params = visible_group_clause("g", user_id, is_admin)
        rows = await self.db.fetch_all(f"SELECT g.id FROM groups g WHERE {visible}", tuple(params))
        return [row["id"] for row in rows]

    async def find_visible_group(self, user_id: str, is_admin: bool, name: str) -> Optional[Dict[str, Any]]:
        visible, params = visible_group_clause("g", user_id, is_admin)
        return await self.db.fetch_one(
            f"SELECT g.id, g.name FROM groups g WHERE g.name = ? COLLATE NOCASE AND {visible}", (name, *params)
        )

    async def my_groups(self, user_id: str, is_admin: bool) -> List[Dict[str, Any]]:
        """Groups the user owns, belongs to or follows (and can still see), with activity counts."""
        visible, params = visible_group_clause("g", user_id, is_admin)
        return await self.db.fetch_all(
            "SELECT g.id, g.name, g.visibility, "
            "(g.owner_id = ?) AS is_owner, "
            "EXISTS (SELECT 1 FROM group_members m WHERE m.group_id = g.id AND m.user_id = ?) AS is_member, "
            "EXISTS (SELECT 1 FROM group_followers f WHERE f.group_id = g.id AND f.user_id = ?) AS is_following, "
            "(SELECT COUNT(*) FROM group_members m WHERE m.group_id = g.id) AS member_count, "
            "(SELECT COUNT(*) FROM posts p WHERE p.group_id = g.id AND p.deleted_date IS NULL) AS post_count, "
            "(SELECT MAX(p.created_date) FROM posts p WHERE p.group_id = g.id AND p.deleted_date IS NULL) "
            "AS last_post_date "
            "FROM groups g WHERE (g.owner_id = ? "
            "OR EXISTS (SELECT 1 FROM group_members m WHERE m.group_id = g.id AND m.user_id = ?) "
            "OR EXISTS (SELECT 1 FROM group_followers f WHERE f.group_id = g.id AND f.user_id = ?)) "
            f"AND {visible} ORDER BY g.name COLLATE NOCASE",
            (*(user_id,) * 6, *params),
        )

    # --- for (re)indexing search

    async def live_posts(self) -> List[Dict[str, Any]]:
        return await self.db.fetch_all(
            "SELECT id, group_id, title, body FROM posts WHERE deleted_date IS NULL"
        )

    async def live_comments(self) -> List[Dict[str, Any]]:
        return await self.db.fetch_all(
            "SELECT c.id, c.body, p.group_id FROM comments c JOIN posts p ON p.id = c.post_id "
            "WHERE c.deleted_date IS NULL AND p.deleted_date IS NULL"
        )
