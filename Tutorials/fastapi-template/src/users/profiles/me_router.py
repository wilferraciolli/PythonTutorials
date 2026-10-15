from fastapi import APIRouter, Depends, Request
from wiltech_labs_auth import AuthenticatedUser, get_authenticated_user
from wiltech_labs_core import get_database

from users.profiles.me_service import MeService
from users.profiles.schemas import MeResponse
from users.user_repository import UserRepository

router = APIRouter(prefix="/me", tags=["me"])


def get_me_service(request: Request) -> MeService:
    db = get_database(request)
    return MeService(UserRepository(db))


@router.get("")
async def get_me(
    current_user: AuthenticatedUser = Depends(get_authenticated_user),
    service: MeService = Depends(get_me_service),
) -> MeResponse:
    me = await service.get_me(current_user)
    return service.build_response(me)
