from fastapi import APIRouter, Depends, Request

from core.config.database import get_database
from shared.settings.region.region_settings_repository import RegionSettingsRepository
from shared.settings.region.schemas import SystemSettingsResponse, SystemSettingsUpdateRequest
from shared.settings.region.system_settings_service import SystemSettingsService

router = APIRouter(prefix="/admin/settings", tags=["system settings"])


def get_system_settings_service(request: Request) -> SystemSettingsService:
    db = get_database(request)
    return SystemSettingsService(RegionSettingsRepository(db))


@router.get("")
async def get_system_settings(
        service: SystemSettingsService = Depends(get_system_settings_service),
) -> SystemSettingsResponse:
    system_settings = await service.get_system_settings()
    return service.build_response(system_settings)


@router.put("")
async def update_system_settings(
        request: SystemSettingsUpdateRequest,
        service: SystemSettingsService = Depends(get_system_settings_service),
) -> SystemSettingsResponse:
    system_settings = await service.update_system_settings(request)
    return service.build_response(system_settings)
