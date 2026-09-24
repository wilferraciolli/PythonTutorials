from datetime import datetime, timezone
from uuid import uuid4

from core.common.api_response import API_PREFIX
from core.common.base_dto import FieldMetadata, Link
from core.security.auth import AuthenticatedUser
from core.security.roles import UserRole, to_role
from users.models import UserModel
from users.profiles.constants import LINK_SELF, LINK_USER_PROFILE, ME_DATA_NAME
from users.profiles.schemas import MeDTO, MeMetadata, MeResponse
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

    async def get_me(self, current_user: AuthenticatedUser) -> MeDTO:
        return self.to_dto(await self.get_or_create_current_user(current_user))

    async def get_or_create_current_user(self, current_user: AuthenticatedUser) -> UserModel:
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
        existing: UserModel,
        current_user: AuthenticatedUser,
    ) -> UserModel:
        saved = set(existing.role_ids)
        missing = [role for role in self._normalise_role_ids(current_user.role_ids) if role not in saved]

        # STANDARD is only the fallback for a user with no roles (auth.py
        # hands it out when the token has none), so don't add it to someone
        # who already has roles.
        if saved:
            missing = [role for role in missing if role is not UserRole.STANDARD]

        if not missing:
            return existing

        await self.user_repository.add_roles(existing.id, missing)
        updated = await self.user_repository.get_by_id(existing.id)
        if updated is None:
            raise RuntimeError(f"user disappeared while adding roles: {existing.id}")
        return updated

    @staticmethod
    def _normalise_role_ids(role_ids: list[str]) -> list[UserRole]:
        # Case-insensitive (to_role): Clerk metadata is free text.
        normalised = [role for role in (to_role(role_id) for role_id in role_ids) if role]
        return list(dict.fromkeys(normalised)) or [UserRole.STANDARD]

    @staticmethod
    def to_dto(model: UserModel) -> MeDTO:
        return MeDTO(
            id=model.id,
            name=model.name,
            email=model.email,
            roleIds=model.role_ids,
            links={
                LINK_SELF: Link(href=f"{API_PREFIX}/me", method="GET"),
                LINK_USER_PROFILE: Link(href=f"{API_PREFIX}/users/{model.id}/profile", method="GET"),
            },
        )

    @staticmethod
    def build_metadata() -> MeMetadata:
        return MeMetadata(
            id=FieldMetadata(readOnly=True, hidden=True),
            name=FieldMetadata(readOnly=True),
            email=FieldMetadata(readOnly=True),
            roleIds=FieldMetadata(readOnly=True),
        )

    def build_response(self, me: MeDTO) -> MeResponse:
        return MeResponse.of(ME_DATA_NAME, me, self.build_metadata())
