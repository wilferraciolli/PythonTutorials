from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from auth import AuthenticatedUser, get_authenticated_user
from database import get_database
from repositories.user_repository import UserRepository
from services.me_service import MeService
from services.user_profile_service import UserProfileService

router = APIRouter(prefix="/users", tags=["userprofiles"])


def get_user_profile_service(request: Request) -> UserProfileService:
    db = get_database(request)
    return UserProfileService(UserRepository(db))


async def get_current_user_row(
    request: Request,
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
) -> dict[str, Any]:
    # The caller's own `users` row — same identity-to-row mapping /me uses.
    # The profile is asked for by {user_id} in the path, which may or may
    # not be the caller; the service compares the two.
    db = get_database(request)
    return await MeService(UserRepository(db)).get_or_create_current_user(current_user)


@router.get("/{user_id}/profile")
async def get_user_profile(
    user_id: str,
    caller: dict[str, Any] = Depends(get_current_user_row),
    service: UserProfileService = Depends(get_user_profile_service),
) -> dict[str, Any]:
    try:
        user_profile = await service.get_user_profile(user_id, caller)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed to view this user's profile")

    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")

    return service.build_response(user_profile)
