from typing import Optional

from fastapi import APIRouter, Depends, Request

from admin.admin_service import AdminService
from admin.schemas import AdminResponse, PostSearchReindexResponse, PostStatsRebuildResponse
from core.config.database import get_database
from core.security.authorization import require_admin
from groups.posts.post_router import get_post_search_service
from groups.posts.post_search_service import PostSearchService
from groups.posts.post_stats_repository import PostStatsRepository

# Admins only: every route requires the ADMIN role (saved roles, not the token).
router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


def get_admin_service(
    request: Request,
    search: Optional[PostSearchService] = Depends(get_post_search_service),
) -> AdminService:
    return AdminService(PostStatsRepository(get_database(request)), search)


@router.get("")
async def admin_area(service: AdminService = Depends(get_admin_service)) -> AdminResponse:
    """The admin hub: what an admin can do, as links."""
    return service.build_admin_response(service.get_admin())


@router.post("/post-stats/rebuild")
async def rebuild_post_stats(service: AdminService = Depends(get_admin_service)) -> PostStatsRebuildResponse:
    """Recompute every post's likes, comments and score from the source tables."""
    return service.build_post_stats_response(await service.rebuild_post_stats())


@router.post("/post-search/reindex")
async def reindex_post_search(service: AdminService = Depends(get_admin_service)) -> PostSearchReindexResponse:
    """Backfill search vectors for posts and comments that have none."""
    return service.build_reindex_response(await service.reindex_post_search())
