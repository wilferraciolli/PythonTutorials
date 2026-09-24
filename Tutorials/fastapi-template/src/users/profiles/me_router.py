from typing import Any

from fastapi import APIRouter, Depends, Request

from core.security.auth import AuthenticatedUser, get_authenticated_user
from core.config.database import get_database
from users.user_repository import UserRepository
from users.profiles.me_service import MeService

router = APIRouter(prefix="/me", tags=["me"])


def get_me_service(request: Request) -> MeService:
    db = get_database(request)
    return MeService(UserRepository(db))


@router.get("")
async def get_me(
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
    service: MeService = Depends(get_me_service),
) -> dict[str, Any]:
    user_row = await service.get_or_create_current_user(current_user)
    return service.build_response(user_row)
