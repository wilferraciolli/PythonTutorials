from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from core.config.database import get_database
from tags.schemas import Tag, TagCreate
from tags.tag_repository import TagRepository
from tags.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])


def get_tag_service(request: Request) -> TagService:
    """
    Build a TagService per-request using the configured database adapter.

    The app can run against local SQLite, Cloudflare D1 binding, or D1 HTTP
    without repositories/services depending on a concrete database runtime.
    """
    return TagService(TagRepository(get_database(request)))


@router.get("/search")
async def search_tags(
        tag: Optional[str] = None,
        service: TagService = Depends(get_tag_service)
) -> Dict[str, Any]:
    tags = await service.search_tags(tag)
    return service.build_response("tags", tags)

@router.get("/template", status_code=200)
async def get_tag_template(service: TagService = Depends(get_tag_service)) -> Dict[str, Any]:
    """Get a Tag template"""
    return service.build_template_response()

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
