from typing import Any, Dict, List, Optional

from core.config.database import Database
from core.security.roles import UserRole, parse_role_ids


class UserRepository:
    """
    Repository for user database operations.

    Reads go through `user_detail_view`, which returns each user with their
    roles in one row, so listing users is one query rather than one per user.

    This repository depends on the portable Database protocol, not SQLite,
    Cloudflare D1, or any other concrete database runtime.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def create(
        self,
        user_id: str,
        name: str,
        email: str,
        role_ids: list[UserRole],
        created_date: str,
        external_user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        role_ids = self.normalise_role_ids(role_ids)
        await self.db.execute(
            "INSERT INTO users (id, external_user_id, name, email, created_date) VALUES (?, ?, ?, ?, ?)",
            (user_id, external_user_id, name, email, created_date),
        )

        for role_id in role_ids:
            await self.db.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, role_id.value),
            )

        created = await self.get_by_id(user_id)
        if created is None:
            raise RuntimeError(f"created user was not found: {user_id}")
        return created

    async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        row = await self.db.fetch_one(
            "SELECT * FROM user_detail_view WHERE id = ?",
            (user_id,),
        )

        return self._to_user(row) if row else None

    async def get_by_external_id(self, external_user_id: str) -> Optional[Dict[str, Any]]:
        row = await self.db.fetch_one(
            "SELECT * FROM user_detail_view WHERE external_user_id = ?",
            (external_user_id,),
        )

        return self._to_user(row) if row else None

    async def get_all(self) -> List[Dict[str, Any]]:
        rows = await self.db.fetch_all(
            "SELECT * FROM user_detail_view ORDER BY name",
        )

        return [self._to_user(row) for row in rows]

    async def search(self, term: Optional[str] = None) -> List[Dict[str, Any]]:
        # Case-insensitive match on name or email (SQLite LIKE and D1 both
        # are for ASCII). No term returns everyone, same as get_all().
        if not term:
            return await self.get_all()

        like = f"%{term}%"
        rows = await self.db.fetch_all(
            "SELECT * FROM user_detail_view WHERE name LIKE ? OR email LIKE ? ORDER BY name",
            (like, like),
        )

        return [self._to_user(row) for row in rows]

    async def update(self, user_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
        role_ids = fields.pop("roleIds", None)

        updatable = {key: value for key, value in fields.items() if value is not None}

        if updatable:
            set_clause = ", ".join(f"{key} = ?" for key in updatable)
            values = list(updatable.values()) + [user_id]

            await self.db.execute(
                f"UPDATE users SET {set_clause} WHERE id = ?",
                tuple(values),
            )

        if role_ids is not None:
            await self.replace_roles(user_id, role_ids)

        return await self.get_by_id(user_id)

    async def delete(self, user_id: str) -> bool:
        existing = await self.get_by_id(user_id)

        if not existing:
            return False

        await self.db.execute(
            "DELETE FROM user_roles WHERE user_id = ?",
            (user_id,),
        )

        await self.db.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,),
        )

        return True

    async def add_roles(self, user_id: str, role_ids: list[UserRole]) -> None:
        """Add roles the user doesn't already have; never removes any."""
        for role_id in role_ids:
            await self.db.execute(
                "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, role_id.value),
            )

    async def replace_roles(
        self,
        user_id: str,
        role_ids: list[UserRole],
    ) -> None:
        role_ids = self.normalise_role_ids(role_ids)
        await self.db.execute(
            "DELETE FROM user_roles WHERE user_id = ?",
            (user_id,),
        )

        for role_id in role_ids:
            await self.db.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, role_id.value),
            )

    def normalise_role_ids(self, role_ids: list[UserRole]) -> list[UserRole]:
        if not role_ids:
            return [UserRole.STANDARD]

        return list(dict.fromkeys(role_ids))

    @staticmethod
    def _to_user(row: Dict[str, Any]) -> Dict[str, Any]:
        user = dict(row)
        user["roleIds"] = parse_role_ids(user.pop("role_ids"))
        return user
