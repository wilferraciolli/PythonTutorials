from typing import Any, Dict, Optional

from core.config.database import Database
from shared.settings.region.enums import RegionSettingOwnerType


class RegionSettingsRepository:
    """
    Repository for region settings database operations.

    A user's own row uses the user's id as its primary key (owner_type USER);
    the single SYSTEM row holds the defaults every user falls back to.

    This repository depends on the portable Database protocol, not SQLite,
    Cloudflare D1, or any other concrete database runtime.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_system_settings(self) -> Optional[Dict[str, Any]]:
        return await self.db.fetch_one(
            "SELECT * FROM region_settings WHERE owner_type = ?",
            (RegionSettingOwnerType.SYSTEM.value,),
        )

    async def get_user_settings(self, user_id: str) -> Optional[Dict[str, Any]]:
        return await self.db.fetch_one(
            "SELECT * FROM region_settings WHERE id = ? AND owner_type = ?",
            (user_id, RegionSettingOwnerType.USER.value),
        )

    async def upsert_user_settings(
        self,
        user_id: str,
        timezone: str,
        language: str,
        currency: str,
        theme: str,
    ) -> Dict[str, Any]:
        await self.db.execute(
            "INSERT INTO region_settings (id, owner_type, timezone, language, currency, theme) "
            "VALUES (?, ?, ?, ?, ?, ?) "
            "ON CONFLICT(id) DO UPDATE SET "
            "timezone = excluded.timezone, language = excluded.language, "
            "currency = excluded.currency, theme = excluded.theme",
            (user_id, RegionSettingOwnerType.USER.value, timezone, language, currency, theme),
        )

        saved = await self.get_user_settings(user_id)
        if saved is None:
            raise RuntimeError(f"saved region settings were not found: {user_id}")
        return saved

    async def delete_user_settings(self, user_id: str) -> None:
        await self.db.execute(
            "DELETE FROM region_settings WHERE id = ? AND owner_type = ?",
            (user_id, RegionSettingOwnerType.USER.value),
        )
