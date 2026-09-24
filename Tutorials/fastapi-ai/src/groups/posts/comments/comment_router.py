from typing import Optional

from fastapi import APIRouter, Depends, Request, Response

from core.config.database import get_database
from core.security.authorization import Caller, get_caller
from groups.posts.comments.comment_repository import CommentRepository
from groups.posts.comments.comment_service import CommentService
from groups.posts.comments.schemas import (
    CommentCreateRequest,
    CommentListResponse,
    CommentResponse,
    CommentUpdateRequest,
)
from groups.posts.post_router import get_post_search_service, get_post_service
from groups.posts.post_search_service import PostSearchService
from groups.posts.post_stats_repository import PostStatsRepository
from groups.posts.reaction_repository import ReactionRepository

# Under the post (and the post under its group), so the group's visibility is
# checked on every comment request too.
router = APIRouter(prefix="/groups/{group_id}/posts/{post_id}/comments", tags=["post comments"])


def get_comment_service(
    request: Request, search: Optional[PostSearchService] = Depends(get_post_search_service)
) -> CommentService:
    db = get_database(request)
    return CommentService(
        CommentRepository(db),
        PostStatsRepository(db),
        ReactionRepository(db),
        get_post_service(request, media=None, search=search),
    )


@router.get("")
async def list_comments(
    group_id: str,
    post_id: str,
    caller: Caller = Depends(get_caller),
    service: CommentService = Depends(get_comment_service),
) -> CommentListResponse:
    """All comments, oldest first; replies carry `parentCommentId`."""
    access, post, comments = await service.list_comments(caller, group_id, post_id)
    return service.build_comments_response(caller, access, post, comments)


@router.post("", status_code=201)
async def create_comment(
    group_id: str,
    post_id: str,
    request: CommentCreateRequest,
    caller: Caller = Depends(get_caller),
    service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    """Comment on the post, or reply to a comment by sending `parentCommentId`."""
    access, post, comment = await service.create_comment(caller, group_id, post_id, request)
    return service.build_comment_response(caller, access, post, comment)


@router.put("/{comment_id}")
async def update_comment(
    group_id: str,
    post_id: str,
    comment_id: str,
    request: CommentUpdateRequest,
    caller: Caller = Depends(get_caller),
    service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    access, post, comment = await service.update_comment(caller, group_id, post_id, comment_id, request)
    return service.build_comment_response(caller, access, post, comment)


@router.delete("/{comment_id}", status_code=204)
async def delete_comment(
    group_id: str,
    post_id: str,
    comment_id: str,
    caller: Caller = Depends(get_caller),
    service: CommentService = Depends(get_comment_service),
) -> Response:
    await service.delete_comment(caller, group_id, post_id, comment_id)
    return Response(status_code=204)


@router.put("/{comment_id}/like")
async def like_comment(
    group_id: str,
    post_id: str,
    comment_id: str,
    caller: Caller = Depends(get_caller),
    service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    access, post, comment = await service.like(caller, group_id, post_id, comment_id)
    return service.build_comment_response(caller, access, post, comment)


@router.delete("/{comment_id}/like")
async def unlike_comment(
    group_id: str,
    post_id: str,
    comment_id: str,
    caller: Caller = Depends(get_caller),
    service: CommentService = Depends(get_comment_service),
) -> CommentResponse:
    access, post, comment = await service.unlike(caller, group_id, post_id, comment_id)
    return service.build_comment_response(caller, access, post, comment)
