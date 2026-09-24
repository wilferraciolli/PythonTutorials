import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from core.ai.schemas import ReindexDTO
from core.common.api_response import API_PREFIX
from core.common.base_dto import EmbeddedRef, FieldMetadata, Link
from tags.tag_service import TagService
from todos.constants import (
    LINK_ADD_TAG,
    LINK_DELETE,
    LINK_SELF,
    LINK_TAGS,
    LINK_TODO_TEMPLATE,
    LINK_UPDATE,
    NOT_STARTED_TAG,
    OVERDUE_TAG,
    REINDEX_DATA_NAME,
    TODO_DATA_NAME,
    TODOS_DATA_NAME,
)
from todos.enums import TodoState
from todos.models import TodoModel
from todos.schemas import (
    TodoCreateRequest,
    TodoDTO,
    TodoListResponse,
    TodoMetadata,
    TodoReindexResponse,
    TodoResponse,
    TodoSearchHitDTO,
    TodoSearchResponse,
    TodoTemplateMetadata,
    TodoTemplateResponse,
    TodoUpdateRequest,
)
from todos.todo_repository import TodoRepository
from todos.todo_search_service import TodoSearchService
from todos.todo_utils import TodoUtils

logger = logging.getLogger(__name__)


class TodoService:
    """
    Business logic for a user's todos.

    Todos are personal: the router only lets the user in the path through
    (require_owner), so every link here is theirs to follow.
    """

    def __init__(
        self,
        repository: TodoRepository,
        tag_service: TagService,
        search_service: Optional[TodoSearchService] = None,
    ):
        self.repository = repository
        self.tag_service = tag_service
        self.search_service = search_service

    async def create_todo(self, user_id: str, request: TodoCreateRequest) -> TodoDTO:
        model = await self.repository.create(
            todo_id=str(uuid4()),
            user_id=user_id,
            title=request.title,
            description=request.description,
            complete_by=request.complete_by.isoformat(),
            state=request.state,
            created_date=datetime.now(timezone.utc).isoformat(),
        )
        await self._sync_auto_tags(model)
        await self._index(model)
        return self.to_dto(model)

    async def get_todo(self, user_id: str, todo_id: str) -> Optional[TodoDTO]:
        model = await self.repository.get_by_id(todo_id, user_id)
        if not model:
            return None

        if TodoUtils.is_overdue(model):
            logger.info("todo %s is overdue", todo_id)
        elif TodoUtils.is_due_soon(model, days=3):
            logger.info("todo %s is due soon", todo_id)

        return self.to_dto(model)

    async def get_all_todos(self, user_id: str, state: Optional[TodoState] = None) -> List[TodoDTO]:
        return [self.to_dto(model) for model in await self.repository.get_all(user_id, state=state)]

    async def update_todo(self, user_id: str, todo_id: str, request: TodoUpdateRequest) -> Optional[TodoDTO]:
        model = await self.repository.update(
            todo_id,
            user_id,
            title=request.title,
            description=request.description,
            complete_by=request.complete_by.isoformat() if request.complete_by else None,
            state=request.state,
        )
        if not model:
            return None

        await self._sync_auto_tags(model)
        await self._index(model)
        return self.to_dto(model)

    async def update_todo_state(self, user_id: str, todo_id: str, new_state: TodoState) -> Optional[TodoDTO]:
        model = await self.repository.update(todo_id, user_id, state=new_state)
        if not model:
            return None

        await self._sync_auto_tags(model)
        return self.to_dto(model)

    async def delete_todo(self, user_id: str, todo_id: str) -> bool:
        deleted = await self.repository.delete(todo_id, user_id)
        if deleted:
            await self.tag_service.delete_all_tags_for_resource(todo_id)
            if self.search_service:
                await self.search_service.remove_todo(todo_id)
        return deleted

    async def _sync_auto_tags(self, todo: TodoModel) -> None:
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

    async def _index(self, todo: TodoModel) -> None:
        # Best effort: search indexing must never fail a todo write. Anything
        # missed is picked up by POST .../todos/search/reindex.
        if not self.search_service:
            return
        try:
            await self.search_service.index_todos([todo])
        except Exception:
            logger.exception("failed to index todo %s for search", todo.id)

    # --- responses

    def to_dto(self, model: TodoModel) -> TodoDTO:
        return TodoDTO(**model.model_dump(), links=self.build_links(model))

    @staticmethod
    def build_links(todo: TodoModel) -> dict[str, Link]:
        """Resource-level links for this todo. The owner may do everything with it."""
        url = f"{API_PREFIX}/users/{todo.user_id}/todos/{todo.id}"
        return {
            LINK_SELF: Link(href=url, method="GET"),
            LINK_UPDATE: Link(href=url, method="PUT"),
            LINK_DELETE: Link(href=url, method="DELETE"),
            LINK_ADD_TAG: Link(href=f"{API_PREFIX}/tags", method="POST"),
            LINK_TAGS: Link(href=f"{API_PREFIX}/tags?resource_id={todo.id}", method="GET"),
        }

    @staticmethod
    def build_meta_links(user_id: str) -> dict[str, Link]:
        """
        Collection-level links.

        There is no standalone `createTodo` link: the create URL is never
        POSTed to blind. Clients get it by first GETting `todoTemplate`
        (its field metadata says what's mandatory) and deriving the create
        URL from that template link.
        """
        return {LINK_TODO_TEMPLATE: Link(href=f"{API_PREFIX}/users/{user_id}/todos/template", method="GET")}

    @staticmethod
    def _state_values(todo: Optional[TodoDTO] = None) -> list[EmbeddedRef]:
        # A todo that has left NEW can't go back to it, so NEW is only
        # offered while the todo is still NEW (or for a list, where there's
        # no single todo to judge by).
        return [
            EmbeddedRef(id=state.value, value=state.value.title())
            for state in TodoState
            if todo is None or todo.state == TodoState.NEW or state != TodoState.NEW
        ]

    def build_metadata(self, todo: Optional[TodoDTO] = None) -> TodoMetadata:
        return TodoMetadata(
            id=FieldMetadata(readOnly=True, hidden=True),
            user_id=FieldMetadata(readOnly=True, hidden=True),
            title=FieldMetadata(mandatory=True),
            complete_by=FieldMetadata(mandatory=True),
            state=FieldMetadata(mandatory=True, values=self._state_values(todo)),
            created_date=FieldMetadata(readOnly=True),
        )

    def build_response(self, todo: TodoDTO) -> TodoResponse:
        return TodoResponse.of(TODO_DATA_NAME, todo, self.build_metadata(todo), self.build_meta_links(todo.user_id))

    def build_list_response(self, user_id: str, todos: List[TodoDTO]) -> TodoListResponse:
        return TodoListResponse.of(TODOS_DATA_NAME, todos, self.build_metadata(), self.build_meta_links(user_id))

    def build_search_response(self, user_id: str, hits: List[TodoSearchHitDTO]) -> TodoSearchResponse:
        return TodoSearchResponse.of(TODOS_DATA_NAME, hits, self.build_metadata(), self.build_meta_links(user_id))

    def build_reindex_response(self, user_id: str, indexed: int) -> TodoReindexResponse:
        return TodoReindexResponse.of(
            REINDEX_DATA_NAME, ReindexDTO(indexed=indexed), self.build_metadata(), self.build_meta_links(user_id)
        )

    def build_template_response(self, user_id: str) -> TodoTemplateResponse:
        # Blank title, so skip the create validation (min_length) on purpose.
        template = TodoCreateRequest.model_construct(
            title="",
            description="",
            complete_by=datetime.now(timezone.utc),
            state=TodoState.NEW,
        )
        return TodoTemplateResponse.of(
            TODO_DATA_NAME,
            template,
            TodoTemplateMetadata(
                title=FieldMetadata(mandatory=True),
                complete_by=FieldMetadata(mandatory=True),
                state=FieldMetadata(mandatory=True, values=self._state_values()),
            ),
            self.build_meta_links(user_id),
        )
