from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from links import build_todo_links
from models import Todo, TodoCreate, TodoState, TodoUpdate
from repositories.todo_repository import TodoRepository
from services.tag_service import TagService
from utils import TodoUtils

OVERDUE_TAG = "overdue"
NOT_STARTED_TAG = "not-started"


class TodoService:
    """Business logic for TODOs, sitting between the router and the D1 repository."""

    def __init__(self, repository: TodoRepository, tag_service: TagService):
        self.repository = repository
        self.tag_service = tag_service

    async def create_todo(self, todo_create: TodoCreate) -> Todo:
        row = await self.repository.create(
            title=todo_create.title,
            description=todo_create.description,
            complete_by=todo_create.complete_by.isoformat(),
            state=todo_create.state,
            created_date=datetime.now(timezone.utc).isoformat(),
        )
        todo = self._row_to_todo(row)
        await self._sync_auto_tags(todo)
        return todo

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

        todo = self._row_to_todo(row)
        await self._sync_auto_tags(todo)
        return todo

    async def update_todo_state(self, todo_id: int, new_state: TodoState) -> Optional[Todo]:
        row = await self.repository.update(todo_id, state=new_state)
        if not row:
            return None

        todo = self._row_to_todo(row)
        await self._sync_auto_tags(todo)
        return todo

    async def delete_todo(self, todo_id: int) -> bool:
        deleted = await self.repository.delete(todo_id)
        if deleted:
            await self.tag_service.delete_all_tags_for_resource(todo_id)
        return deleted

    async def _sync_auto_tags(self, todo: Todo) -> None:
        """
        Keep the "overdue" and "not-started" tags in sync with the todo's
        current state. The two are mutually exclusive - adding one removes
        the other, so a todo never ends up wearing a stale tag.
        """
        if TodoUtils.is_overdue(todo):
            await self.tag_service.add_tag_if_missing(todo.id, OVERDUE_TAG)
            await self.tag_service.remove_tag_by_name(todo.id, NOT_STARTED_TAG)
        elif todo.state == TodoState.NEW:
            await self.tag_service.add_tag_if_missing(todo.id, NOT_STARTED_TAG)
            await self.tag_service.remove_tag_by_name(todo.id, OVERDUE_TAG)

    @staticmethod
    def _row_to_todo(row: Dict[str, Any]) -> Todo:
        """Convert a raw D1 row (dict-like) into a validated Todo model."""
        todo_id = row["id"]
        return Todo(
            id=todo_id,
            title=row["title"],
            description=row.get("description") if hasattr(row, "get") else row["description"],
            complete_by=datetime.fromisoformat(row["complete_by"]),
            state=TodoState(row["state"]),
            created_date=datetime.fromisoformat(row["created_date"]),
            links=build_todo_links(todo_id),
        )
