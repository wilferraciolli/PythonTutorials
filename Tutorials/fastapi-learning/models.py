from enum import Enum
from datetime import datetime
from pydantic import BaseModel

# Enum for todo state
class TodoState(str, Enum):
    NEW = "NEW"
    ACTIVE = "ACTIVE"
    CLOSED = "CLOSED"

# Request model
class TodoCreate(BaseModel):
    title: str
    description: str
    complete_by: datetime

# Response model
class Todo(TodoCreate):
    id: int
    state: TodoState
    created_date: datetime

    # Pydantic to use with SQLAlchemy and models
    class Config:
        from_attributes = True
