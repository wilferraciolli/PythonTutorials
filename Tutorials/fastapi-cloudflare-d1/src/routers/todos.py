from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from models import Todo, TodoCreate, TodoState, TodoUpdate
from repositories.tag_repository import TagRepository
from repositories.todo_repository import TodoRepository
from services.tag_service import TagService
from services.todo_service import TodoService

router = APIRouter(prefix="/todos", tags=["todos"])


def get_todo_service(request: Request) -> TodoService:
    """
    Build a TodoService per-request.

    Unlike SQLAlchemy's global `engine`, the D1 binding (`env.DB`) only exists
    on the incoming request's `scope["env"]` - Cloudflare injects it per call,
    so it cannot be created once at startup like our old `Depends(get_db)`.
    """
    env = request.scope["env"]
    tag_service = TagService(TagRepository(env.DB))
    return TodoService(TodoRepository(env.DB), tag_service)


@router.get("/template", status_code=200)
async def create_todo(service: TodoService = Depends(get_todo_service)) -> Dict[str, Any]:
    """Get a TODO template"""
    template = service.get_template()
    return service.build_response("todo", template)


@router.post("", status_code=201)
async def create_todo(todo: TodoCreate, service: TodoService = Depends(get_todo_service)) -> Dict[str, Any]:
    """Create a new TODO"""
    created = await service.create_todo(todo)
    return service.build_response("todo", created)


@router.get("")
async def get_all_todos(
    state: Optional[TodoState] = None,
    service: TodoService = Depends(get_todo_service),
) -> Dict[str, Any]:
    """Get all TODOs, optionally filtered by state"""
    todos = await service.get_all_todos(state=state)
    return service.build_response("todos", todos)


@router.get("/{todo_id}")
async def get_todo(todo_id: str, service: TodoService = Depends(get_todo_service)) -> Dict[str, Any]:
    """Get a single TODO by ID"""
    todo = await service.get_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return service.build_response("todo", todo)


@router.put("/{todo_id}")
async def update_todo(
    todo_id: str,
    todo_update: TodoUpdate,
    service: TodoService = Depends(get_todo_service),
) -> Dict[str, Any]:
    """Update a TODO (partial update - only send fields you want to change)"""
    todo = await service.update_todo(todo_id, todo_update)
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return service.build_response("todo", todo)


@router.patch("/{todo_id}/state/{new_state}")
async def update_todo_state(
    todo_id: str,
    new_state: TodoState,
    service: TodoService = Depends(get_todo_service),
) -> Dict[str, Any]:
    """Update only the state of a TODO"""
    todo = await service.update_todo_state(todo_id, new_state)
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return service.build_response("todo", todo)


@router.delete("/{todo_id}", status_code=204)
async def delete_todo(todo_id: str, service: TodoService = Depends(get_todo_service)) -> None:
    """Delete a TODO"""
    success = await service.delete_todo(todo_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
