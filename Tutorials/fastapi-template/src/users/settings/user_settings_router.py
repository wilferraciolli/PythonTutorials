from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from core.config.database import get_database
from shared.settings.region.region_settings_repository import RegionSettingsRepository
from shared.settings.region.schemas import RegionSettingPayload
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
) -> dict[str, Any]:
    settings = await service.get_region_settings(user_id)

    if not settings:
        raise HTTPException(status_code=404, detail="User not found")

    return service.build_response(settings)


@router.put("")
async def update_user_settings(
    user_id: str,
    payload: RegionSettingPayload,
    service: UserSettingsService = Depends(get_user_settings_service),
) -> dict[str, Any]:
    settings = await service.update_region_settings(user_id, payload)

    if not settings:
        raise HTTPException(status_code=404, detail="User not found")

    return service.build_response(settings)


@router.delete("", status_code=204)
async def reset_user_settings(
    user_id: str,
    service: UserSettingsService = Depends(get_user_settings_service),
) -> Response:
    """Drop the user's own settings so they fall back to the system defaults."""
    if not await service.reset_region_settings(user_id):
        raise HTTPException(status_code=404, detail="User not found")

    return Response(status_code=204)
