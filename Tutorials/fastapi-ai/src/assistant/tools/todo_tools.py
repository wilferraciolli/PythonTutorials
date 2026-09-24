from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from assistant.tools.tool import Tool
from todos.todo_repository import TodoRepository
from todos.todo_search_service import TodoSearchService

STATES = ["NEW", "ACTIVE", "CLOSED"]
MAX_LIST = 50

_FILTERS = {
    "state": {
        "type": "string",
        "enum": STATES,
        "description": "Only todos in this state. Omit for any state.",
    },
    "overdue": {
        "type": "boolean",
        "description": "true = only todos past their complete_by date that are not CLOSED. Omit for no filter.",
    },
    "tag": {
        "type": "string",
        "description": "Only todos carrying this tag, e.g. 'important' (case-insensitive). Use list_tags to see the tags.",
    },
    "created_from": {"type": "string", "description": "Only todos created on/after this date (YYYY-MM-DD)."},
    "created_to": {"type": "string", "description": "Only todos created on/before this date (YYYY-MM-DD)."},
    "due_from": {"type": "string", "description": "Only todos due on/after this date (YYYY-MM-DD)."},
    "due_to": {"type": "string", "description": "Only todos due on/before this date (YYYY-MM-DD)."},
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _day_start(value: str) -> datetime:
    day = date.fromisoformat(value)
    return datetime(day.year, day.month, day.day, tzinfo=timezone.utc)


def build_todo_tools(
    repository: TodoRepository,
    now: Callable[[], datetime] = utc_now,
    search: Optional[TodoSearchService] = None,
) -> List[Tool]:
    async def _filtered(user_id: str, args: Dict[str, Any]) -> List[Dict[str, Any]] | Dict[str, str]:
        state: Optional[str] = args.get("state")
        if state is not None and state not in STATES:
            return {"error": f"state must be one of {STATES}"}

        try:
            created_from = _day_start(args["created_from"]) if args.get("created_from") else None
            # "to" dates are inclusive, so compare against the start of the next day.
            created_to = _day_start(args["created_to"]) + timedelta(days=1) if args.get("created_to") else None
            due_from = _day_start(args["due_from"]) if args.get("due_from") else None
            due_to = _day_start(args["due_to"]) + timedelta(days=1) if args.get("due_to") else None
        except ValueError:
            return {"error": "dates must be YYYY-MM-DD"}

        rows = await repository.list_for_user(user_id)

        if state:
            rows = [row for row in rows if row["state"] == state]
        if args.get("overdue") is True:
            current = now()
            rows = [row for row in rows if row["state"] != "CLOSED" and _parse(row["complete_by"]) < current]
        if args.get("tag"):
            tagged = await repository.ids_with_tag(user_id, str(args["tag"]))
            rows = [row for row in rows if row["id"] in tagged]
        if created_from:
            rows = [row for row in rows if _parse(row["created_date"]) >= created_from]
        if created_to:
            rows = [row for row in rows if _parse(row["created_date"]) < created_to]
        if due_from:
            rows = [row for row in rows if _parse(row["complete_by"]) >= due_from]
        if due_to:
            rows = [row for row in rows if _parse(row["complete_by"]) < due_to]
        return rows

    async def count_todos(user_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        rows = await _filtered(user_id, args)
        if isinstance(rows, dict):
            return rows
        return {"count": len(rows)}

    async def list_todos(user_id: str, args: Dict[str, Any]) -> Any:
        rows = await _filtered(user_id, args)
        if isinstance(rows, dict):
            return rows

        limit = max(1, min(int(args.get("limit") or 10), MAX_LIST))
        return {
            "total": len(rows),
            "todos": [
                {
                    "title": r["title"],
                    "state": r["state"],
                    "complete_by": r["complete_by"],
                    "created_date": r["created_date"],
                }
                for r in rows[:limit]
            ],
        }

    async def list_tags(user_id: str, args: Dict[str, Any]) -> Any:
        return {"tags": await repository.tag_counts(user_id)}

    tools = [
        Tool(
            name="count_todos",
            description=(
                "Count the user's todos. Combine any filters: state, overdue, tag, created and due "
                "date ranges. For relative periods ('last quarter') call date_range first."
            ),
            parameters={"type": "object", "properties": dict(_FILTERS)},
            handler=count_todos,
        ),
        Tool(
            name="list_todos",
            description=(
                "List the user's todos (title, state, due and created dates), earliest due first. "
                "Same filters as count_todos."
            ),
            parameters={
                "type": "object",
                "properties": {
                    **_FILTERS,
                    "limit": {"type": "integer", "description": f"Max todos to return (default 10, max {MAX_LIST})."},
                },
            },
            handler=list_todos,
        ),
        Tool(
            name="list_tags",
            description="List the tags the user's todos carry, with how many todos have each.",
            parameters={"type": "object", "properties": {}},
            handler=list_tags,
        ),
    ]

    if search:

        async def search_todos(user_id: str, args: Dict[str, Any]) -> Any:
            query = str(args.get("query") or "").strip()
            if not query:
                return {"error": "query is required"}
            if args.get("state") is not None and args["state"] not in STATES:
                return {"error": f"state must be one of {STATES}"}

            matches = await search.search(user_id, query, args.get("state"), int(args.get("limit") or 5))
            return {
                "matches": [
                    {k: m[k] for k in ("title", "description", "state", "complete_by")} for m in matches
                ]
            }

        tools.append(
            Tool(
                name="search_todos",
                description=(
                    "Find todos by what they are ABOUT (meaning of title/description), e.g. 'the tax "
                    "return' or 'anything related to the garden'. Use count_todos/list_todos instead "
                    "for counts, states, dates and tags."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "What the todos are about."},
                        "state": {"type": "string", "enum": STATES},
                        "limit": {"type": "integer", "description": "Max matches (default 5)."},
                    },
                    "required": ["query"],
                },
                handler=search_todos,
            )
        )

    return tools
