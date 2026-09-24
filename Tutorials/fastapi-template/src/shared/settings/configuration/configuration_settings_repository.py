from typing import Any, Dict, Optional

from core.config.database import Database
from shared.settings.configuration.enums import ConfigurationSettingType


class ConfigurationSettingsRepository:
    """
    Repository for system configuration settings.

    This repository depends on the portable Database protocol, not SQLite,
    Cloudflare D1, or any other concrete database runtime.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_by_type(self, setting_type: ConfigurationSettingType) -> Optional[Dict[str, Any]]:
        return await self.db.fetch_one(
            "SELECT * FROM configuration_settings WHERE setting_type = ?",
            (setting_type.value,),
        )

    async def set_enabled(self, setting_type: ConfigurationSettingType, enabled: bool) -> Optional[Dict[str, Any]]:
        await self.db.execute(
            "UPDATE configuration_settings SET enabled = ? WHERE setting_type = ?",
            (1 if enabled else 0, setting_type.value),
        )
        return await self.get_by_type(setting_type)
