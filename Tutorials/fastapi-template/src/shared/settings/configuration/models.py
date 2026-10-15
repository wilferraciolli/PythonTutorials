from pydantic import BaseModel

from shared.settings.configuration.enums import ConfigurationSettingType


class ConfigurationSettingModel(BaseModel):
    """A `configuration_settings` database row."""
    id: str
    setting_type: ConfigurationSettingType
    enabled: bool
