from pydantic import BaseModel

from core.common.base_dto import LinkedResource
from shared.settings.region.enums import RegionSettingOwnerType, SupportedTimeZones, SupportedLanguages, SupportedCurrencies, SupportedThemes


class RegionSettingDTO(LinkedResource):
    id: str
    owner_type: RegionSettingOwnerType
    timezone: SupportedTimeZones
    language: SupportedLanguages
    currency: SupportedCurrencies
    theme: SupportedThemes


class RegionSettingPayload(BaseModel):
    timezone: SupportedTimeZones
    language: SupportedLanguages
    currency: SupportedCurrencies
    theme: SupportedThemes
