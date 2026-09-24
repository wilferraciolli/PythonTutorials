from typing import Any, List, Mapping, Optional

from core.config.database import Database
from core.security.roles import UserRole, parse_role_ids
from users.models import UserModel


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
    ) -> UserModel:
        await self.db.execute(
            "INSERT INTO users (id, external_user_id, name, email, created_date) VALUES (?, ?, ?, ?, ?)",
            (user_id, external_user_id, name, email, created_date),
        )

        await self.add_roles(user_id, role_ids)

        return await self._get_saved(user_id)

    async def get_by_id(self, user_id: str) -> Optional[UserModel]:
        row = await self.db.fetch_one(
            "SELECT * FROM user_detail_view WHERE id = ?",
            (user_id,),
        )

        return self._to_model(row)

    async def get_by_external_id(self, external_user_id: str) -> Optional[UserModel]:
        row = await self.db.fetch_one(
            "SELECT * FROM user_detail_view WHERE external_user_id = ?",
            (external_user_id,),
        )

        return self._to_model(row)

    async def get_all(self) -> List[UserModel]:
        rows = await self.db.fetch_all(
            "SELECT * FROM user_detail_view ORDER BY name",
        )

        return [self._to_model(row) for row in rows]

    async def search(self, term: Optional[str] = None) -> List[UserModel]:
        # Case-insensitive match on name or email (SQLite LIKE and D1 both
        # are for ASCII). No term returns everyone, same as get_all().
        if not term:
            return await self.get_all()

        like = f"%{term}%"
        rows = await self.db.fetch_all(
            "SELECT * FROM user_detail_view WHERE name LIKE ? OR email LIKE ? ORDER BY name",
            (like, like),
        )

        return [self._to_model(row) for row in rows]

    async def update(
        self,
        user_id: str,
        name: Optional[str] = None,
        email: Optional[str] = None,
        role_ids: Optional[list[UserRole]] = None,
    ) -> UserModel:
        """Change only the arguments that are not None."""
        updatable = {key: value for key, value in (("name", name), ("email", email)) if value is not None}

        if updatable:
            set_clause = ", ".join(f"{key} = ?" for key in updatable)

            await self.db.execute(
                f"UPDATE users SET {set_clause} WHERE id = ?",
                (*updatable.values(), user_id),
            )

        if role_ids is not None:
            await self.replace_roles(user_id, role_ids)

        return await self._get_saved(user_id)

    async def delete(self, user_id: str) -> None:
        await self.db.execute(
            "DELETE FROM user_roles WHERE user_id = ?",
            (user_id,),
        )

        await self.db.execute(
            "DELETE FROM users WHERE id = ?",
            (user_id,),
        )

    async def add_roles(self, user_id: str, role_ids: list[UserRole]) -> None:
        """Add roles the user doesn't already have; never removes any."""
        for role_id in role_ids:
            await self.db.execute(
                "INSERT OR IGNORE INTO user_roles (user_id, role_id) VALUES (?, ?)",
                (user_id, role_id.value),
            )

    async def replace_roles(self, user_id: str, role_ids: list[UserRole]) -> None:
        await self.db.execute(
            "DELETE FROM user_roles WHERE user_id = ?",
            (user_id,),
        )

        await self.add_roles(user_id, role_ids)

    async def _get_saved(self, user_id: str) -> UserModel:
        saved = await self.get_by_id(user_id)
        if saved is None:
            raise RuntimeError(f"saved user was not found: {user_id}")
        return saved

    @staticmethod
    def _to_model(row: Optional[Mapping[str, Any]]) -> Optional[UserModel]:
        if not row:
            return None

        return UserModel(
            **{key: value for key, value in row.items() if key != "role_ids"},
            role_ids=parse_role_ids(row["role_ids"]),
        )
