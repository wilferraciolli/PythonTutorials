from enum import Enum
from typing import Type

from core.common.api_response import API_PREFIX
from core.common.base_dto import Link, FieldMetadata, EmbeddedRef
from shared.settings.region.constants import LINK_SELF, LINK_UPDATE_SETTINGS, SYSTEM_SETTINGS_DATA_NAME
from shared.settings.region.enums import SupportedTimeZones, SupportedLanguages, SupportedCurrencies, SupportedThemes
from shared.settings.region.models import RegionSettingModel
from shared.settings.region.region_settings_repository import RegionSettingsRepository
from shared.settings.region.schemas import SystemSettingsDTO, SystemSettingsMetadata, SystemSettingsResponse, \
    SystemSettingsUpdateRequest


class SystemSettingsService:
    """
    Application service for the system settings: the single SYSTEM
    region_settings row every user falls back to until they save their own.
    """

    def __init__(
            self,
            region_repository: RegionSettingsRepository
    ) -> None:
        self.region_repository = region_repository

    async def get_system_settings(self) -> SystemSettingsDTO:
        model = await self.region_repository.get_system_settings()
        if model is None:
            raise RuntimeError("system region settings are missing; run the migrations")

        return self.to_dto(model)

    async def update_system_settings(
            self,
            request: SystemSettingsUpdateRequest,
    ) -> SystemSettingsDTO:
        model = await self.region_repository.update_system_settings(
            timezone=request.timezone.value,
            language=request.language.value,
            currency=request.currency.value,
            theme=request.theme.value,
        )

        return self.to_dto(model)

    def to_dto(self, model: RegionSettingModel) -> SystemSettingsDTO:
        return SystemSettingsDTO(
            **model.model_dump(),
            links=self.build_links(),
        )

    def build_metadata(self, system_settings: SystemSettingsDTO) -> SystemSettingsMetadata:
        # Receives the DTO so rules can depend on its current state
        # (e.g. restrict `values` or make a field readOnly).
        return SystemSettingsMetadata(
            id=FieldMetadata(readOnly=True, hidden=True),
            timezone=self._choice_field(SupportedTimeZones),
            language=self._choice_field(SupportedLanguages),
            currency=self._choice_field(SupportedCurrencies),
            theme=self._choice_field(SupportedThemes),
        )

    @staticmethod
    def build_links() -> dict[str, Link]:
        url = f"{API_PREFIX}/admin/settings"
        return {
            LINK_SELF: Link(href=url, method="GET"),
            LINK_UPDATE_SETTINGS: Link(href=url, method="PUT"),
        }

    @staticmethod
    def _choice_field(enum_type: Type[Enum]) -> FieldMetadata:
        return FieldMetadata(
            mandatory=True,
            values=[EmbeddedRef(id=member.value, value=member.value) for member in enum_type],
        )

    def build_response(self, system_settings: SystemSettingsDTO) -> SystemSettingsResponse:
        return SystemSettingsResponse.of(
            SYSTEM_SETTINGS_DATA_NAME,
            system_settings,
            self.build_metadata(system_settings),
        )
