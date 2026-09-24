from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from core.common.base_dto import LinkedResource
from core.common.serializers import format_utc_datetime
from todos.enums import TodoState


class TodoCreate(BaseModel):
    """Model for creating a new TODO"""
    title: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = Field(None)
    complete_by: datetime
    state: TodoState = Field(default=TodoState.NEW)


class TodoUpdate(BaseModel):
    """Model for updating a TODO"""
    title: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = Field(None)
    complete_by: Optional[datetime] = None
    state: Optional[TodoState] = None


class Todo(LinkedResource):
    """Complete TODO object returned by API"""
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    complete_by: datetime
    state: TodoState
    created_date: datetime

    class Config:
        from_attributes = True

    @field_serializer("complete_by", "created_date")
    def serialize_datetime(self, value: datetime) -> str:
        return format_utc_datetime(value)
