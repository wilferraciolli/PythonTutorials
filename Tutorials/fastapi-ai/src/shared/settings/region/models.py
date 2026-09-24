from pydantic import BaseModel

from shared.settings.region.enums import (
    RegionSettingOwnerType,
    SupportedCurrencies,
    SupportedLanguages,
    SupportedThemes,
    SupportedTimeZones,
)


class RegionSettingModel(BaseModel):
    """A `region_settings` database row."""
    id: str
    owner_type: RegionSettingOwnerType
    timezone: SupportedTimeZones
    language: SupportedLanguages
    currency: SupportedCurrencies
    theme: SupportedThemes
