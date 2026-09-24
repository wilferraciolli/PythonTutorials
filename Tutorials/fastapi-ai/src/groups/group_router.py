from typing import Any, Optional

from fastapi import APIRouter, Depends, Request, Response

from core.config.database import get_database
from groups.group_permissions import Caller
from groups.schemas import GroupCreate, GroupOwnerUpdate, GroupUpdate
from groups.group_repository import GroupRepository
from users.user_repository import UserRepository
from users.dependencies import get_caller
from groups.group_service import GroupService

# Groups are shared, not one person's data, so they are not under /users/{id}.
# The caller is always the token's user (get_caller).
router = APIRouter(prefix="/groups", tags=["groups"])


def get_group_service(request: Request) -> GroupService:
    db = get_database(request)
    return GroupService(GroupRepository(db), UserRepository(db))


@router.get("")
async def list_groups(
    q: Optional[str] = None,
    following: bool = False,
    mine: bool = False,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> dict[str, Any]:
    """Groups you can see (admins: all). `q` searches name/description; `following`/`mine` narrow it."""
    return service.build_list_response(caller, await service.list_groups(caller, q, following, mine))


@router.post("", status_code=201)
async def create_group(
    payload: GroupCreate,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> dict[str, Any]:
    """Create a group; you become its owner, a member and a follower."""
    return service.build_response(caller, await service.create_group(caller, payload))


@router.get("/{group_id}")
async def get_group(
    group_id: str,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> dict[str, Any]:
    return service.build_response(caller, await service.get_visible(caller, group_id))


@router.put("/{group_id}")
async def update_group(
    group_id: str,
    payload: GroupUpdate,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> dict[str, Any]:
    return service.build_response(caller, await service.update_group(caller, group_id, payload))


@router.delete("/{group_id}", status_code=204)
async def delete_group(
    group_id: str,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> Response:
    await service.delete_group(caller, group_id)
    return Response(status_code=204)


@router.put("/{group_id}/owner")
async def assign_owner(
    group_id: str,
    payload: GroupOwnerUpdate,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> dict[str, Any]:
    return service.build_response(caller, await service.assign_owner(caller, group_id, payload.userId))


# --- members ("me" routes first so they aren't read as a user id)


@router.get("/{group_id}/members")
async def list_members(
    group_id: str,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> dict[str, Any]:
    access, rows = await service.list_members(caller, group_id)
    return service.build_members_response(caller, access, rows)


@router.put("/{group_id}/members/me")
async def join_group(
    group_id: str,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> dict[str, Any]:
    return service.build_response(caller, await service.join(caller, group_id))


@router.delete("/{group_id}/members/me", status_code=204)
async def leave_group(
    group_id: str,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> Response:
    await service.remove_member(caller, group_id, caller.id)
    return Response(status_code=204)


@router.put("/{group_id}/members/{user_id}")
async def add_member(
    group_id: str,
    user_id: str,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> dict[str, Any]:
    return service.build_response(caller, await service.add_member(caller, group_id, user_id))


@router.delete("/{group_id}/members/{user_id}", status_code=204)
async def remove_member(
    group_id: str,
    user_id: str,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> Response:
    await service.remove_member(caller, group_id, user_id)
    return Response(status_code=204)


# --- followers


@router.get("/{group_id}/followers")
async def list_followers(
    group_id: str,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> dict[str, Any]:
    _, rows = await service.list_followers(caller, group_id)
    return service.build_followers_response(rows)


@router.put("/{group_id}/followers/me")
async def follow_group(
    group_id: str,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> dict[str, Any]:
    return service.build_response(caller, await service.follow(caller, group_id))


@router.delete("/{group_id}/followers/me")
async def unfollow_group(
    group_id: str,
    caller: Caller = Depends(get_caller),
    service: GroupService = Depends(get_group_service),
) -> dict[str, Any]:
    return service.build_response(caller, await service.unfollow(caller, group_id))
