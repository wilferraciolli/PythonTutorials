from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from models import Todo, TodoCreate, TodoState, TodoUpdate
from repositories.todo_repository import TodoRepository
from utils import TodoUtils


class TodoService:
    """Business logic for TODOs, sitting between the router and the D1 repository."""

    def __init__(self, repository: TodoRepository):
        self.repository = repository

    async def create_todo(self, todo_create: TodoCreate) -> Todo:
        row = await self.repository.create(
            title=todo_create.title,
            description=todo_create.description,
            complete_by=todo_create.complete_by.isoformat(),
            state=todo_create.state,
            created_date=datetime.now(timezone.utc).isoformat(),
        )
        return self._row_to_todo(row)

    async def get_todo(self, todo_id: int) -> Optional[Todo]:
        row = await self.repository.get_by_id(todo_id)
        if not row:
            return None

        todo = self._row_to_todo(row)

        if TodoUtils.is_overdue(todo):
            print(f"WARNING: TODO {todo_id} is overdue!")
        if TodoUtils.is_due_soon(todo, days=3):
            print(f"NOTICE: TODO {todo_id} is due soon!")

        return todo

    async def get_all_todos(self, state: Optional[TodoState] = None) -> List[Todo]:
        rows = await self.repository.get_all(state=state)
        return [self._row_to_todo(row) for row in rows]

    async def update_todo(self, todo_id: int, todo_update: TodoUpdate) -> Optional[Todo]:
        update_data = todo_update.model_dump(exclude_unset=True)
        if "complete_by" in update_data and update_data["complete_by"] is not None:
            update_data["complete_by"] = todo_update.complete_by.isoformat()

        row = await self.repository.update(todo_id, **update_data)
        if not row:
            return None

        return self._row_to_todo(row)

    async def update_todo_state(self, todo_id: int, new_state: TodoState) -> Optional[Todo]:
        row = await self.repository.update(todo_id, state=new_state)
        if not row:
            return None

        return self._row_to_todo(row)

    async def delete_todo(self, todo_id: int) -> bool:
        return await self.repository.delete(todo_id)

    @staticmethod
    def _row_to_todo(row: Dict[str, Any]) -> Todo:
        """Convert a raw D1 row (dict-like) into a validated Todo model."""
        return Todo(
            id=row["id"],
            title=row["title"],
            description=row.get("description") if hasattr(row, "get") else row["description"],
            complete_by=datetime.fromisoformat(row["complete_by"]),
            state=TodoState(row["state"]),
            created_date=datetime.fromisoformat(row["created_date"]),
        )
