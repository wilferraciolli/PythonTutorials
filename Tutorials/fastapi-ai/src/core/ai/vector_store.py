import json
import math
from typing import Protocol

from core.config.database import Database


class VectorItem:
    """One vector to store, with the metadata search filters/results need."""

    def __init__(self, message_id: str, chat_id: str, user_id: str, model: str, vector: list[float]) -> None:
        self.message_id = message_id
        self.chat_id = chat_id
        self.user_id = user_id
        self.model = model
        self.vector = vector


class VectorHit:
    def __init__(self, message_id: str, chat_id: str, score: float) -> None:
        self.message_id = message_id
        self.chat_id = chat_id
        self.score = score


class VectorStore(Protocol):
    """
    Portable vector storage, same idea as Database/AI: the search service
    doesn't know where the vectors live. DatabaseVectorStore is the default;
    a Cloudflare Vectorize adapter can implement this same protocol.
    """

    async def upsert(self, items: list[VectorItem], created_date: str) -> None: ...

    async def query(self, user_id: str, vector: list[float], limit: int) -> list[VectorHit]: ...

    async def delete_by_chat(self, chat_id: str) -> None: ...

    async def indexed_message_ids(self, user_id: str) -> set[str]: ...


def normalise(vector: list[float]) -> list[float]:
    length = math.sqrt(sum(value * value for value in vector))
    return [value / length for value in vector] if length else vector


class DatabaseVectorStore:
    """
    Stores vectors in the `message_embeddings` table and ranks them in
    Python (brute-force cosine over one user's rows). Works on SQLite and
    D1 with no extra infrastructure; fine for thousands of messages per
    user. Swap in Vectorize behind VectorStore when that stops being true.
    """

    def __init__(self, db: Database) -> None:
        self.db = db

    async def upsert(self, items: list[VectorItem], created_date: str) -> None:
        for item in items:
            await self.db.execute(
                "INSERT OR REPLACE INTO message_embeddings "
                "(message_id, chat_id, user_id, model, embedding, created_date) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    item.message_id,
                    item.chat_id,
                    item.user_id,
                    item.model,
                    json.dumps(normalise(item.vector)),
                    created_date,
                ),
            )

    async def query(self, user_id: str, vector: list[float], limit: int) -> list[VectorHit]:
        # user_id is always part of the query: it is the tenancy boundary.
        rows = await self.db.fetch_all(
            "SELECT message_id, chat_id, embedding FROM message_embeddings WHERE user_id = ?",
            (user_id,),
        )

        query_vector = normalise(vector)
        hits = [
            VectorHit(row["message_id"], row["chat_id"], _dot(query_vector, json.loads(row["embedding"])))
            for row in rows
        ]
        hits.sort(key=lambda hit: hit.score, reverse=True)
        return hits[:limit]

    async def delete_by_chat(self, chat_id: str) -> None:
        await self.db.execute("DELETE FROM message_embeddings WHERE chat_id = ?", (chat_id,))

    async def indexed_message_ids(self, user_id: str) -> set[str]:
        rows = await self.db.fetch_all(
            "SELECT message_id FROM message_embeddings WHERE user_id = ?", (user_id,)
        )
        return {row["message_id"] for row in rows}


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))

