from enum import Enum

from core.common.base_dto import EmbeddedRef


# Enum for user role
class UserRole(str, Enum):
    STANDARD = "STANDARD"
    ADMIN = "ADMIN"


# Display labels for metadata option lists.
ROLE_LABELS: dict[UserRole, str] = {
    UserRole.STANDARD: "Standard user",
    UserRole.ADMIN: "System Administrator",
}


def role_options() -> list[EmbeddedRef]:
    """The `values` list for any `roleIds` field in `_metadata`."""
    return [EmbeddedRef(id=role.value, value=label) for role, label in ROLE_LABELS.items()]


def to_role(role_id: str) -> UserRole | None:
    """
    A role name from outside (e.g. Clerk metadata, which is free text) as a
    UserRole, matching case-insensitively: "admin", "Admin" and " ADMIN "
    all mean ADMIN. None for anything that isn't a role.
    """
    try:
        return UserRole(str(role_id).strip().upper())
    except ValueError:
        return None


def parse_role_ids(value: str | None) -> list[str]:
    """
    Split `user_detail_view.role_ids` ('ADMIN,STANDARD', or NULL) into a
    sorted list. GROUP_CONCAT does not guarantee order, so sort for stable
    responses.
    """
    if not value:
        return []

    return sorted(role for role in value.split(",") if role)
