from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from api_response import envelope
from models import Link, Todo, TodoCreate, TodoState, TodoUpdate, format_utc_datetime
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

    def build_template_response(self, user_id: str) -> Dict[str, Any]:
        """
        Build a create-template response.

        Templates use the create DTO shape, not the persisted Todo shape, so
        server-managed fields like id and created_date are omitted entirely.
        """
        template = {
            "id": "",
            "title": "",
            "description": "",
            "complete_by": format_utc_datetime(datetime.now(timezone.utc)),
            "state": TodoState.NEW,
            "created_date": ""
        }

        return envelope(
            "todo",
            template,
            self._template_metadata(),
            self._meta_links(user_id),
        )

    async def create_todo(self, user_id: str, todo_create: TodoCreate) -> Todo:
        row = await self.repository.create(
            todo_id=str(uuid4()),
            user_id=user_id,
            title=todo_create.title,
            description=todo_create.description,
            complete_by=todo_create.complete_by.isoformat(),
            state=todo_create.state,
            created_date=datetime.now(timezone.utc).isoformat(),
        )
        todo = self._row_to_todo(row)
        await self._sync_auto_tags(todo)
        return todo

    async def get_todo(self, user_id: str, todo_id: str) -> Optional[Todo]:
        row = await self.repository.get_by_id(todo_id, user_id)
        if not row:
            return None

        todo = self._row_to_todo(row)

        if TodoUtils.is_overdue(todo):
            print(f"WARNING: TODO {todo_id} is overdue!")
        if TodoUtils.is_due_soon(todo, days=3):
            print(f"NOTICE: TODO {todo_id} is due soon!")

        return todo

    async def get_all_todos(self, user_id: str, state: Optional[TodoState] = None) -> List[Todo]:
        rows = await self.repository.get_all(user_id, state=state)
        return [self._row_to_todo(row) for row in rows]

    async def update_todo(self, user_id: str, todo_id: str, todo_update: TodoUpdate) -> Optional[Todo]:
        update_data = todo_update.model_dump(exclude_unset=True)
        if "complete_by" in update_data and update_data["complete_by"] is not None:
            update_data["complete_by"] = todo_update.complete_by.isoformat()

        row = await self.repository.update(todo_id, user_id, **update_data)
        if not row:
            return None

        todo = self._row_to_todo(row)
        await self._sync_auto_tags(todo)
        return todo

    async def update_todo_state(self, user_id: str, todo_id: str, new_state: TodoState) -> Optional[Todo]:
        row = await self.repository.update(todo_id, user_id, state=new_state)
        if not row:
            return None

        todo = self._row_to_todo(row)
        await self._sync_auto_tags(todo)
        return todo

    async def delete_todo(self, user_id: str, todo_id: str) -> bool:
        deleted = await self.repository.delete(todo_id, user_id)
        if deleted:
            await self.tag_service.delete_all_tags_for_resource(todo_id)
        return deleted

    def build_response(
        self,
        data_name: str,
        data: Any,
        user_id: str,
        messages: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Build the full Todo response envelope for this stateless request.

        Metadata and links are calculated here in the application service,
        because they are business decisions. Later, this method can use the
        current user/permissions to hide fields or remove links like delete.
        """
        todo = data if isinstance(data, Todo) else None
        return envelope(
            data_name,
            data,
            self._metadata(todo),
            self._meta_links(user_id),
            messages,
        )

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

    def _row_to_todo(self, row: Dict[str, Any]) -> Todo:
        """Convert a raw D1 row (dict-like) into a validated Todo model."""
        todo_id = row["id"]
        todo = Todo(
            id=todo_id,
            user_id=row["user_id"],
            title=row["title"],
            description=row.get("description") if hasattr(row, "get") else row["description"],
            complete_by=datetime.fromisoformat(row["complete_by"]),
            state=TodoState(row["state"]),
            created_date=datetime.fromisoformat(row["created_date"]),
        )
        todo.links = self._links(todo)
        return todo

    def _links(
        self,
        todo: Todo,
        *,
        can_update: bool = True,
        can_delete: bool = True,
        can_add_tag: bool = True,
        can_view_tags: bool = True,
    ) -> Dict[str, Link]:
        """
        Resource-level links for this Todo, calculated per request.

        Permission flags are hard-coded for now because there is no auth yet.
        Once auth exists, these values should come from the current user.
        """
        links = {
            "self": Link(href=f"/users/{todo.user_id}/todos/{todo.id}", method="GET"),
        }

        if can_update:
            links["update"] = Link(href=f"/users/{todo.user_id}/todos/{todo.id}", method="PUT")

        if can_delete:
            links["delete"] = Link(href=f"/users/{todo.user_id}/todos/{todo.id}", method="DELETE")

        if can_add_tag:
            links["addTag"] = Link(href="/tags", method="POST")

        if can_view_tags:
            links["tags"] = Link(href=f"/tags?resource_id={todo.id}", method="GET")

        return links

    def _metadata(self, todo: Optional[Todo] = None) -> Dict[str, Any]:
        """
        Field metadata for Todo payloads, calculated per request.

        Example business rule:
        - If a todo has already left NEW, NEW is no longer offered as an
          allowed state value.
        """
        state_values = [
            {"id": state.value, "value": state.value.title()}
            for state in TodoState
            if todo is None or todo.state == TodoState.NEW or state != TodoState.NEW
        ]

        return {
            "id": {
                "readOnly": True,
                "hidden": True,
            },
            "user_id": {
                "readOnly": True,
                "hidden": True,
            },
            "title": {
                "mandatory": True,
            },
            "complete_by": {
                "mandatory": True,
            },
            "state": {
                "mandatory": True,
                "values": state_values,
            },
            "created_date": {
                "readOnly": True
            }
        }

    def _template_metadata(self) -> Dict[str, Any]:
        """Metadata for a create template: only fields the client can submit."""
        return {
            "title": {
                "mandatory": True,
            },
            "complete_by": {
                "mandatory": True,
            },
            "state": {
                "mandatory": True,
                "values": [
                    {"id": state.value, "value": state.value.title()}
                    for state in TodoState
                ],
            },
        }

    def _meta_links(self, user_id: str, *, can_create: bool = True) -> Dict[str, Link]:
        """
        Collection-level Todo links, calculated per request.

        There is no standalone `createTodo` link: the create URL is never
        POSTed to blind. Clients get it by first GETting `todoTemplate`
        (its field metadata says what's mandatory) and deriving the create
        URL from that template link.
        """
        if not can_create:
            return {}

        return {
            "todoTemplate": Link(href=f"/users/{user_id}/todos/template", method="GET"),
        }
