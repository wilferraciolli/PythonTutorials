from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request

from database import get_database
from repositories.user_repository import UserRepository
from services.user_profile_service import UserProfileService

router = APIRouter(prefix="/users", tags=["userprofiles"])


def get_user_profile_service(request: Request) -> UserProfileService:
    db = get_database(request)
    return UserProfileService(UserRepository(db))


@router.get("/{user_id}/profile")
async def get_user_profile(
    user_id: str,
    service: UserProfileService = Depends(get_user_profile_service),
) -> dict[str, Any]:
    user_profile = await service.get_user_profile(user_id)

    if not user_profile:
        raise HTTPException(status_code=404, detail="User not found")

    return service.build_response(user_profile)
