from typing import Any

from fastapi import APIRouter, Depends

from services.user_profile_service import UserProfileService

router = APIRouter(prefix="/userprofiles", tags=["userprofiles"])


def get_user_profile_service() -> UserProfileService:
    return UserProfileService()


@router.get("")
async def get_user_profile(
    service: UserProfileService = Depends(get_user_profile_service),
) -> dict[str, Any]:
    return service.build_response()
