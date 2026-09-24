from datetime import datetime, timezone
from typing import Dict, List, Optional

from core.ai.embeddings import EmbedFn
from core.ai.resource_vector_store import ResourceVectorStore
from todos.enums import TodoState
from todos.models import TodoModel
from todos.schemas import TodoSearchHitDTO
from todos.todo_repository import TodoRepository

DEFAULT_LIMIT = 10
MAX_LIMIT = 50
RRF_K = 60  # same reciprocal-rank-fusion constant as chat search


def todo_text(todo: TodoModel) -> str:
    """What gets embedded for a todo: its title and description."""
    return f"{todo.title}\n{todo.description or ''}".strip()


class TodoSearchService:
    """
    Search a user's todos by meaning ("the tax return" finds "HMRC
    self-assessment") plus exact keyword matches, merged with reciprocal rank
    fusion — the same recipe as chat search, for a different resource.

    Counting and date/state filtering are NOT done here: those are plain
    queries (see assistant/tools/todo_tools.py). Every call is scoped to `user_id`.
    """

    def __init__(
        self,
        repository: TodoRepository,
        store: ResourceVectorStore,
        embed: EmbedFn,
        embedding_model: str,
    ) -> None:
        self.repository = repository
        self.store = store
        self.embed = embed
        self.embedding_model = embedding_model

    async def index_todos(self, todos: List[TodoModel]) -> int:
        if not todos:
            return 0

        vectors = await self.embed([todo_text(todo) for todo in todos])
        now = datetime.now(timezone.utc).isoformat()
        for todo, vector in zip(todos, vectors):
            await self.store.upsert(todo.id, todo.user_id, self.embedding_model, vector, now)
        return len(todos)

    async def remove_todo(self, todo_id: str) -> None:
        await self.store.delete(todo_id)

    async def reindex_user(self, user_id: str) -> int:
        """Backfill: embed every todo of this user that isn't indexed yet."""
        indexed = await self.store.indexed_ids(user_id)
        pending = [todo for todo in await self.repository.list_for_user(user_id) if todo.id not in indexed]
        return await self.index_todos(pending)

    async def search(
        self, user_id: str, query: str, state: Optional[TodoState] = None, limit: int = DEFAULT_LIMIT
    ) -> List[TodoSearchHitDTO]:
        query = query.strip()
        if not query:
            return []

        limit = max(1, min(limit, MAX_LIMIT))
        pool = limit * 3

        [query_vector] = await self.embed([query])
        vector_hits = await self.store.query(user_id, query_vector, pool)
        keyword_matches = await self.repository.search_by_keyword(user_id, query, pool)

        scores: Dict[str, float] = {}
        for rank, (todo_id, _) in enumerate(vector_hits):
            scores[todo_id] = scores.get(todo_id, 0.0) + 1 / (RRF_K + rank + 1)
        keyword_ids = {todo.id for todo in keyword_matches}
        for rank, todo in enumerate(keyword_matches):
            scores[todo.id] = scores.get(todo.id, 0.0) + 1 / (RRF_K + rank + 1)

        todos = {todo.id: todo for todo in await self.repository.list_for_user(user_id)}
        ranked = [todo_id for todo_id in sorted(scores, key=lambda i: scores[i], reverse=True) if todo_id in todos]
        if state:
            ranked = [todo_id for todo_id in ranked if todos[todo_id].state == state]

        return [
            TodoSearchHitDTO(
                id=todo_id,
                title=todos[todo_id].title,
                description=todos[todo_id].description,
                state=todos[todo_id].state,
                complete_by=todos[todo_id].complete_by,
                score=round(scores[todo_id], 6),
                keywordMatch=todo_id in keyword_ids,
            )
            for todo_id in ranked[:limit]
        ]
