from enum import Enum


# Enum for Region Settings Owner Type
class RegionSettingOwnerType(str, Enum):
    SYSTEM = "SYSTEM"
    USER = "USER"


# IANA timezones
class SupportedTimeZones(str, Enum):
    LONDON = "Europe/London"
    SAO_PAULO = "America/Sao_Paulo"
    CYPRUS = "Asia/Nicosia"


# BCP 47 / ISO standards languages
class SupportedLanguages(str, Enum):
    EN_GB = "en-GB"
    EL = "el"
    PT_BR = "pt-BR"


# ISO 4217 currency values
class SupportedCurrencies(str, Enum):
    GBP = "GBP"
    EUR = "EUR"
    BRL = "BRL"


class SupportedThemes(str, Enum):
    LIGHT = "light"
    DARK = "dark"
