from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from models import Tag, TagCreate
from repositories.tag_repository import TagRepository
from services.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])


def get_tag_service(request: Request) -> TagService:
    """
    Build a Service per-request.

    Unlike SQLAlchemy's global `engine`, the D1 binding (`env.DB`) only exists
    on the incoming request's `scope["env"]` - Cloudflare injects it per call,
    so it cannot be created once at startup like our old `Depends(get_db)`.
    """
    env = request.scope["env"]
    return TagService(TagRepository(env.DB))


@router.get("/search")
async def search_tags(
        tag: Optional[str] = None,
        service: TagService = Depends(get_tag_service)
) -> List[Tag]:
    return await service.search_tags(tag)

@router.post("")
async def create_tag(
        tag: TagCreate,
        service: TagService = Depends(get_tag_service)
) -> Tag:
    return await service.create_tag(tag)

@router.get("")
async def get_all_tags(
        service: TagService = Depends(get_tag_service)
) -> List[Tag]:
    return await service.get_all_tags()

@router.get("/{resource_id}")
async def get_all_tags_for_resource(
        resource_id: int,
        service: TagService = Depends(get_tag_service)
) -> List[Tag]:
    return await service.get_all_tags_for_resource(resource_id)


@router.get("/{id}")
async def get_tag(
        id: int,
        service: TagService = Depends(get_tag_service)
) -> Tag:
    tag = await service.get_tag(id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    return tag

@router.delete("/{id}")
async def delete_tag(
        id: int,
        service: TagService = Depends(get_tag_service)
) -> None:
    return await service.delete_tag(id)
