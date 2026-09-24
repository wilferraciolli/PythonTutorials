from datetime import datetime
from todos.enums import TodoState
from todos.schemas import Todo


class TodoUtils:
    """Utility methods for TODO operations"""

    @staticmethod
    def is_overdue(todo: Todo) -> bool:
        """A TODO is overdue if complete_by has passed and it is not CLOSED."""
        if todo.state == TodoState.CLOSED:
            return False
        return todo.complete_by < datetime.now(todo.complete_by.tzinfo)

    @staticmethod
    def get_days_until_due(todo: Todo) -> int:
        """Days until due (negative if overdue)."""
        now = datetime.now(todo.complete_by.tzinfo)
        return (todo.complete_by - now).days

    @staticmethod
    def is_due_soon(todo: Todo, days: int = 3) -> bool:
        """True if TODO is due within N days and not CLOSED."""
        if todo.state == TodoState.CLOSED:
            return False
        days_left = TodoUtils.get_days_until_due(todo)
        return 0 <= days_left <= days
