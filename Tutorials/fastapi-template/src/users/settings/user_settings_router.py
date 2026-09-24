from fastapi import APIRouter, Depends, HTTPException, Request, Response

from core.config.database import get_database
from shared.settings.region.region_settings_repository import RegionSettingsRepository
from users.settings.schemas import UserSettingsResponse, UserSettingsUpdateRequest
from users.settings.user_settings_service import UserSettingsService
from users.user_repository import UserRepository

router = APIRouter(prefix="/users/{user_id}/settings", tags=["user settings"])


def get_user_settings_service(request: Request) -> UserSettingsService:
    db = get_database(request)
    return UserSettingsService(UserRepository(db), RegionSettingsRepository(db))


@router.get("")
async def get_user_settings(
        user_id: str,
        service: UserSettingsService = Depends(get_user_settings_service),
) -> UserSettingsResponse:
    user_settings = await service.get_user_settings(user_id)

    if not user_settings:
        raise HTTPException(status_code=404, detail="User not found")

    return service.build_response(user_settings)


@router.put("")
async def update_user_settings(
        user_id: str,
        request: UserSettingsUpdateRequest,
        service: UserSettingsService = Depends(get_user_settings_service),
) -> UserSettingsResponse:
    user_settings = await service.update_user_settings(user_id, request)

    if not user_settings:
        raise HTTPException(status_code=404, detail="User not found")

    return service.build_response(user_settings)


@router.delete("", status_code=204)
async def reset_user_settings(
        user_id: str,
        service: UserSettingsService = Depends(get_user_settings_service),
) -> Response:
    """Drop the user's own settings so they fall back to the system defaults."""
    if not await service.reset_user_settings(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    return Response(status_code=204)
