from typing import Any, Optional

from fastapi import APIRouter, Depends, Request, Response

from database import get_database
from group_permissions import Caller
from media_providers import MediaProviders
from models import MediaRef, PostCreate, PostUpdate
from repositories.post_repository import PostRepository
from repositories.post_stats_repository import PostStatsRepository
from repositories.reaction_repository import ReactionRepository
from routers.deps import get_caller, get_media_providers
from routers.groups import get_group_service
from services.post_service import DEFAULT_LIMIT, PostService

# Nested under the group on purpose: every request re-checks the group's
# visibility, so a private group's post can't be reached any other way.
# Comments are their own API: routers/post_comments.py.
router = APIRouter(prefix="/groups/{group_id}/posts", tags=["posts"])


def get_post_service(
    request: Request, media: Optional[MediaProviders] = Depends(get_media_providers)
) -> PostService:
    """Comments and the timeline reuse this with media=None: they only read posts."""
    db = get_database(request)
    return PostService(
        PostRepository(db), PostStatsRepository(db), ReactionRepository(db), get_group_service(request), media
    )


@router.get("")
async def list_posts(
    group_id: str,
    limit: int = DEFAULT_LIMIT,
    caller: Caller = Depends(get_caller),
    service: PostService = Depends(get_post_service),
) -> dict[str, Any]:
    """The group's posts, newest first."""
    access, rows = await service.list_posts(caller, group_id, limit)
    return service.build_posts_response(caller, access, rows)


@router.post("", status_code=201)
async def create_post(
    group_id: str,
    payload: PostCreate,
    caller: Caller = Depends(get_caller),
    service: PostService = Depends(get_post_service),
) -> dict[str, Any]:
    access, row = await service.create_post(caller, group_id, payload)
    return service.build_post_response(caller, access, row)


@router.get("/{post_id}")
async def get_post(
    group_id: str,
    post_id: str,
    caller: Caller = Depends(get_caller),
    service: PostService = Depends(get_post_service),
) -> dict[str, Any]:
    access, row = await service.get_post(caller, group_id, post_id)
    return service.build_post_response(caller, access, row)


@router.put("/{post_id}")
async def update_post(
    group_id: str,
    post_id: str,
    payload: PostUpdate,
    caller: Caller = Depends(get_caller),
    service: PostService = Depends(get_post_service),
) -> dict[str, Any]:
    access, row = await service.update_post(caller, group_id, post_id, payload)
    return service.build_post_response(caller, access, row)


@router.delete("/{post_id}", status_code=204)
async def delete_post(
    group_id: str,
    post_id: str,
    caller: Caller = Depends(get_caller),
    service: PostService = Depends(get_post_service),
) -> Response:
    await service.delete_post(caller, group_id, post_id)
    return Response(status_code=204)


@router.put("/{post_id}/media")
async def set_post_media(
    group_id: str,
    post_id: str,
    payload: MediaRef,
    caller: Caller = Depends(get_caller),
    service: PostService = Depends(get_post_service),
) -> dict[str, Any]:
    """Attach an Unsplash photo, Giphy GIF or YouTube video (author only)."""
    access, row = await service.set_media(caller, group_id, post_id, payload)
    return service.build_post_response(caller, access, row)


@router.delete("/{post_id}/media")
async def remove_post_media(
    group_id: str,
    post_id: str,
    caller: Caller = Depends(get_caller),
    service: PostService = Depends(get_post_service),
) -> dict[str, Any]:
    access, row = await service.remove_media(caller, group_id, post_id)
    return service.build_post_response(caller, access, row)


@router.put("/{post_id}/like")
async def like_post(
    group_id: str,
    post_id: str,
    caller: Caller = Depends(get_caller),
    service: PostService = Depends(get_post_service),
) -> dict[str, Any]:
    access, row = await service.like(caller, group_id, post_id)
    return service.build_post_response(caller, access, row)


@router.delete("/{post_id}/like")
async def unlike_post(
    group_id: str,
    post_id: str,
    caller: Caller = Depends(get_caller),
    service: PostService = Depends(get_post_service),
) -> dict[str, Any]:
    access, row = await service.unlike(caller, group_id, post_id)
    return service.build_post_response(caller, access, row)
