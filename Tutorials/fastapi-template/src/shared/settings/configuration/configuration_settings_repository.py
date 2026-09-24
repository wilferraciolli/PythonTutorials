from typing import Any, Mapping, Optional

from core.config.database import Database
from shared.settings.configuration.enums import ConfigurationSettingType
from shared.settings.configuration.models import ConfigurationSettingModel


class ConfigurationSettingsRepository:
    """
    Repository for system configuration settings.

    This repository depends on the portable Database protocol, not SQLite,
    Cloudflare D1, or any other concrete database runtime.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def get_by_type(self, setting_type: ConfigurationSettingType) -> Optional[ConfigurationSettingModel]:
        row = await self.db.fetch_one(
            "SELECT * FROM configuration_settings WHERE setting_type = ?",
            (setting_type.value,),
        )

        return self._to_model(row)

    async def set_enabled(self, setting_type: ConfigurationSettingType, enabled: bool) -> Optional[ConfigurationSettingModel]:
        await self.db.execute(
            "UPDATE configuration_settings SET enabled = ? WHERE setting_type = ?",
            (1 if enabled else 0, setting_type.value),
        )

        return await self.get_by_type(setting_type)

    @staticmethod
    def _to_model(row: Optional[Mapping[str, Any]]) -> Optional[ConfigurationSettingModel]:
        return ConfigurationSettingModel(**row) if row else None
