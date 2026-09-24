from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from todos.todo_repository import TodoRepository
from core.ai.resource_vector_store import ResourceVectorStore

EmbedFn = Callable[[List[str]], Awaitable[List[List[float]]]]

DEFAULT_LIMIT = 10
MAX_LIMIT = 50
RRF_K = 60  # same reciprocal-rank-fusion constant as SearchService


def todo_text(row: Dict[str, Any]) -> str:
    """What gets embedded for a todo: its title and description."""
    return f"{row['title']}\n{row.get('description') or ''}".strip()


class TodoSearchService:
    """
    Search a user's todos by meaning ("the tax return" finds "HMRC
    self-assessment") plus exact keyword matches, merged with reciprocal rank
    fusion — the same recipe as chat search, for a different resource.

    Counting and date/state filtering are NOT done here: those are plain
    queries (see assistant/todo_tools.py). Every call is scoped to `user_id`.
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

    async def index_todos(self, rows: List[Dict[str, Any]]) -> int:
        if not rows:
            return 0

        vectors = await self.embed([todo_text(row) for row in rows])
        now = datetime.now(timezone.utc).isoformat()
        for row, vector in zip(rows, vectors):
            await self.store.upsert(row["id"], row["user_id"], self.embedding_model, vector, now)
        return len(rows)

    async def remove_todo(self, todo_id: str) -> None:
        await self.store.delete(todo_id)

    async def reindex_user(self, user_id: str) -> int:
        """Backfill: embed every todo of this user that isn't indexed yet."""
        indexed = await self.store.indexed_ids(user_id)
        pending = [row for row in await self.repository.list_for_user(user_id) if row["id"] not in indexed]
        return await self.index_todos(pending)

    async def search(
        self, user_id: str, query: str, state: Optional[str] = None, limit: int = DEFAULT_LIMIT
    ) -> List[Dict[str, Any]]:
        query = query.strip()
        if not query:
            return []

        limit = max(1, min(limit, MAX_LIMIT))
        pool = limit * 3

        [query_vector] = await self.embed([query])
        vector_hits = await self.store.query(user_id, query_vector, pool)
        keyword_rows = await self.repository.search_by_keyword(user_id, query, pool)

        scores: Dict[str, float] = {}
        for rank, (todo_id, _) in enumerate(vector_hits):
            scores[todo_id] = scores.get(todo_id, 0.0) + 1 / (RRF_K + rank + 1)
        keyword_ids = {row["id"] for row in keyword_rows}
        for rank, row in enumerate(keyword_rows):
            scores[row["id"]] = scores.get(row["id"], 0.0) + 1 / (RRF_K + rank + 1)

        rows = {row["id"]: row for row in await self.repository.list_for_user(user_id)}
        ranked = [todo_id for todo_id in sorted(scores, key=lambda i: scores[i], reverse=True) if todo_id in rows]
        if state:
            ranked = [todo_id for todo_id in ranked if rows[todo_id]["state"] == state]

        return [
            {
                "id": todo_id,
                "title": rows[todo_id]["title"],
                "description": rows[todo_id].get("description"),
                "state": rows[todo_id]["state"],
                "complete_by": rows[todo_id]["complete_by"],
                "score": round(scores[todo_id], 6),
                "keywordMatch": todo_id in keyword_ids,
            }
            for todo_id in ranked[:limit]
        ]
