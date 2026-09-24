from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from core.config.database import get_database
from users.schemas import UserCreate, UserUpdate
from users.user_repository import UserRepository
from users.user_service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_user_service(request: Request) -> UserService:
    db = get_database(request)
    return UserService(UserRepository(db))


@router.get("")
async def get_users(
    service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    users = await service.get_users()
    return service.build_response("users", users)


@router.get("/search")
async def search_users(
    q: Optional[str] = None,
    service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    """Search users by name or email (`?q=`); no `q` returns everyone."""
    users = await service.search_users(q)
    return service.build_response("users", users)


@router.get("/template")
async def get_user_template(
    service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    return service.build_template_response()


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    user = await service.get_user(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return service.build_response("user", user)


@router.post("", status_code=201)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    created = await service.create_user(user)
    return service.build_response("user", created)


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    user: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    updated = await service.update_user(user_id, user)

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return service.build_response("user", updated)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
) -> Response:
    deleted = await service.delete_user(user_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return Response(status_code=204)