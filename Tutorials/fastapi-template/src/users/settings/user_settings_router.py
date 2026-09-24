from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from core.config.database import get_database
from users.schemas import UserUpdate
from users.user_repository import UserRepository
from users.user_service import UserService

router = APIRouter(prefix="/users/{id}/settings", tags=["user settings"])


def get_user_service(request: Request) -> UserService:
    db = get_database(request)
    return UserService(UserRepository(db))


@router.get("")
async def get_user_setting(
        user_id: str,
        service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    users = await service.get_users()
    return service.build_response("users", users)


@router.put("")
async def update_user_setting(
        user_id: str,
        user: UserUpdate,
        service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    updated = await service.update_user(user_id, user)

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return service.build_response("user", updated)
