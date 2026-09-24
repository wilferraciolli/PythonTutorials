from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from core.common.api_response import API_PREFIX, envelope
from core.security.auth import AuthenticatedUser
from core.common.base_dto import Link
from core.security.roles import UserRole
from users.profiles.schemas import Me
from users.user_repository import UserRepository


class MeService:
    """
    Application service backing `/me`.

    The Clerk token only proves who the caller is (`sub`, name, email,
    roles). This service maps that external identity onto our own `users`
    row, creating one the first time a given Clerk user is seen.

    On every later call, roles in the Clerk token that the saved user lacks
    are added — never removed. Roles granted through our own API (e.g. ADMIN)
    therefore survive even if Clerk stops sending them; revoking a role is
    done through `/users`, not Clerk.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def get_or_create_current_user(self, current_user: AuthenticatedUser) -> Dict[str, Any]:
        existing = await self.user_repository.get_by_external_id(current_user.id)
        if existing:
            return await self._add_missing_clerk_roles(existing, current_user)

        return await self.user_repository.create(
            user_id=str(uuid4()),
            name=current_user.name,
            email=current_user.email or f"{current_user.id}@clerk.local",
            role_ids=self._normalise_role_ids(current_user.role_ids),
            created_date=datetime.now(timezone.utc).isoformat(),
            external_user_id=current_user.id,
        )

    async def _add_missing_clerk_roles(
        self,
        existing: Dict[str, Any],
        current_user: AuthenticatedUser,
    ) -> Dict[str, Any]:
        saved = set(existing["roleIds"])
        missing = [role for role in self._normalise_role_ids(current_user.role_ids) if role.value not in saved]

        # STANDARD is only the fallback for a user with no roles (auth.py
        # hands it out when the token has none), so don't add it to someone
        # who already has roles.
        if saved:
            missing = [role for role in missing if role is not UserRole.STANDARD]

        if not missing:
            return existing

        await self.user_repository.add_roles(existing["id"], missing)
        updated = await self.user_repository.get_by_id(existing["id"])
        if updated is None:
            raise RuntimeError(f"user disappeared while adding roles: {existing['id']}")
        return updated

    def _normalise_role_ids(self, role_ids: list[str]) -> list[UserRole]:
        normalised = [role for role in (self._to_role(role) for role in role_ids) if role]
        return list(dict.fromkeys(normalised)) or [UserRole.STANDARD]

    def _to_role(self, role_id: str) -> UserRole | None:
        try:
            return UserRole(role_id)
        except ValueError:
            return None

    def build_response(self, user_row: Dict[str, Any]) -> dict[str, Any]:
        me = Me(
            id=user_row["id"],
            name=user_row["name"],
            email=user_row["email"],
            roleIds=user_row["roleIds"],
            links={
                "self": Link(href=f"{API_PREFIX}/me", method="GET"),
                "userProfile": Link(href=f"{API_PREFIX}/users/{user_row['id']}/profile", method="GET"),
            },
        )

        return envelope(
            data_name="me",
            data=me,
            metadata={
                "id": {
                    "readOnly": True,
                    "hidden": True,
                },
                "name": {
                    "readOnly": True,
                },
                "email": {
                    "readOnly": True,
                },
                "roleIds": {
                    "readOnly": True,
                },
            },
            meta_links={},
        )
