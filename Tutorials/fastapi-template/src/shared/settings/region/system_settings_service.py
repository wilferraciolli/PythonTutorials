from wiltech_labs_rest import API_PREFIX, FieldMetadata, Link, choice_field

from shared.settings.region.constants import LINK_SELF, LINK_UPDATE_SETTINGS, SYSTEM_SETTINGS_DATA_NAME
from shared.settings.region.enums import SupportedTimeZones, SupportedLanguages, SupportedLocales, SupportedCurrencies, SupportedThemes
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
            locale=request.locale.value,
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
            timezone=choice_field(SupportedTimeZones),
            language=choice_field(SupportedLanguages),
            locale=choice_field(SupportedLocales),
            currency=choice_field(SupportedCurrencies),
            theme=choice_field(SupportedThemes),
        )

    @staticmethod
    def build_links() -> dict[str, Link]:
        url = f"{API_PREFIX}/admin/settings"
        return {
            LINK_SELF: Link(href=url, method="GET"),
            LINK_UPDATE_SETTINGS: Link(href=url, method="PUT"),
        }

    def build_response(self, system_settings: SystemSettingsDTO) -> SystemSettingsResponse:
        return SystemSettingsResponse.of(
            SYSTEM_SETTINGS_DATA_NAME,
            system_settings,
            self.build_metadata(system_settings),
        )
