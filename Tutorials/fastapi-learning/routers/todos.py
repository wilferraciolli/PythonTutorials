from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from models import Todo, TodoCreate, TodoUpdate, TodoState
from services.todo_service import TodoService
from dependencies import get_db, get_todo_repository, get_todo_service

router = APIRouter(prefix="/todos", tags=["todos"])


# CREATE
@router.post("/", response_model=Todo, status_code=201)
def create_todo(
        todo: TodoCreate,
        service: TodoService = Depends(get_todo_service)
) -> Todo:
    """Create a new TODO"""
    return service.create_todo(todo)


# GET ALL
@router.get("/", response_model=List[Todo])
def get_all_todos(
        state: Optional[TodoState] = None,
        service: TodoService = Depends(get_todo_service)
) -> List[Todo]:
    """Get all TODOs"""
    return service.get_all_todos(state=state)


# READ ONE - GET
@router.get("/{todo_id}", response_model=Todo)
def get_todo(
        todo_id: int,
        service: TodoService = Depends(get_todo_service)
) -> Todo:
    """Get a single TODO by ID"""
    todo = service.get_todo(todo_id)

    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")

    return todo


# UPDATE - PUT
@router.put("/{todo_id}", response_model=Todo)
def update_todo(
        todo_id: int,
        todo_update: TodoUpdate,
        service: TodoService = Depends(get_todo_service)
) -> Todo:
    """Update a TODO"""
    todo = service.update_todo(todo_id, todo_update)

    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")

    return todo


# UPDATE STATE - PATCH (like a partial update)
@router.patch("/{todo_id}/state/{new_state}")
def update_todo_state(
        todo_id: int,
        new_state: TodoState,
        service: TodoService = Depends(get_todo_service)
) -> Todo:
    """Update TODO state"""
    todo = service.update_todo_state(todo_id, new_state)

    if not todo:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")

    return todo


# DELETE - DELETE
@router.delete("/{todo_id}")
def delete_todo(
        todo_id: int,
        service: TodoService = Depends(get_todo_service)
) -> None:
    """Delete a TODO"""
    success = service.delete_todo(todo_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"TODO {todo_id} not found")
