from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Response

from core.ai.embeddings import get_embedder
from core.ai.resource_vector_store import ResourceVectorStore
from core.config.database import get_database
from core.security.authorization import require_owner
from tags.tag_repository import TagRepository
from tags.tag_service import TagService
from todos.enums import TodoState
from todos.schemas import (
    TodoCreateRequest,
    TodoListResponse,
    TodoReindexResponse,
    TodoResponse,
    TodoSearchResponse,
    TodoTemplateResponse,
    TodoUpdateRequest,
)
from todos.todo_repository import TodoRepository
from todos.todo_search_service import DEFAULT_LIMIT, TodoSearchService
from todos.todo_service import TodoService

# Personal resource: only the user in the path may use it (require_owner, 403).
router = APIRouter(prefix="/users/{user_id}/todos", tags=["todos"], dependencies=[Depends(require_owner)])


def get_todo_search_service(request: Request) -> TodoSearchService:
    db = get_database(request)
    embed_texts, model = get_embedder(request)
    return TodoSearchService(TodoRepository(db), ResourceVectorStore(db, "todo"), embed_texts, model)


def get_todo_service(request: Request) -> TodoService:
    db = get_database(request)
    return TodoService(TodoRepository(db), TagService(TagRepository(db)), get_todo_search_service(request))


@router.get("/search")
async def search_todos(
    user_id: str,
    q: str,
    state: Optional[TodoState] = None,
    limit: int = DEFAULT_LIMIT,
    search: TodoSearchService = Depends(get_todo_search_service),
    service: TodoService = Depends(get_todo_service),
) -> TodoSearchResponse:
    """Find todos by meaning (embeddings) and keyword, best first."""
    hits = await search.search(user_id, q, state, limit)
    return service.build_search_response(user_id, hits)


@router.post("/search/reindex")
async def reindex_todos(
    user_id: str,
    search: TodoSearchService = Depends(get_todo_search_service),
    service: TodoService = Depends(get_todo_service),
) -> TodoReindexResponse:
    """Backfill: embed this user's todos that aren't indexed yet."""
    return service.build_reindex_response(user_id, await search.reindex_user(user_id))


@router.get("/template")
async def get_todo_template(
    user_id: str,
    service: TodoService = Depends(get_todo_service),
) -> TodoTemplateResponse:
    """The shape a new todo is POSTed in, with defaults."""
    return service.build_template_response(user_id)


@router.post("", status_code=201)
async def create_todo(
    user_id: str,
    request: TodoCreateRequest,
    service: TodoService = Depends(get_todo_service),
) -> TodoResponse:
    return service.build_response(await service.create_todo(user_id, request))


@router.get("")
async def get_all_todos(
    user_id: str,
    state: Optional[TodoState] = None,
    service: TodoService = Depends(get_todo_service),
) -> TodoListResponse:
    """All the user's todos, optionally filtered by state."""
    return service.build_list_response(user_id, await service.get_all_todos(user_id, state=state))


@router.get("/{todo_id}")
async def get_todo(
    user_id: str,
    todo_id: str,
    service: TodoService = Depends(get_todo_service),
) -> TodoResponse:
    todo = await service.get_todo(user_id, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return service.build_response(todo)


@router.put("/{todo_id}")
async def update_todo(
    user_id: str,
    todo_id: str,
    request: TodoUpdateRequest,
    service: TodoService = Depends(get_todo_service),
) -> TodoResponse:
    """Partial update: only the fields sent are changed."""
    todo = await service.update_todo(user_id, todo_id, request)
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return service.build_response(todo)


@router.patch("/{todo_id}/state/{new_state}")
async def update_todo_state(
    user_id: str,
    todo_id: str,
    new_state: TodoState,
    service: TodoService = Depends(get_todo_service),
) -> TodoResponse:
    todo = await service.update_todo_state(user_id, todo_id, new_state)
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return service.build_response(todo)


@router.delete("/{todo_id}", status_code=204)
async def delete_todo(
    user_id: str,
    todo_id: str,
    service: TodoService = Depends(get_todo_service),
) -> Response:
    if not await service.delete_todo(user_id, todo_id):
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return Response(status_code=204)
