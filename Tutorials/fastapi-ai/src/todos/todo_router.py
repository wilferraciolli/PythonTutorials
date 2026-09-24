from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from core.config.database import get_database
from core.ai.embeddings import get_embedder
from core.ai.resource_vector_store import ResourceVectorStore
from core.security.authorization import require_owner
from todos.enums import TodoState
from todos.schemas import Todo, TodoCreate, TodoUpdate
from tags.tag_repository import TagRepository
from todos.todo_repository import TodoRepository
from tags.tag_service import TagService
from todos.todo_search_service import DEFAULT_LIMIT, TodoSearchService
from todos.todo_service import TodoService

router = APIRouter(prefix="/users/{user_id}/todos", tags=["todos"], dependencies=[Depends(require_owner)])


def get_todo_search_service(request: Request) -> TodoSearchService:
    db = get_database(request)
    embed_texts, model = get_embedder(request)
    return TodoSearchService(TodoRepository(db), ResourceVectorStore(db, "todo"), embed_texts, model)


def get_todo_service(request: Request) -> TodoService:
    """
    Build a TodoService per-request using the configured database adapter.

    The app can run against local SQLite, Cloudflare D1 binding, or D1 HTTP
    without repositories/services depending on a concrete database runtime.
    """
    db = get_database(request)
    tag_service = TagService(TagRepository(db))
    return TodoService(TodoRepository(db), tag_service, get_todo_search_service(request))


@router.get("/search")
async def search_todos(
    user_id: str,
    q: str,
    state: Optional[TodoState] = None,
    limit: int = DEFAULT_LIMIT,
    search: TodoSearchService = Depends(get_todo_search_service),
    service: TodoService = Depends(get_todo_service),
) -> Dict[str, Any]:
    """Find todos by meaning (embeddings) and keyword, best first."""
    hits = await search.search(user_id, q, state.value if state else None, limit)
    return service.build_response("todos", hits, user_id)


@router.post("/search/reindex")
async def reindex_todos(
    user_id: str,
    search: TodoSearchService = Depends(get_todo_search_service),
    service: TodoService = Depends(get_todo_service),
) -> Dict[str, Any]:
    """Backfill: embed this user's todos that aren't indexed yet."""
    indexed = await search.reindex_user(user_id)
    return service.build_response("reindex", {"indexed": indexed}, user_id)


@router.get("/template", status_code=200)
async def get_todo_template(
    user_id: str,
    service: TodoService = Depends(get_todo_service),
) -> Dict[str, Any]:
    """Get a TODO template"""
    return service.build_template_response(user_id)


@router.post("", status_code=201)
async def create_todo(
    user_id: str,
    todo: TodoCreate,
    service: TodoService = Depends(get_todo_service),
) -> Dict[str, Any]:
    """Create a new TODO"""
    created = await service.create_todo(user_id, todo)
    return service.build_response("todo", created, user_id)


@router.get("")
async def get_all_todos(
    user_id: str,
    state: Optional[TodoState] = None,
    service: TodoService = Depends(get_todo_service),
) -> Dict[str, Any]:
    """Get all TODOs for a user, optionally filtered by state"""
    todos = await service.get_all_todos(user_id, state=state)
    return service.build_response("todos", todos, user_id)


@router.get("/{todo_id}")
async def get_todo(
    user_id: str,
    todo_id: str,
    service: TodoService = Depends(get_todo_service),
) -> Dict[str, Any]:
    """Get a single TODO by ID"""
    todo = await service.get_todo(user_id, todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return service.build_response("todo", todo, user_id)


@router.put("/{todo_id}")
async def update_todo(
    user_id: str,
    todo_id: str,
    todo_update: TodoUpdate,
    service: TodoService = Depends(get_todo_service),
) -> Dict[str, Any]:
    """Update a TODO (partial update - only send fields you want to change)"""
    todo = await service.update_todo(user_id, todo_id, todo_update)
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return service.build_response("todo", todo, user_id)


@router.patch("/{todo_id}/state/{new_state}")
async def update_todo_state(
    user_id: str,
    todo_id: str,
    new_state: TodoState,
    service: TodoService = Depends(get_todo_service),
) -> Dict[str, Any]:
    """Update only the state of a TODO"""
    todo = await service.update_todo_state(user_id, todo_id, new_state)
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return service.build_response("todo", todo, user_id)


@router.delete("/{todo_id}", status_code=204)
async def delete_todo(
    user_id: str,
    todo_id: str,
    service: TodoService = Depends(get_todo_service),
) -> None:
    """Delete a TODO"""
    success = await service.delete_todo(user_id, todo_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
