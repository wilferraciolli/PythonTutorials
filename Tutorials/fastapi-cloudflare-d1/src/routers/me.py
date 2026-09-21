from typing import Any

from fastapi import APIRouter, Depends

from auth import AuthenticatedUser, get_authenticated_user
from services.me_service import MeService

router = APIRouter(prefix="/me", tags=["me"])


def get_me_service() -> MeService:
    return MeService()


@router.get("")
async def get_me(
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
    service: MeService = Depends(get_me_service),
) -> dict[str, Any]:
    return service.build_response(current_user)
