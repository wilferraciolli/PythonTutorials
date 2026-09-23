from fastapi import Depends, HTTPException, Request

from auth import AuthenticatedUser, get_authenticated_user
from database import get_database
from repositories.user_repository import UserRepository
from services.me_service import MeService


async def get_current_user_id(
    user_id: str,
    request: Request,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
) -> str:
    """
    The user whose resources are being addressed: the `{user_id}` in the path.

    The caller (Clerk identity -> our `users` row, the same mapping /me uses)
    is resolved separately and compared with it. Business-logic seam: today
    only the owner may touch a user's chats, todos and assistant; loosen it
    here (e.g. admins, or users who share something) once those rules exist.
    """
    db = get_database(request)
    me_service = MeService(UserRepository(db))
    caller = await me_service.get_or_create_current_user(current_user)
    if caller["id"] != user_id:
        raise HTTPException(status_code=403, detail="Not allowed to access this user's resources")
    return user_id
