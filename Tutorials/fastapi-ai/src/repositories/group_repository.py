from typing import Any, Dict, List, Optional

from database import Database

_SELECT_GROUP = (
    "SELECT g.*, "
    "(SELECT COUNT(*) FROM group_members m WHERE m.group_id = g.id) AS member_count, "
    "(SELECT COUNT(*) FROM group_followers f WHERE f.group_id = g.id) AS follower_count "
    "FROM groups g"
)


class GroupRepository:
    """Groups, their members and their followers. No permission logic here (see group_permissions.py)."""

    def __init__(self, db: Database) -> None:
        self.db = db

    # --- groups

    async def create(
        self,
        group_id: str,
        name: str,
        description: Optional[str],
        visibility: str,
        owner_id: Optional[str],
        created_date: str,
    ) -> Dict[str, Any]:
        await self.db.execute(
            "INSERT INTO groups (id, name, description, visibility, owner_id, created_by, created_date) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (group_id, name, description, visibility, owner_id, owner_id, created_date),
        )
        created = await self.get(group_id)
        if created is None:
            raise RuntimeError(f"created group was not found: {group_id}")
        return created

    async def get(self, group_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.fetch_one(f"{_SELECT_GROUP} WHERE g.id = ?", (group_id,))

    async def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        return await self.db.fetch_one("SELECT * FROM groups WHERE name = ? COLLATE NOCASE", (name,))

    async def list_visible(
        self,
        user_id: str,
        is_admin: bool,
        term: Optional[str] = None,
        following_only: bool = False,
        member_only: bool = False,
    ) -> List[Dict[str, Any]]:
        where: List[str] = []
        params: List[Any] = []

        if not is_admin:
            where.append(
                "(g.visibility = 'PUBLIC' OR g.owner_id = ? "
                "OR EXISTS (SELECT 1 FROM group_members m WHERE m.group_id = g.id AND m.user_id = ?))"
            )
            params += [user_id, user_id]
        if term:
            where.append("(g.name LIKE ? OR g.description LIKE ?)")
            params += [f"%{term}%", f"%{term}%"]
        if following_only:
            where.append("EXISTS (SELECT 1 FROM group_followers f WHERE f.group_id = g.id AND f.user_id = ?)")
            params.append(user_id)
        if member_only:
            where.append("EXISTS (SELECT 1 FROM group_members m WHERE m.group_id = g.id AND m.user_id = ?)")
            params.append(user_id)

        clause = f" WHERE {' AND '.join(where)}" if where else ""
        return await self.db.fetch_all(f"{_SELECT_GROUP}{clause} ORDER BY g.name COLLATE NOCASE", tuple(params))

    async def update(self, group_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
        updatable = {key: value for key, value in fields.items() if value is not None}
        if updatable:
            set_clause = ", ".join(f"{key} = ?" for key in updatable)
            await self.db.execute(
                f"UPDATE groups SET {set_clause} WHERE id = ?", (*updatable.values(), group_id)
            )
        return await self.get(group_id)

    async def set_owner(self, group_id: str, owner_id: Optional[str]) -> None:
        await self.db.execute("UPDATE groups SET owner_id = ? WHERE id = ?", (owner_id, group_id))

    async def delete(self, group_id: str) -> None:
        # Posts, comments, reactions and stats join this list in step 2.
        await self.db.execute("DELETE FROM group_followers WHERE group_id = ?", (group_id,))
        await self.db.execute("DELETE FROM group_members WHERE group_id = ?", (group_id,))
        await self.db.execute("DELETE FROM groups WHERE id = ?", (group_id,))

    # --- members

    async def is_member(self, group_id: str, user_id: str) -> bool:
        row = await self.db.fetch_one(
            "SELECT 1 AS found FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id)
        )
        return row is not None

    async def add_member(self, group_id: str, user_id: str, joined_date: str) -> None:
        await self.db.execute(
            "INSERT OR IGNORE INTO group_members (group_id, user_id, joined_date) VALUES (?, ?, ?)",
            (group_id, user_id, joined_date),
        )

    async def remove_member(self, group_id: str, user_id: str) -> None:
        await self.db.execute("DELETE FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))

    async def list_members(self, group_id: str) -> List[Dict[str, Any]]:
        return await self.db.fetch_all(
            "SELECT m.user_id, m.joined_date, u.name FROM group_members m "
            "LEFT JOIN users u ON u.id = m.user_id WHERE m.group_id = ? ORDER BY m.joined_date ASC",
            (group_id,),
        )

    # --- followers

    async def is_following(self, group_id: str, user_id: str) -> bool:
        row = await self.db.fetch_one(
            "SELECT 1 AS found FROM group_followers WHERE group_id = ? AND user_id = ?", (group_id, user_id)
        )
        return row is not None

    async def add_follower(self, group_id: str, user_id: str, created_date: str) -> None:
        await self.db.execute(
            "INSERT OR IGNORE INTO group_followers (group_id, user_id, created_date) VALUES (?, ?, ?)",
            (group_id, user_id, created_date),
        )

    async def remove_follower(self, group_id: str, user_id: str) -> None:
        await self.db.execute(
            "DELETE FROM group_followers WHERE group_id = ? AND user_id = ?", (group_id, user_id)
        )

    async def remove_non_member_followers(self, group_id: str) -> None:
        await self.db.execute(
            "DELETE FROM group_followers WHERE group_id = ? AND user_id NOT IN "
            "(SELECT user_id FROM group_members WHERE group_id = ?)",
            (group_id, group_id),
        )

    async def list_followers(self, group_id: str) -> List[Dict[str, Any]]:
        return await self.db.fetch_all(
            "SELECT f.user_id, f.created_date, u.name FROM group_followers f "
            "LEFT JOIN users u ON u.id = f.user_id WHERE f.group_id = ? ORDER BY f.created_date ASC",
            (group_id,),
        )

    # --- users being deleted

    async def forget_user(self, user_id: str) -> None:
        """A deleted user leaves every group; groups they owned become ownerless."""
        await self.db.execute("UPDATE groups SET owner_id = NULL WHERE owner_id = ?", (user_id,))
        await self.db.execute("DELETE FROM group_members WHERE user_id = ?", (user_id,))
        await self.db.execute("DELETE FROM group_followers WHERE user_id = ?", (user_id,))
