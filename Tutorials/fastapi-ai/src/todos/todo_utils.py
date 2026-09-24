from datetime import datetime, timezone

from todos.enums import TodoState
from todos.models import TodoModel


class TodoUtils:
    """Date rules for todos."""

    @staticmethod
    def is_overdue(todo: TodoModel) -> bool:
        """A todo is overdue if complete_by has passed and it is not CLOSED."""
        if todo.state == TodoState.CLOSED:
            return False
        return todo.complete_by < datetime.now(timezone.utc)

    @staticmethod
    def get_days_until_due(todo: TodoModel) -> int:
        """Days until due (negative if overdue)."""
        return (todo.complete_by - datetime.now(timezone.utc)).days

    @staticmethod
    def is_due_soon(todo: TodoModel, days: int = 3) -> bool:
        """True if the todo is due within N days and not CLOSED."""
        if todo.state == TodoState.CLOSED:
            return False
        return 0 <= TodoUtils.get_days_until_due(todo) <= days
