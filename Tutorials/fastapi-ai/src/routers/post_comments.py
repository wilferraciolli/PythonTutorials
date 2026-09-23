from typing import Any

from fastapi import APIRouter, Depends, Request, Response

from database import get_database
from group_permissions import Caller
from models import CommentCreate, CommentUpdate
from repositories.post_comment_repository import PostCommentRepository
from repositories.post_stats_repository import PostStatsRepository
from repositories.reaction_repository import ReactionRepository
from routers.deps import get_caller
from routers.posts import get_post_service
from services.post_comment_service import PostCommentService

# Under the post (and the post under its group), so the group's visibility is
# checked on every comment request too.
router = APIRouter(prefix="/groups/{group_id}/posts/{post_id}/comments", tags=["post comments"])


def get_post_comment_service(request: Request) -> PostCommentService:
    db = get_database(request)
    return PostCommentService(
        PostCommentRepository(db), PostStatsRepository(db), ReactionRepository(db), get_post_service(request)
    )


@router.get("")
async def list_comments(
    group_id: str,
    post_id: str,
    caller: Caller = Depends(get_caller),
    service: PostCommentService = Depends(get_post_comment_service),
) -> dict[str, Any]:
    """All comments, oldest first; replies carry `parentCommentId`."""
    access, post, rows = await service.list_comments(caller, group_id, post_id)
    return service.build_comments_response(caller, access, post, rows)


@router.post("", status_code=201)
async def create_comment(
    group_id: str,
    post_id: str,
    payload: CommentCreate,
    caller: Caller = Depends(get_caller),
    service: PostCommentService = Depends(get_post_comment_service),
) -> dict[str, Any]:
    """Comment on the post, or reply to a comment by sending `parentCommentId`."""
    access, post, row = await service.create_comment(caller, group_id, post_id, payload)
    return service.build_comment_response(caller, access, post, row)


@router.put("/{comment_id}")
async def update_comment(
    group_id: str,
    post_id: str,
    comment_id: str,
    payload: CommentUpdate,
    caller: Caller = Depends(get_caller),
    service: PostCommentService = Depends(get_post_comment_service),
) -> dict[str, Any]:
    access, post, row = await service.update_comment(caller, group_id, post_id, comment_id, payload)
    return service.build_comment_response(caller, access, post, row)


@router.delete("/{comment_id}", status_code=204)
async def delete_comment(
    group_id: str,
    post_id: str,
    comment_id: str,
    caller: Caller = Depends(get_caller),
    service: PostCommentService = Depends(get_post_comment_service),
) -> Response:
    await service.delete_comment(caller, group_id, post_id, comment_id)
    return Response(status_code=204)


@router.put("/{comment_id}/like")
async def like_comment(
    group_id: str,
    post_id: str,
    comment_id: str,
    caller: Caller = Depends(get_caller),
    service: PostCommentService = Depends(get_post_comment_service),
) -> dict[str, Any]:
    access, post, row = await service.like(caller, group_id, post_id, comment_id)
    return service.build_comment_response(caller, access, post, row)


@router.delete("/{comment_id}/like")
async def unlike_comment(
    group_id: str,
    post_id: str,
    comment_id: str,
    caller: Caller = Depends(get_caller),
    service: PostCommentService = Depends(get_post_comment_service),
) -> dict[str, Any]:
    access, post, row = await service.unlike(caller, group_id, post_id, comment_id)
    return service.build_comment_response(caller, access, post, row)
