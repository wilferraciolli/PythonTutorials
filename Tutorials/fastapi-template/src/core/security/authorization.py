from dataclasses import dataclass
from typing import Optional

from fastapi import Depends, HTTPException, Request, status

from core.config.database import get_database
from core.security.auth import AuthenticatedUser, get_authenticated_user
from core.security.roles import UserRole, parse_role_ids


@dataclass(frozen=True)
class Caller:
    """
    The signed-in caller as our database sees them.

    `user_id` is their `users.id`, or None if they have never called `/me`
    and so have no saved user yet. `role_ids` are their saved roles — the
    source of truth for permissions, not the Clerk token.
    """
    external_id: str
    user_id: Optional[str]
    role_ids: list[str]

    @property
    def is_admin(self) -> bool:
        return UserRole.ADMIN.value in self.role_ids


async def get_caller(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
) -> Caller:
    """
    Route dependency: who is calling, with their saved roles.

    Reads `user_detail_view` rather than the users repository, so this
    package never imports the users domain.
    """
    row = await get_database(request).fetch_one(
        "SELECT id, role_ids FROM user_detail_view WHERE external_user_id = ?",
        (current_user.id,),
    )

    if not row:
        return Caller(external_id=current_user.id, user_id=None, role_ids=[])

    return Caller(
        external_id=current_user.id,
        user_id=row["id"],
        role_ids=parse_role_ids(row["role_ids"]),
    )


async def require_admin(caller: Caller = Depends(get_caller)) -> Caller:
    """
    Route dependency: only callers whose saved roles include ADMIN get through.

    An admin granted through the API stays an admin even if Clerk stops
    sending the role. 401 if not signed in (raised by get_authenticated_user);
    403 if signed in but not an admin, including a caller with no saved user.
    """
    if not caller.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    return caller
