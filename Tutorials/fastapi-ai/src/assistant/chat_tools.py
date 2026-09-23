from typing import Any, Dict, List

from assistant.tools import Tool
from services.search_service import SearchService


def build_chat_tools(search: SearchService) -> List[Tool]:
    async def search_chats(user_id: str, args: Dict[str, Any]) -> Any:
        query = str(args.get("query") or "").strip()
        if not query:
            return {"error": "query is required"}

        hits = await search.search(user_id, query, int(args.get("limit") or 5))
        return {
            "matches": [
                {
                    "chat_title": hit.chatTitle,
                    "role": hit.role.value,
                    "date": hit.created_date.isoformat(),
                    "snippet": hit.snippet,
                }
                for hit in hits
            ]
        }

    return [
        Tool(
            name="search_chats",
            description=(
                "Search the user's past AI chat conversations by meaning and keyword, "
                "for example 'where did I ask about java'. Returns the best matching messages."
            ),
            parameters={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to look for."},
                    "limit": {"type": "integer", "description": "Max matches (default 5)."},
                },
                "required": ["query"],
            },
            handler=search_chats,
        )
    ]
