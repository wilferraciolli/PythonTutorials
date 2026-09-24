from core.common.base_dto import LinkedResource
from shared.settings.configuration.enums import ConfigurationSettingType


class ConfigurationSettingDTO(LinkedResource):
    id: str
    setting_type: ConfigurationSettingType
    enabled: bool
