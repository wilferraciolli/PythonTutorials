from typing import Any, Dict, Optional

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
) -> Dict[str, Any]:
    tags = await service.search_tags(tag)
    return service.build_response("tags", tags)

@router.post("", status_code=201)
async def create_tag(
        tag: TagCreate,
        service: TagService = Depends(get_tag_service)
) -> Dict[str, Any]:
    created = await service.create_tag(tag)
    return service.build_response("tag", created)

@router.get("", status_code=200)
async def get_all_tags(
        resource_id: Optional[str] = None,
        service: TagService = Depends(get_tag_service)
) -> Dict[str, Any]:
    tags = await service.get_all_tags(resource_id)
    return service.build_response("tags", tags)

@router.get("/{id}", status_code=200)
async def get_tag(
        id: str,
        service: TagService = Depends(get_tag_service)
) -> Dict[str, Any]:
    tag = await service.get_tag(id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    return service.build_response("tag", tag)

@router.delete("/{id}", status_code=204)
async def delete_tag(
        id: str,
        service: TagService = Depends(get_tag_service)
) -> None:
    success = await service.delete_tag(id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
