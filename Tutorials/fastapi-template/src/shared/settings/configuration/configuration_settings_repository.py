from typing import Any, Dict, List, Optional

from core.config.database import Database

from core.common.models import UserRole
from shared.settings.configuration.enums import ConfigurationSettingType
from shared.settings.region.enums import RegionSettingOwnerType


class ConfigurationSettingsRepository:
    """
    Repository for configuration settings operations.

    This repository depends on the portable Database protocol, not SQLite,
    Cloudflare D1, or any other concrete database runtime.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    # Get system Settings
    async def get_config_settings(self, configurationSetting: ConfigurationSettingType) -> Optional[Dict[str, Any]]:
        result = await self.db.fetch_one(
            "SELECT * FROM configuration_settings WHERE setting_type = ?",
            (configurationSetting)
        )

        if not result:
            return None

        return result


    # Update user Settings
    async def update_config_settings(self, user_id: str, **fields: Any) -> Optional[Dict[str, Any]]:
        result = await self.db.fetch_one(
            "SELECT * FROM configuration_settings WHERE id = ?",
            (user_id)
        )

        if not result:
            return None

        return result




















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
        user = await self.db.fetch_one(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        )

        if not user:
            return None

        user["roleIds"] = await self.get_role_ids(user_id)
        return user



    async def get_all(self) -> List[Dict[str, Any]]:
        users = await self.db.fetch_all(
            "SELECT * FROM users ORDER BY name",
        )

        for user in users:
            user["roleIds"] = await self.get_role_ids(user["id"])

        return users

    async def search(self, term: Optional[str] = None) -> List[Dict[str, Any]]:
        # Case-insensitive match on name or email (SQLite LIKE and D1 both
        # are for ASCII). No term returns everyone, same as get_all().
        if not term:
            return await self.get_all()

        like = f"%{term}%"
        users = await self.db.fetch_all(
            "SELECT * FROM users WHERE name LIKE ? OR email LIKE ? ORDER BY name",
            (like, like),
        )

        for user in users:
            user["roleIds"] = await self.get_role_ids(user["id"])

        return users

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

    async def get_role_ids(self, user_id: str) -> list[str]:
        rows = await self.db.fetch_all(
            "SELECT role_id FROM user_roles WHERE user_id = ? ORDER BY role_id",
            (user_id,),
        )

        return [row["role_id"] for row in rows]

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
