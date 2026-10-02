from pydantic import BaseModel
from wiltech_labs_rest import ApiResponse, FieldMetadata, LinkedResource

from shared.settings.region.enums import (
    SupportedCurrencies,
    SupportedLanguages,
    SupportedLocales,
    SupportedThemes,
    SupportedTimeZones,
)


# --- Request: what the client sends -----------------------------------------

class SystemSettingsUpdateRequest(BaseModel):
    """
    Body of `PUT /admin/settings`.

    Only the fields an admin may change — no id, owner_type or links, because
    the server decides those.
    """
    timezone: SupportedTimeZones
    language: SupportedLanguages
    locale: SupportedLocales
    currency: SupportedCurrencies
    theme: SupportedThemes


# --- DTO: what the application service returns ------------------------------

class SystemSettingsDTO(LinkedResource):
    """A system's settings plus the links the client can follow from them."""
    id: str
    timezone: SupportedTimeZones
    language: SupportedLanguages
    locale: SupportedLocales
    currency: SupportedCurrencies
    theme: SupportedThemes


class SystemSettingsMetadata(BaseModel):
    """How the client should treat each field of `SystemSettingsDTO`."""
    id: FieldMetadata
    timezone: FieldMetadata
    language: FieldMetadata
    locale: FieldMetadata
    currency: FieldMetadata
    theme: FieldMetadata


# --- Response: the envelope the service builds ------------------------------

SystemSettingsResponse = ApiResponse[SystemSettingsDTO, SystemSettingsMetadata]
