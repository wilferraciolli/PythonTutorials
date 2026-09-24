from typing import Optional

from pydantic import BaseModel

from core.common.serializers import UtcDateTime
from todos.enums import TodoState


class TodoModel(BaseModel):
    """A `todos` database row."""
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    complete_by: UtcDateTime
    state: TodoState
    created_date: UtcDateTime


class TodoTagCountModel(BaseModel):
    """A tag on a user's todos, with how many of their todos carry it."""
    tag: str
    count: int
