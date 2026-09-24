from pydantic import BaseModel

from core.common.api_response import ApiResponse
from core.common.base_dto import FieldMetadata, LinkedResource
from shared.settings.region.enums import (
    RegionSettingOwnerType,
    SupportedCurrencies,
    SupportedLanguages,
    SupportedThemes,
    SupportedTimeZones,
)


# --- Request: what the client sends -----------------------------------------

class UserSettingsUpdateRequest(BaseModel):
    """
    Body of `PUT /users/{user_id}/settings`.

    Only the fields a user may change — no id, owner_type or links, because
    the server decides those.
    """
    timezone: SupportedTimeZones
    language: SupportedLanguages
    currency: SupportedCurrencies
    theme: SupportedThemes


# --- DTO: what the application service returns ------------------------------

class UserSettingsDTO(LinkedResource):
    """A user's settings plus the links the client can follow from them."""
    id: str
    owner_type: RegionSettingOwnerType
    timezone: SupportedTimeZones
    language: SupportedLanguages
    currency: SupportedCurrencies
    theme: SupportedThemes


class UserSettingsMetadata(BaseModel):
    """How the client should treat each field of `UserSettingsDTO`."""
    id: FieldMetadata
    owner_type: FieldMetadata
    timezone: FieldMetadata
    language: FieldMetadata
    currency: FieldMetadata
    theme: FieldMetadata


# --- Response: the envelope the service builds ------------------------------

UserSettingsResponse = ApiResponse[UserSettingsDTO, UserSettingsMetadata]
