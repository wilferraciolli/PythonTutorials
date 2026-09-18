from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from models import Todo, TodoCreate, TodoState, TodoUpdate
from repositories.todo_repository import TodoRepository
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
    return TodoService(TodoRepository(env.DB))


@router.post("", response_model=Todo, status_code=201)
async def create_todo(todo: TodoCreate, service: TodoService = Depends(get_todo_service)) -> Todo:
    """Create a new TODO"""
    return await service.create_todo(todo)


@router.get("", response_model=List[Todo])
async def get_all_todos(
    state: Optional[TodoState] = None,
    service: TodoService = Depends(get_todo_service),
) -> List[Todo]:
    """Get all TODOs, optionally filtered by state"""
    return await service.get_all_todos(state=state)


@router.get("/{todo_id}", response_model=Todo)
async def get_todo(todo_id: int, service: TodoService = Depends(get_todo_service)) -> Todo:
    """Get a single TODO by ID"""
    todo = await service.get_todo(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return todo


@router.put("/{todo_id}", response_model=Todo)
async def update_todo(
    todo_id: int,
    todo_update: TodoUpdate,
    service: TodoService = Depends(get_todo_service),
) -> Todo:
    """Update a TODO (partial update - only send fields you want to change)"""
    todo = await service.update_todo(todo_id, todo_update)
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return todo


@router.patch("/{todo_id}/state/{new_state}", response_model=Todo)
async def update_todo_state(
    todo_id: int,
    new_state: TodoState,
    service: TodoService = Depends(get_todo_service),
) -> Todo:
    """Update only the state of a TODO"""
    todo = await service.update_todo_state(todo_id, new_state)
    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
    return todo


@router.delete("/{todo_id}", status_code=204)
async def delete_todo(todo_id: int, service: TodoService = Depends(get_todo_service)) -> None:
    """Delete a TODO"""
    success = await service.delete_todo(todo_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
