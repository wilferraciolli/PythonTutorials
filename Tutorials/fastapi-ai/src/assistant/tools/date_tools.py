from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Tuple

from assistant.tools.tool import Tool

PERIODS = [
    "today",
    "yesterday",
    "last_7_days",
    "last_30_days",
    "this_week",
    "last_week",
    "this_month",
    "last_month",
    "this_quarter",
    "last_quarter",
    "this_year",
    "last_year",
]


def _quarter_start(day: date) -> date:
    return date(day.year, 3 * ((day.month - 1) // 3) + 1, 1)


def _month_end(first_of_month: date) -> date:
    next_month = (first_of_month.replace(day=28) + timedelta(days=4)).replace(day=1)
    return next_month - timedelta(days=1)


def _add_months(day: date, months: int) -> date:
    index = day.year * 12 + (day.month - 1) + months
    return date(index // 12, index % 12 + 1, 1)


def resolve_period(period: str, today: date) -> Tuple[date, date]:
    """
    Turn a named period into an inclusive (first day, last day) range.

    Calendar quarters (Jan-Mar, Apr-Jun, Jul-Sep, Oct-Dec) and ISO weeks
    (Monday first). Kept in code, not left to the model, so "last quarter"
    means the same thing every time.
    """
    if period == "today":
        return today, today
    if period == "yesterday":
        day = today - timedelta(days=1)
        return day, day
    if period == "last_7_days":
        return today - timedelta(days=6), today
    if period == "last_30_days":
        return today - timedelta(days=29), today
    if period == "this_week":
        start = today - timedelta(days=today.weekday())
        return start, start + timedelta(days=6)
    if period == "last_week":
        start = today - timedelta(days=today.weekday() + 7)
        return start, start + timedelta(days=6)
    if period == "this_month":
        start = today.replace(day=1)
        return start, _month_end(start)
    if period == "last_month":
        start = _add_months(today.replace(day=1), -1)
        return start, _month_end(start)
    if period == "this_quarter":
        start = _quarter_start(today)
        return start, _month_end(_add_months(start, 2))
    if period == "last_quarter":
        start = _add_months(_quarter_start(today), -3)
        return start, _month_end(_add_months(start, 2))
    if period == "this_year":
        return date(today.year, 1, 1), date(today.year, 12, 31)
    if period == "last_year":
        return date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)
    raise ValueError(f"unknown period {period!r}")


def build_date_tools(now: Callable[[], datetime]) -> List[Tool]:
    async def date_range(user_id: str, args: Dict[str, Any]) -> Dict[str, Any]:
        period = args.get("period")
        if period not in PERIODS:
            return {"error": f"period must be one of {PERIODS}"}

        start, end = resolve_period(period, now().astimezone(timezone.utc).date())
        return {"period": period, "from": start.isoformat(), "to": end.isoformat()}

    return [
        Tool(
            name="date_range",
            description=(
                "Convert a relative period such as 'last quarter' or 'this month' into exact "
                "from/to dates (YYYY-MM-DD, inclusive; calendar quarters, weeks start Monday). "
                "ALWAYS call this first for any relative period, then pass its from/to to other "
                "tools (created_from/created_to, due_from/due_to)."
            ),
            parameters={
                "type": "object",
                "properties": {"period": {"type": "string", "enum": PERIODS}},
                "required": ["period"],
            },
            handler=date_range,
        )
    ]
