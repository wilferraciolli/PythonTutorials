from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from core.config.database import get_database
from core.security.authorization import Caller, get_caller, require_admin
from users.exceptions import SelfLockoutError
from users.schemas import (
    UserCreateRequest,
    UserListResponse,
    UserResponse,
    UserTemplateResponse,
    UserUpdateRequest,
)
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
    caller: Caller = Depends(get_caller),
    service: UserService = Depends(get_user_service),
) -> UserListResponse:
    users = await service.get_users(caller)
    return service.build_list_response(users, caller)


@router.get("/search")
async def search_users(
    q: Optional[str] = None,
    caller: Caller = Depends(get_caller),
    service: UserService = Depends(get_user_service),
) -> UserListResponse:
    """Search users by name or email (`?q=`); no `q` returns everyone."""
    users = await service.search_users(q, caller)
    return service.build_list_response(users, caller)


@router.get("/template")
async def get_user_template(
    service: UserService = Depends(get_user_service),
) -> UserTemplateResponse:
    return service.build_template_response()


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    caller: Caller = Depends(get_caller),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    user = await service.get_user(user_id, caller)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return service.build_response(user, caller)


@router.post("", status_code=201)
async def create_user(
    request: UserCreateRequest,
    caller: Caller = Depends(require_admin),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    created = await service.create_user(request, caller)
    return service.build_response(created, caller)


@router.put("/{user_id}")
async def update_user(
    user_id: str,
    request: UserUpdateRequest,
    caller: Caller = Depends(require_admin),
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    try:
        updated = await service.update_user(user_id, request, caller)
    except SelfLockoutError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return service.build_response(updated, caller)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    caller: Caller = Depends(require_admin),
    service: UserService = Depends(get_user_service),
) -> Response:
    try:
        deleted = await service.delete_user(user_id, caller)
    except SelfLockoutError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

    return Response(status_code=204)
