from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from assistant.tools import Tool
from repositories.todo_repository import TodoRepository

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
        "description": "true = only todos past their complete_by date that are not CLOSED. Omit for no date filter.",
    },
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _parse(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def build_todo_tools(repository: TodoRepository, now: Callable[[], datetime] = utc_now) -> List[Tool]:
    async def _filtered(user_id: str, args: Dict[str, Any]) -> List[Dict[str, Any]] | Dict[str, str]:
        state: Optional[str] = args.get("state")
        if state is not None and state not in STATES:
            return {"error": f"state must be one of {STATES}"}

        rows = await repository.list_for_user(user_id)
        if state:
            rows = [row for row in rows if row["state"] == state]
        if args.get("overdue") is True:
            current = now()
            rows = [row for row in rows if row["state"] != "CLOSED" and _parse(row["complete_by"]) < current]
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
                {"title": r["title"], "state": r["state"], "complete_by": r["complete_by"]}
                for r in rows[:limit]
            ],
        }

    return [
        Tool(
            name="count_todos",
            description="Count the user's todos, optionally by state and/or only overdue ones.",
            parameters={"type": "object", "properties": dict(_FILTERS)},
            handler=count_todos,
        ),
        Tool(
            name="list_todos",
            description=(
                "List the user's todos (title, state, due date), earliest due first. "
                "Optionally by state and/or only overdue."
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
    ]
