from enum import Enum


# Enum for user role
class UserRole(str, Enum):
    STANDARD = "STANDARD"
    ADMIN = "ADMIN"


def parse_role_ids(value: str | None) -> list[str]:
    """
    Split `user_detail_view.role_ids` ('ADMIN,STANDARD', or NULL) into a
    sorted list. GROUP_CONCAT does not guarantee order, so sort for stable
    responses.
    """
    if not value:
        return []

    return sorted(role for role in value.split(",") if role)
