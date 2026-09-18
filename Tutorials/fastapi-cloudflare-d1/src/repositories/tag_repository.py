from typing import Any, Dict, List, Optional


class TagRepository:
    """
    Repository for Tag database operations, backed by a Cloudflare D1 binding.

    D1 has no connection string - it is accessed via a binding object (env.DB)
    injected by the Workers runtime. All methods here are async because every
    D1 call crosses into the Workers runtime asynchronously.

    NOTE: D1's Python binding API is in beta. Row objects returned by
    `.first()` / `.all().results` behave like dicts (`row["id"]`). If the
    exact attribute names differ in your installed `workers-py` version,
    adjust `_get()` below - everything else stays the same.
    """

    def __init__(self, db):
        # `db` is the D1 binding (e.g. env.DB), passed in per-request.
        self.db = db

    @staticmethod
    def _get(row: Any, key: str, default=None):
        """Safely read a field whether the row is dict-like or attribute-like."""
        if row is None:
            return default
        try:
            return row[key]
        except (TypeError, KeyError):
            return getattr(row, key, default)

    async def create(
            self,
            tag: str,
            resource_id: int,
            created_date: str
    ) -> Dict[str, Any]:
        result = await self.db.prepare(
            "INSERT INTO tags (tag, resource_id, created_date) "
            "VALUES (?, ?, ?)"
        ).bind(tag, resource_id, created_date).run()

        new_id = self._get(self._get(result, "meta"), "last_row_id")

        return await self.get_by_id(new_id)

    async def get_all_by_resource_id(self, resource_id: int) -> List[Dict[str, Any]]:
        result = await (self.db.prepare("SELECT * FROM tags WHERE resource_id = ?")
                        .bind(resource_id).all())

        return self._get(result, "results", [])

    async def search_tags(self, term: Optional[str] = None) -> List[Dict[str, Any]]:
        if term:
            result = await self.db.prepare("SELECT * FROM tags WHERE tag LIKE ?").bind(term).all()
        else:
            result = await self.db.prepare("SELECT * FROM tags WHERE resource_id = ?").all()

        return self._get(result, "results", [])

    async def get_all(self) -> List[Dict[str, Any]]:
        result = await (self.db.prepare("SELECT * FROM tags")
                        .all())

        return self._get(result, "results", [])

    async def get_by_id(self, id: int) -> Optional[Dict[str, Any]]:
        row = await self.db.prepare("SELECT * FROM tags WHERE id = ?").bind(id).first()

        return row

    async def delete(self, id: int) -> bool:
        existing = await self.get_by_id(id)

        if not existing:
            return False

        await self.db.prepare("DELETE FROM tags WHERE id = ?").bind(id).run()

        return True
