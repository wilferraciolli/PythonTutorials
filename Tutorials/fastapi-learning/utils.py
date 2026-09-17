from datetime import datetime
from models import Todo, TodoState


class TodoUtils:
    """Utility methods for TODO operations"""

    @staticmethod
    def is_overdue(todo: Todo) -> bool:
        """
        Check if a TODO is overdue.
        A TODO is overdue if:
        - complete_by date has passed AND
        - state is not CLOSED
        """
        now = datetime.now()
        return todo.complete_by < now and todo.state != TodoState.CLOSED

    @staticmethod
    def get_days_until_due(todo: Todo) -> int:
        """Get number of days until TODO is due (negative if overdue)"""
        now = datetime.now()
        delta = todo.complete_by - now
        return delta.days

    @staticmethod
    def is_due_soon(todo: Todo, days: int = 3) -> bool:
        """Check if TODO is due within N days"""
        days_left = TodoUtils.get_days_until_due(todo)
        return 0 <= days_left <= days