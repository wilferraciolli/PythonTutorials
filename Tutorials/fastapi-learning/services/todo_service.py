from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from models import Todo, TodoCreate, TodoUpdate, TodoState
from repositories.todo_repository import TodoRepository
from utils import TodoUtils


class TodoService:
    """Service for TODO business logic"""

    def __init__(self, repository: TodoRepository):
        self.repository = repository

    def create_todo(self, todo_create: TodoCreate) -> Todo:
        """Create a new TODO"""
        db_todo = self.repository.create(
            title=todo_create.title,
            description=todo_create.description,
            complete_by=todo_create.complete_by,
            state=todo_create.state
        )

        return Todo.from_orm(db_todo)

    def get_todo(self, todo_id: int) -> Optional[Todo]:
        """Get TODO by ID"""
        db_todo = self.repository.get_by_id(todo_id)

        if not db_todo:
            return None

        todo = Todo.from_orm(db_todo)

        # Check status
        if TodoUtils.is_overdue(todo):
            print(f"⚠️ TODO {todo_id} is overdue!")

        if TodoUtils.is_due_soon(todo, days=3):
            print(f"⏰ TODO {todo_id} is due soon!")

        return todo

    def get_all_todos(self, state: Optional[TodoState] = None) -> List[Todo]:
        """Get all TODOs"""
        db_todos = self.repository.get_all(state=state)
        return [Todo.from_orm(todo) for todo in db_todos]

    def update_todo(self, todo_id: int, todo_update: TodoUpdate) -> Optional[Todo]:
        """Update TODO"""
        update_data = todo_update.dict(exclude_unset=True)

        db_todo = self.repository.update(todo_id, **update_data)

        if not db_todo:
            return None

        return Todo.from_orm(db_todo)

    def update_todo_state(self, todo_id: int, new_state: TodoState) -> Optional[Todo]:
        """Update TODO state only"""
        db_todo = self.repository.update(todo_id, state=new_state)

        if not db_todo:
            return None

        return Todo.from_orm(db_todo)

    def delete_todo(self, todo_id: int) -> bool:
        """Delete TODO"""
        return self.repository.delete(todo_id)