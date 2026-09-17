from enum import Enum
from datetime import datetime
from pydantic import BaseModel

# Enum for todo state
class TodoState(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"

# Request model for crating
class TodoCreate(BaseModel):
    title: str
    description: str
    complete_by: datetime
    state: TodoState = TodoState.NEW

# Request model for updateing
class TodoUpdate(BaseModel):
    title: str
    description: str
    complete_by: datetime
    state: TodoState

# Response model
class Todo(TodoCreate):
    id: int
    state: TodoState
    created_date: datetime

    # Pydantic to use with SQLAlchemy and models
    class Config:
        from_attributes = True
