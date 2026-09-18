from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# Enum for todo state
class TodoState(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"


# Request model for creating
class TodoCreate(BaseModel):
    """Model for creating a new TODO"""
    title: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = Field(None)
    complete_by: datetime
    state: TodoState = Field(default=TodoState.NEW)


# Request model for updating
class TodoUpdate(BaseModel):
    """Model for updating a TODO"""
    title: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = Field(None)
    complete_by: Optional[datetime] = None
    state: Optional[TodoState] = None


# Response model
class Todo(BaseModel):
    """Complete TODO object returned by API"""
    id: int
    title: str
    description: Optional[str] = None
    complete_by: datetime
    state: TodoState
    created_date: datetime

    class Config:
        from_attributes = True
