from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from core.config.database import get_database
from tags.schemas import TagCreateRequest, TagListResponse, TagResponse, TagTemplateResponse
from tags.tag_repository import TagRepository
from tags.tag_service import TagService

router = APIRouter(prefix="/tags", tags=["tags"])


def get_tag_service(request: Request) -> TagService:
    return TagService(TagRepository(get_database(request)))


@router.get("/search")
async def search_tags(
    tag: Optional[str] = None,
    service: TagService = Depends(get_tag_service),
) -> TagListResponse:
    return service.build_list_response(await service.search_tags(tag))


@router.get("/template")
async def get_tag_template(service: TagService = Depends(get_tag_service)) -> TagTemplateResponse:
    return service.build_template_response()


@router.post("", status_code=201)
async def create_tag(
    request: TagCreateRequest,
    service: TagService = Depends(get_tag_service),
) -> TagResponse:
    return service.build_response(await service.create_tag(request))


@router.get("")
async def get_all_tags(
    resource_id: Optional[str] = None,
    service: TagService = Depends(get_tag_service),
) -> TagListResponse:
    return service.build_list_response(await service.get_all_tags(resource_id))


@router.get("/{tag_id}")
async def get_tag(
    tag_id: str,
    service: TagService = Depends(get_tag_service),
) -> TagResponse:
    tag = await service.get_tag(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return service.build_response(tag)


@router.delete("/{tag_id}", status_code=204)
async def delete_tag(
    tag_id: str,
    service: TagService = Depends(get_tag_service),
) -> Response:
    if not await service.delete_tag(tag_id):
        raise HTTPException(status_code=404, detail="Tag not found")
    return Response(status_code=204)
