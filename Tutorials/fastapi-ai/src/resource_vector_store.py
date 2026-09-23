import json

from database import Database
from vector_store import normalise


class ResourceVectorStore:
    """
    Vectors for one kind of resource (`resource_type`, e.g. "todo") in the
    shared `resource_embeddings` table. Same brute-force cosine as
    DatabaseVectorStore, scoped to one user; a new searchable resource is a
    new `resource_type`, not a new table.
    """

    def __init__(self, db: Database, resource_type: str) -> None:
        self.db = db
        self.resource_type = resource_type

    async def upsert(self, resource_id: str, user_id: str, model: str, vector: list[float], created_date: str) -> None:
        await self.db.execute(
            "INSERT OR REPLACE INTO resource_embeddings "
            "(resource_type, resource_id, user_id, model, embedding, created_date) VALUES (?, ?, ?, ?, ?, ?)",
            (self.resource_type, resource_id, user_id, model, json.dumps(normalise(vector)), created_date),
        )

    async def query(self, user_id: str, vector: list[float], limit: int) -> list[tuple[str, float]]:
        # user_id is always part of the query: it is the tenancy boundary.
        rows = await self.db.fetch_all(
            "SELECT resource_id, embedding FROM resource_embeddings WHERE resource_type = ? AND user_id = ?",
            (self.resource_type, user_id),
        )
        query_vector = normalise(vector)
        scored = [
            (row["resource_id"], sum(a * b for a, b in zip(query_vector, json.loads(row["embedding"]))))
            for row in rows
        ]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored[:limit]

    async def delete(self, resource_id: str) -> None:
        await self.db.execute(
            "DELETE FROM resource_embeddings WHERE resource_type = ? AND resource_id = ?",
            (self.resource_type, resource_id),
        )

    async def indexed_ids(self, user_id: str) -> set[str]:
        rows = await self.db.fetch_all(
            "SELECT resource_id FROM resource_embeddings WHERE resource_type = ? AND user_id = ?",
            (self.resource_type, user_id),
        )
        return {row["resource_id"] for row in rows}
