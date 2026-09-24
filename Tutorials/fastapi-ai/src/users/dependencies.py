from fastapi import Depends, Request

from core.config.database import get_database
from core.security.auth import AuthenticatedUser, get_authenticated_user
from users.profiles.me_service import MeService
from users.user_repository import UserRepository


async def ensure_current_user(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
) -> None:
    """
    Router dependency (main.py): create the caller's `users` row on their
    first request, and add any new Clerk roles — exactly what `/me` does.

    It runs before the route's own dependencies, so `get_caller` and
    `require_admin` (core/security) always find the caller in
    `user_detail_view` and `Caller.user_id` is set inside every route.
    """
    await MeService(UserRepository(get_database(request))).get_or_create_current_user(current_user)
