from typing import Any, Optional

from fastapi import APIRouter, Depends, Request, Response

from core.config.database import get_database
from groups.group_permissions import Caller
from media.media_providers import MediaProviders
from groups.posts.schemas import PostCreate, PostUpdate
from media.schemas import MediaRef
from groups.posts.post_repository import PostRepository
from groups.posts.post_stats_repository import PostStatsRepository
from groups.posts.reaction_repository import ReactionRepository
from core.ai.embeddings import get_embedder
from media.media_router import get_media_providers
from users.dependencies import get_caller
from groups.group_router import get_group_service
from groups.posts.post_search_service import PostSearchService
from groups.posts.post_service import DEFAULT_LIMIT, PostService

# Nested under the group on purpose: every request re-checks the group's
# visibility, so a private group's post can't be reached any other way.
# Comments are their own API: routers/post_comments.py.
router = APIRouter(prefix="/groups/{group_id}/posts", tags=["posts"])


def get_post_search_service(request: Request) -> PostSearchService:
    """Post and comment search (embeddings via Workers AI, built lazily like the todo search)."""
    embed_texts, model = get_embedder(request)
    return PostSearchService(get_database(request), embed_texts, model)


def get_post_service(
    request: Request,
    media: Optional[MediaProviders] = Depends(get_media_providers),
    search: Optional[PostSearchService] = Depends(get_post_search_service),
) -> PostService:
    """The timeline reuses this with media=None, search=None: it only reads posts."""
    db = get_database(request)
    return PostService(
        PostRepository(db),
        PostStatsRepository(db),
        ReactionRepository(db),
        get_group_service(request),
        media,
        search,
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
