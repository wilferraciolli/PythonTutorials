from enum import Enum
from typing import Optional, Type

from core.common.api_response import API_PREFIX
from core.common.base_dto import EmbeddedRef, FieldMetadata, Link
from shared.settings.region.enums import (
    SupportedCurrencies,
    SupportedLanguages,
    SupportedThemes,
    SupportedTimeZones,
)
from shared.settings.region.region_settings_repository import RegionSettingsRepository
from shared.settings.region.models import RegionSettingModel
from users.settings.constants import (
    LINK_RESET_SETTINGS,
    LINK_SELF,
    LINK_UPDATE_SETTINGS,
    USER_SETTINGS_DATA_NAME,
)
from users.settings.schemas import (
    UserSettingsDTO,
    UserSettingsMetadata,
    UserSettingsResponse,
    UserSettingsUpdateRequest,
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

    async def get_user_settings(self, user_id: str) -> Optional[UserSettingsDTO]:
        if not await self.user_repository.get_by_id(user_id):
            return None

        model = await self.region_repository.get_user_settings(user_id)
        if model is None:
            model = await self.region_repository.get_system_settings()
        if model is None:
            raise RuntimeError("system region settings are missing; run the migrations")

        return self.to_dto(user_id, model)

    async def update_user_settings(
            self,
            user_id: str,
            request: UserSettingsUpdateRequest,
    ) -> Optional[UserSettingsDTO]:
        if not await self.user_repository.get_by_id(user_id):
            return None

        model = await self.region_repository.upsert_user_settings(
            user_id,
            timezone=request.timezone.value,
            language=request.language.value,
            currency=request.currency.value,
            theme=request.theme.value,
        )

        return self.to_dto(user_id, model)

    async def reset_user_settings(self, user_id: str) -> bool:
        if not await self.user_repository.get_by_id(user_id):
            return False

        await self.region_repository.delete_user_settings(user_id)
        return True

    def to_dto(self, user_id: str, model: RegionSettingModel) -> UserSettingsDTO:
        return UserSettingsDTO(
            **model.model_dump(),
            links=self.build_links(user_id),
        )

    def build_metadata(self, user_settings: UserSettingsDTO) -> UserSettingsMetadata:
        # Receives the DTO so rules can depend on its current state
        # (e.g. restrict `values` or make a field readOnly).
        return UserSettingsMetadata(
            id=FieldMetadata(readOnly=True, hidden=True),
            owner_type=FieldMetadata(readOnly=True),
            timezone=self._choice_field(SupportedTimeZones),
            language=self._choice_field(SupportedLanguages),
            currency=self._choice_field(SupportedCurrencies),
            theme=self._choice_field(SupportedThemes),
        )

    @staticmethod
    def build_links(user_id: str) -> dict[str, Link]:
        url = f"{API_PREFIX}/users/{user_id}/settings"
        return {
            LINK_SELF: Link(href=url, method="GET"),
            LINK_UPDATE_SETTINGS: Link(href=url, method="PUT"),
            LINK_RESET_SETTINGS: Link(href=url, method="DELETE"),
        }

    @staticmethod
    def _choice_field(enum_type: Type[Enum]) -> FieldMetadata:
        return FieldMetadata(
            mandatory=True,
            values=[EmbeddedRef(id=member.value, value=member.value) for member in enum_type],
        )

    def build_response(self, user_settings: UserSettingsDTO) -> UserSettingsResponse:
        return UserSettingsResponse.of(
            USER_SETTINGS_DATA_NAME,
            user_settings,
            self.build_metadata(user_settings),
        )
