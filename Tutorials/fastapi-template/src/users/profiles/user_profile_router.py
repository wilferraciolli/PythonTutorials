from fastapi import APIRouter, Depends, HTTPException, Request

from core.config.database import get_database
from core.security.authorization import Caller, get_caller
from users.profiles.schemas import UserProfileResponse
from users.profiles.user_profile_service import UserProfileService
from users.user_repository import UserRepository

router = APIRouter(prefix="/users", tags=["userprofiles"])


def get_user_profile_service(request: Request) -> UserProfileService:
    db = get_database(request)
    return UserProfileService(UserRepository(db))


@router.get("/{user_id}/profile")
async def get_user_profile(
    user_id: str,
    caller: Caller = Depends(get_caller),
    service: UserProfileService = Depends(get_user_profile_service),
) -> UserProfileResponse:
    try:
        user_profile = await service.get_user_profile(user_id, caller)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not allowed to view this user's profile")

    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")

    return service.build_response(user_profile)
