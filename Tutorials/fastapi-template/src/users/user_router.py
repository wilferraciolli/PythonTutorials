from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from core.config.database import get_database
from core.security.auth import AuthenticatedUser
from core.security.authorization import require_admin
from users.exceptions import SelfLockoutError
from users.schemas import UserCreate, UserUpdate
from users.user_repository import UserRepository
from users.user_service import UserService

# Reads are open to any signed-in user (main.py adds get_authenticated_user);
# writes additionally require the ADMIN role, since they can change roles.
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


@router.post("", status_code=201, dependencies=[Depends(require_admin)])
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
    current_user: AuthenticatedUser = Depends(require_admin),
    service: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    try:
        updated = await service.update_user(user_id, user, current_user.id)
    except SelfLockoutError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return service.build_response("user", updated)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    current_user: AuthenticatedUser = Depends(require_admin),
    service: UserService = Depends(get_user_service),
) -> Response:
    try:
        deleted = await service.delete_user(user_id, current_user.id)
    except SelfLockoutError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return Response(status_code=204)