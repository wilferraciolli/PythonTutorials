from typing import Any, List, Optional

from core.config.database import Database
from groups.group_repository import visible_group_clause
from groups.models import GroupRefModel, MyGroupModel, SocialCommentModel, SocialPostModel

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
_COMMENT_FROM = "FROM comments c JOIN posts p ON p.id = c.post_id JOIN groups g ON g.id = p.group_id"
_COMMENT_COLUMNS = "c.id, c.post_id, p.group_id, c.body"


def _placeholders(values: List[str]) -> str:
    return ", ".join("?" for _ in values)


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

    @staticmethod
    def _post_filters(
        user_id: str,
        is_admin: bool,
        group_id: Optional[str],
        author_id: Optional[str],
        created_from: Optional[str],
        created_to: Optional[str],
    ) -> tuple[str, List[Any]]:
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

    async def count_posts(
        self,
        user_id: str,
        is_admin: bool,
        group_id: Optional[str] = None,
        author_id: Optional[str] = None,
        created_from: Optional[str] = None,
        created_to: Optional[str] = None,
    ) -> int:
        where, params = self._post_filters(user_id, is_admin, group_id, author_id, created_from, created_to)
        row = await self.db.fetch_one(
            f"SELECT COUNT(*) AS n FROM posts p JOIN groups g ON g.id = p.group_id WHERE {where}", tuple(params)
        )
        return int(row["n"]) if row else 0

    async def list_posts(
        self,
        user_id: str,
        is_admin: bool,
        order_by_score: bool,
        limit: int,
        group_id: Optional[str] = None,
        author_id: Optional[str] = None,
        created_from: Optional[str] = None,
        created_to: Optional[str] = None,
    ) -> List[SocialPostModel]:
        where, params = self._post_filters(user_id, is_admin, group_id, author_id, created_from, created_to)
        order = "score DESC, p.created_date DESC" if order_by_score else "p.created_date DESC"
        rows = await self.db.fetch_all(
            f"SELECT {_POST_COLUMNS} {_POST_FROM} WHERE {where} ORDER BY {order} LIMIT ?", (*params, limit)
        )
        return [SocialPostModel(**row) for row in rows]

    async def posts_by_ids(self, user_id: str, is_admin: bool, post_ids: List[str]) -> List[SocialPostModel]:
        if not post_ids:
            return []
        visible, params = visible_group_clause("g", user_id, is_admin)
        rows = await self.db.fetch_all(
            f"SELECT {_POST_COLUMNS} {_POST_FROM} "
            f"WHERE p.deleted_date IS NULL AND {visible} AND p.id IN ({_placeholders(post_ids)})",
            (*params, *post_ids),
        )
        return [SocialPostModel(**row) for row in rows]

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
            f"SELECT COUNT(*) AS n {_COMMENT_FROM} WHERE {' AND '.join(where)}", tuple(params)
        )
        return int(row["n"]) if row else 0

    async def comments_by_ids(
        self, user_id: str, is_admin: bool, comment_ids: List[str]
    ) -> List[SocialCommentModel]:
        """Live, visible comments with their post id (for turning comment search hits into posts)."""
        if not comment_ids:
            return []
        visible, params = visible_group_clause("g", user_id, is_admin)
        rows = await self.db.fetch_all(
            f"SELECT {_COMMENT_COLUMNS} {_COMMENT_FROM} WHERE c.deleted_date IS NULL AND p.deleted_date IS NULL "
            f"AND {visible} AND c.id IN ({_placeholders(comment_ids)})",
            (*params, *comment_ids),
        )
        return [SocialCommentModel(**row) for row in rows]

    async def keyword_post_ids(
        self, user_id: str, is_admin: bool, term: str, group_id: Optional[str], limit: int
    ) -> List[str]:
        """Ids of visible posts whose title or body contains `term`, newest first."""
        where, params = self._post_filters(user_id, is_admin, group_id, None, None, None)
        like = f"%{term}%"
        rows = await self.db.fetch_all(
            f"SELECT p.id {_POST_FROM} WHERE {where} AND (p.title LIKE ? OR p.body LIKE ?) "
            "ORDER BY p.created_date DESC LIMIT ?",
            (*params, like, like, limit),
        )
        return [row["id"] for row in rows]

    async def keyword_comments(
        self, user_id: str, is_admin: bool, term: str, group_id: Optional[str], limit: int
    ) -> List[SocialCommentModel]:
        where, params = self._post_filters(user_id, is_admin, group_id, None, None, None)
        rows = await self.db.fetch_all(
            f"SELECT {_COMMENT_COLUMNS} {_COMMENT_FROM} WHERE {where} AND c.deleted_date IS NULL "
            "AND c.body LIKE ? ORDER BY c.created_date DESC LIMIT ?",
            (*params, f"%{term}%", limit),
        )
        return [SocialCommentModel(**row) for row in rows]

    async def visible_group_ids(self, user_id: str, is_admin: bool) -> List[str]:
        visible, params = visible_group_clause("g", user_id, is_admin)
        rows = await self.db.fetch_all(f"SELECT g.id FROM groups g WHERE {visible}", tuple(params))
        return [row["id"] for row in rows]

    async def find_visible_group(self, user_id: str, is_admin: bool, name: str) -> Optional[GroupRefModel]:
        visible, params = visible_group_clause("g", user_id, is_admin)
        row = await self.db.fetch_one(
            f"SELECT g.id, g.name FROM groups g WHERE g.name = ? COLLATE NOCASE AND {visible}", (name, *params)
        )
        return GroupRefModel(**row) if row else None

    async def my_groups(self, user_id: str, is_admin: bool) -> List[MyGroupModel]:
        """Groups the user owns, belongs to or follows (and can still see), with activity counts."""
        visible, params = visible_group_clause("g", user_id, is_admin)
        rows = await self.db.fetch_all(
            "SELECT g.id, g.name, g.visibility, "
            "COALESCE(g.owner_id = ?, 0) AS is_owner, "
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
        return [MyGroupModel(**row) for row in rows]

    # --- for (re)indexing search

    async def live_posts(self) -> List[SocialPostModel]:
        rows = await self.db.fetch_all(f"SELECT {_POST_COLUMNS} {_POST_FROM} WHERE p.deleted_date IS NULL")
        return [SocialPostModel(**row) for row in rows]

    async def live_comments(self) -> List[SocialCommentModel]:
        rows = await self.db.fetch_all(
            f"SELECT {_COMMENT_COLUMNS} {_COMMENT_FROM} WHERE c.deleted_date IS NULL AND p.deleted_date IS NULL"
        )
        return [SocialCommentModel(**row) for row in rows]
