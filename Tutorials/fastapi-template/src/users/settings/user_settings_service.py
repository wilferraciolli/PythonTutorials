from typing import Any, Dict, Optional

from core.common.api_response import API_PREFIX, envelope
from core.common.base_dto import Link
from shared.settings.region.enums import (
    SupportedCurrencies,
    SupportedLanguages,
    SupportedThemes,
    SupportedTimeZones,
)
from shared.settings.region.region_settings_repository import RegionSettingsRepository
from shared.settings.region.schemas import RegionSettingDTO, RegionSettingPayload
from users.settings.constants import (
    LINK_RESET_SETTINGS,
    LINK_SELF,
    LINK_UPDATE_SETTINGS,
    USER_SETTINGS_DATA_NAME,
)
from users.user_repository import UserRepository


class UserSettingsService:
    """
    Application service for a user's settings.

    A user without saved settings sees the SYSTEM defaults (owner_type SYSTEM)
    until they save their own, at which point a USER row is created.
    """

    def __init__(
        self,
        user_repository: UserRepository,
        region_repository: RegionSettingsRepository,
    ) -> None:
        self.user_repository = user_repository
        self.region_repository = region_repository

    async def get_region_settings(self, user_id: str) -> Optional[RegionSettingDTO]:
        if not await self.user_repository.get_by_id(user_id):
            return None

        row = await self.region_repository.get_user_settings(user_id)
        if row is None:
            row = await self.region_repository.get_system_settings()
        if row is None:
            raise RuntimeError("system region settings are missing; run the migrations")

        return self.to_region_setting(user_id, row)

    async def update_region_settings(
        self,
        user_id: str,
        payload: RegionSettingPayload,
    ) -> Optional[RegionSettingDTO]:
        if not await self.user_repository.get_by_id(user_id):
            return None

        row = await self.region_repository.upsert_user_settings(
            user_id,
            timezone=payload.timezone.value,
            language=payload.language.value,
            currency=payload.currency.value,
            theme=payload.theme.value,
        )

        return self.to_region_setting(user_id, row)

    async def reset_region_settings(self, user_id: str) -> bool:
        if not await self.user_repository.get_by_id(user_id):
            return False

        await self.region_repository.delete_user_settings(user_id)
        return True

    def to_region_setting(self, user_id: str, row: Dict[str, Any]) -> RegionSettingDTO:
        return RegionSettingDTO(
            id=row["id"],
            owner_type=row["owner_type"],
            timezone=row["timezone"],
            language=row["language"],
            currency=row["currency"],
            theme=row["theme"],
            links=self.build_links(user_id),
        )

    def build_links(self, user_id: str) -> dict[str, Link]:
        url = f"{API_PREFIX}/users/{user_id}/settings"
        return {
            LINK_SELF: Link(href=url, method="GET"),
            LINK_UPDATE_SETTINGS: Link(href=url, method="PUT"),
            LINK_RESET_SETTINGS: Link(href=url, method="DELETE"),
        }

    def build_metadata(self) -> dict[str, Any]:
        return {
            "id": {"readOnly": True, "hidden": True},
            "owner_type": {"readOnly": True},
            "timezone": {"mandatory": True, "values": self._options(SupportedTimeZones)},
            "language": {"mandatory": True, "values": self._options(SupportedLanguages)},
            "currency": {"mandatory": True, "values": self._options(SupportedCurrencies)},
            "theme": {"mandatory": True, "values": self._options(SupportedThemes)},
        }

    @staticmethod
    def _options(enum_type: Any) -> list[dict[str, str]]:
        return [{"id": member.value, "value": member.value} for member in enum_type]

    def build_response(self, settings: RegionSettingDTO) -> Dict[str, Any]:
        return envelope(
            data_name=USER_SETTINGS_DATA_NAME,
            data=settings,
            metadata=self.build_metadata(),
            meta_links={},
        )
