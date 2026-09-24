from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from core.ai.schemas import ReindexDTO
from core.common.api_response import ApiResponse
from core.common.base_dto import FieldMetadata, LinkedResource
from core.common.serializers import format_utc_datetime
from todos.enums import TodoState


# --- Request: what the client sends -----------------------------------------

class TodoCreateRequest(BaseModel):
    """
    Body of `POST /users/{user_id}/todos`. Also the `_data` of the create
    template, filled with defaults, so a form starts from the shape it sends.
    """
    title: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = None
    complete_by: datetime
    state: TodoState = TodoState.NEW

    @field_serializer("complete_by")
    def serialize_complete_by(self, value: datetime) -> str:
        return format_utc_datetime(value)


class TodoUpdateRequest(BaseModel):
    """Body of `PUT /users/{user_id}/todos/{todo_id}`. Only the fields sent are changed."""
    title: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = None
    complete_by: Optional[datetime] = None
    state: Optional[TodoState] = None


# --- DTO: what the application services return ------------------------------

class TodoDTO(LinkedResource):
    """A todo plus the links the caller may follow from it."""
    id: str
    user_id: str
    title: str
    description: Optional[str] = None
    complete_by: datetime
    state: TodoState
    created_date: datetime

    @field_serializer("complete_by", "created_date")
    def serialize_datetime(self, value: datetime) -> str:
        return format_utc_datetime(value)


class TodoSearchHitDTO(BaseModel):
    """One todo matching a search, with how well it matched."""
    id: str
    title: str
    description: Optional[str] = None
    state: TodoState
    complete_by: datetime
    score: float
    keywordMatch: bool

    @field_serializer("complete_by")
    def serialize_complete_by(self, value: datetime) -> str:
        return format_utc_datetime(value)


class TodoMetadata(BaseModel):
    """How the client should treat each field of `TodoDTO`."""
    id: FieldMetadata
    user_id: FieldMetadata
    title: FieldMetadata
    complete_by: FieldMetadata
    state: FieldMetadata
    created_date: FieldMetadata


class TodoTemplateMetadata(BaseModel):
    """How the client should treat each field of the create template."""
    title: FieldMetadata
    complete_by: FieldMetadata
    state: FieldMetadata


# --- Response: the envelopes the service builds -----------------------------

TodoResponse = ApiResponse[TodoDTO, TodoMetadata]
TodoListResponse = ApiResponse[list[TodoDTO], TodoMetadata]
TodoSearchResponse = ApiResponse[list[TodoSearchHitDTO], TodoMetadata]
TodoReindexResponse = ApiResponse[ReindexDTO, TodoMetadata]
TodoTemplateResponse = ApiResponse[TodoCreateRequest, TodoTemplateMetadata]
