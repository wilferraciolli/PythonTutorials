from fastapi import APIRouter, Depends, HTTPException, Request, Response

from core.config.database import get_database
from core.security.authorization import Caller, get_caller
from shared.settings.region.region_settings_repository import RegionSettingsRepository
from users.exceptions import NotOwnerError
from users.settings.schemas import UserSettingsResponse, UserSettingsUpdateRequest
from users.settings.user_settings_service import UserSettingsService

# Personal resource: only the user in the path may use it (403 otherwise).
router = APIRouter(prefix="/users/{user_id}/settings", tags=["user settings"])


def get_user_settings_service(request: Request) -> UserSettingsService:
    db = get_database(request)
    return UserSettingsService(RegionSettingsRepository(db))


@router.get("")
async def get_user_settings(
        user_id: str,
        caller: Caller = Depends(get_caller),
        service: UserSettingsService = Depends(get_user_settings_service),
) -> UserSettingsResponse:
    try:
        user_settings = await service.get_user_settings(user_id, caller)
    except NotOwnerError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return service.build_response(user_settings)


@router.put("")
async def update_user_settings(
        user_id: str,
        request: UserSettingsUpdateRequest,
        caller: Caller = Depends(get_caller),
        service: UserSettingsService = Depends(get_user_settings_service),
) -> UserSettingsResponse:
    try:
        user_settings = await service.update_user_settings(user_id, request, caller)
    except NotOwnerError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return service.build_response(user_settings)


@router.delete("", status_code=204)
async def reset_user_settings(
        user_id: str,
        caller: Caller = Depends(get_caller),
        service: UserSettingsService = Depends(get_user_settings_service),
) -> Response:
    """Drop the user's own settings so they fall back to the system defaults."""
    try:
        await service.reset_user_settings(user_id, caller)
    except NotOwnerError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    return Response(status_code=204)
