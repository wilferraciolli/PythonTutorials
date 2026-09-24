from fastapi import Depends, HTTPException, Request, status

from core.config.database import get_database
from core.security.auth import AuthenticatedUser, get_authenticated_user
from core.security.roles import UserRole, parse_role_ids


async def require_admin(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
) -> AuthenticatedUser:
    """
    Route dependency: only callers whose saved roles include ADMIN get through.

    Roles are read from our own database (`user_detail_view`), not the Clerk
    token, so an admin granted through the API stays an admin even if Clerk
    stops sending the role. Reading the view keeps this package free of any
    import from the users domain.

    401 if not signed in (raised by get_authenticated_user); 403 if signed in
    but not an admin, including a caller who has never hit `/me` and so has
    no saved user yet.
    """
    row = await get_database(request).fetch_one(
        "SELECT role_ids FROM user_detail_view WHERE external_user_id = ?",
        (current_user.id,),
    )

    if not row or UserRole.ADMIN.value not in parse_role_ids(row["role_ids"]):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")

    return current_user
