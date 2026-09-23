from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List

from api_response import API_PREFIX, envelope
from models import ChatSearchHit, Link
from repositories.chat_repository import ChatRepository
from vector_store import VectorItem, VectorStore

EmbedFn = Callable[[List[str]], Awaitable[List[List[float]]]]

SNIPPET_LENGTH = 300
DEFAULT_LIMIT = 10
MAX_LIMIT = 50

# Reciprocal rank fusion constant: dampens the gap between rank 1 and rank 2
# so neither list (vector, keyword) dominates the merged ranking.
RRF_K = 60


class SearchService:
    """
    AI search over a user's chat history (RAG retrieval, no generation yet).

    Write path: `index_messages` embeds new messages into the vector store.
    Query path: `search` embeds the question, takes the closest messages
    from the vector store, adds exact keyword matches, and merges both
    ranked lists with reciprocal rank fusion — so "java" finds both chats
    that talk about the JVM and messages that literally contain "java".
    Every store/repository call is scoped to `user_id`.
    """

    def __init__(
        self,
        chat_repository: ChatRepository,
        vector_store: VectorStore,
        embed: EmbedFn,
        embedding_model: str,
        providers: List[str],
    ) -> None:
        self.chat_repository = chat_repository
        self.vector_store = vector_store
        self.embed = embed
        self.embedding_model = embedding_model
        self.providers = providers

    async def index_messages(self, user_id: str, messages: List[Dict[str, Any]]) -> int:
        messages = [message for message in messages if message["content"].strip()]
        if not messages:
            return 0

        vectors = await self.embed([message["content"] for message in messages])
        items = [
            VectorItem(message["id"], message["chat_id"], user_id, self.embedding_model, vector)
            for message, vector in zip(messages, vectors)
        ]
        await self.vector_store.upsert(items, datetime.now(timezone.utc).isoformat())
        return len(items)

    async def remove_chat(self, chat_id: str) -> None:
        await self.vector_store.delete_by_chat(chat_id)

    async def reindex_user(self, user_id: str) -> int:
        """Backfill: embed every message of this user that isn't indexed yet."""
        indexed = await self.vector_store.indexed_message_ids(user_id)
        pending = [
            message
            for message in await self.chat_repository.list_messages_for_user(user_id, self.providers)
            if message["id"] not in indexed
        ]
        return await self.index_messages(user_id, pending)

    async def search(self, user_id: str, query: str, limit: int = DEFAULT_LIMIT) -> List[ChatSearchHit]:
        query = query.strip()
        if not query:
            return []

        limit = max(1, min(limit, MAX_LIMIT))
        pool = limit * 3

        [query_vector] = await self.embed([query])
        vector_hits = await self.vector_store.query(user_id, query_vector, pool)
        keyword_rows = await self.chat_repository.search_messages_by_keyword(
            user_id, query, self.providers, pool
        )

        scores: Dict[str, float] = {}
        for rank, hit in enumerate(vector_hits):
            scores[hit.message_id] = scores.get(hit.message_id, 0.0) + 1 / (RRF_K + rank + 1)
        keyword_ids = {row["id"] for row in keyword_rows}
        for rank, row in enumerate(keyword_rows):
            scores[row["id"]] = scores.get(row["id"], 0.0) + 1 / (RRF_K + rank + 1)

        top_ids = sorted(scores, key=lambda message_id: scores[message_id], reverse=True)[:limit]
        rows = {row["id"]: row for row in await self.chat_repository.get_messages_for_user(user_id, top_ids)}

        return [
            self.to_hit(rows[message_id], scores[message_id], message_id in keyword_ids)
            for message_id in top_ids
            if message_id in rows  # a message deleted since indexing just drops out
        ]

    def to_hit(self, row: Dict[str, Any], score: float, keyword_match: bool) -> ChatSearchHit:
        content = " ".join(row["content"].split())
        snippet = content if len(content) <= SNIPPET_LENGTH else content[: SNIPPET_LENGTH - 1].rstrip() + "…"
        chat_href = f"{API_PREFIX}/users/{row['user_id']}/chats/{row['chat_id']}"
        return ChatSearchHit(
            messageId=row["id"],
            chatId=row["chat_id"],
            chatTitle=row["chat_title"],
            role=row["role"],
            snippet=snippet,
            score=round(score, 6),
            keywordMatch=keyword_match,
            created_date=row["created_date"],
            links={"chat": Link(href=chat_href, method="GET")},
        )

    def build_response(self, user_id: str, hits: List[ChatSearchHit]) -> Dict[str, Any]:
        return envelope(
            data_name="hits",
            data=hits,
            metadata={},
            meta_links={
                "search": Link(href=f"{API_PREFIX}/users/{user_id}/chats/search", method="GET"),
                "reindex": Link(href=f"{API_PREFIX}/users/{user_id}/chats/search/reindex", method="POST"),
            },
        )

    def build_reindex_response(self, indexed: int) -> Dict[str, Any]:
        return envelope(data_name="reindex", data={"indexed": indexed}, metadata={}, meta_links={})
