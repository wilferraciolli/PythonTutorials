from datetime import datetime, timezone
from typing import Any, Dict
from uuid import uuid4

from api_response import envelope
from auth import AuthenticatedUser
from models import Link, Me, UserRole
from repositories.user_repository import UserRepository


class MeService:
    """
    Application service backing `/me`.

    The Clerk token only proves who the caller is (`sub`, name, email,
    roles). This service maps that external identity onto our own `users`
    row, creating one the first time a given Clerk user is seen.
    """

    def __init__(self, user_repository: UserRepository) -> None:
        self.user_repository = user_repository

    async def get_or_create_current_user(self, current_user: AuthenticatedUser) -> Dict[str, Any]:
        existing = await self.user_repository.get_by_external_id(current_user.id)
        if existing:
            return existing

        return await self.user_repository.create(
            user_id=str(uuid4()),
            name=current_user.name,
            email=current_user.email or f"{current_user.id}@clerk.local",
            role_ids=self._normalise_role_ids(current_user.role_ids),
            created_date=datetime.now(timezone.utc).isoformat(),
            external_user_id=current_user.id,
        )

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
                "self": Link(href="/me", method="GET"),
                "myTodos": Link(href=f"/users/{user_row['id']}/todos", method="GET"),
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
