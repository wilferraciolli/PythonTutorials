from typing import Any, Dict, List, Optional

from core.config.database import Database

class SettingRepository:
    """
    Repository for Coonfiguration Setting database operations.

    This repository depends on the portable Database protocol, not SQLite,
    Cloudflare D1, or any other concrete database runtime.
    """

    def __init__(self, db: Database) -> None:
        self.db = db


async def get_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
    user = await self.db.fetch_one(
        "SELECT * FROM users WHERE id = ?",
        (user_id,),
    )

    if not user:
        return None

    user["roleIds"] = await self.get_role_ids(user_id)
    return user