from datetime import datetime, timezone
from typing import Dict, List

from chats.chat_repository import ChatRepository
from chats.constants import HITS_DATA_NAME, LINK_CHAT, LINK_REINDEX, LINK_SEARCH, REINDEX_DATA_NAME
from chats.models import ChatMessageHitModel, ChatMessageModel
from chats.schemas import ChatReindexResponse, ChatSearchHitDTO, ChatSearchResponse
from core.ai.embeddings import EmbedFn
from core.ai.schemas import ReindexDTO
from core.ai.vector_store import VectorItem, VectorStore
from core.common.api_response import API_PREFIX
from core.common.base_dto import Link, NoMetadata

SNIPPET_LENGTH = 300
DEFAULT_LIMIT = 10
MAX_LIMIT = 50

# Reciprocal rank fusion constant: dampens the gap between rank 1 and rank 2
# so neither list (vector, keyword) dominates the merged ranking.
RRF_K = 60


class ChatSearchService:
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

    async def index_messages(self, user_id: str, messages: List[ChatMessageModel]) -> int:
        messages = [message for message in messages if message.content.strip()]
        if not messages:
            return 0

        vectors = await self.embed([message.content for message in messages])
        items = [
            VectorItem(message.id, message.chat_id, user_id, self.embedding_model, vector)
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
            if message.id not in indexed
        ]
        return await self.index_messages(user_id, pending)

    async def search(self, user_id: str, query: str, limit: int = DEFAULT_LIMIT) -> List[ChatSearchHitDTO]:
        query = query.strip()
        if not query:
            return []

        limit = max(1, min(limit, MAX_LIMIT))
        pool = limit * 3

        [query_vector] = await self.embed([query])
        vector_hits = await self.vector_store.query(user_id, query_vector, pool)
        keyword_matches = await self.chat_repository.search_messages_by_keyword(user_id, query, self.providers, pool)

        scores: Dict[str, float] = {}
        for rank, hit in enumerate(vector_hits):
            scores[hit.message_id] = scores.get(hit.message_id, 0.0) + 1 / (RRF_K + rank + 1)
        keyword_ids = {message.id for message in keyword_matches}
        for rank, message in enumerate(keyword_matches):
            scores[message.id] = scores.get(message.id, 0.0) + 1 / (RRF_K + rank + 1)

        top_ids = sorted(scores, key=lambda message_id: scores[message_id], reverse=True)[:limit]
        found = {
            message.id: message for message in await self.chat_repository.get_messages_for_user(user_id, top_ids)
        }

        return [
            self.to_dto(found[message_id], scores[message_id], message_id in keyword_ids)
            for message_id in top_ids
            if message_id in found  # a message deleted since indexing just drops out
        ]

    # --- responses

    @staticmethod
    def to_dto(message: ChatMessageHitModel, score: float, keyword_match: bool) -> ChatSearchHitDTO:
        content = " ".join(message.content.split())
        snippet = content if len(content) <= SNIPPET_LENGTH else content[: SNIPPET_LENGTH - 1].rstrip() + "…"
        chat_href = f"{API_PREFIX}/users/{message.user_id}/chats/{message.chat_id}"
        return ChatSearchHitDTO(
            messageId=message.id,
            chatId=message.chat_id,
            chatTitle=message.chat_title,
            role=message.role,
            snippet=snippet,
            score=round(score, 6),
            keywordMatch=keyword_match,
            created_date=message.created_date,
            links={LINK_CHAT: Link(href=chat_href, method="GET")},
        )

    @staticmethod
    def build_meta_links(user_id: str) -> dict[str, Link]:
        base = f"{API_PREFIX}/users/{user_id}/chats/search"
        return {
            LINK_SEARCH: Link(href=base, method="GET"),
            LINK_REINDEX: Link(href=f"{base}/reindex", method="POST"),
        }

    def build_response(self, user_id: str, hits: List[ChatSearchHitDTO]) -> ChatSearchResponse:
        return ChatSearchResponse.of(HITS_DATA_NAME, hits, NoMetadata(), self.build_meta_links(user_id))

    @staticmethod
    def build_reindex_response(indexed: int) -> ChatReindexResponse:
        return ChatReindexResponse.of(REINDEX_DATA_NAME, ReindexDTO(indexed=indexed), NoMetadata())
