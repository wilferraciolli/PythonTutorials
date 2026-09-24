from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_serializer

from core.common.api_response import ApiResponse
from core.common.base_dto import FieldMetadata, LinkedResource
from core.common.serializers import format_utc_datetime
from core.security.roles import UserRole


# --- Request: what the client sends -----------------------------------------

class UserCreateRequest(BaseModel):
    """
    Body of `POST /users`. Also the `_data` of `GET /users/template`, filled
    with defaults, so a create form starts from the same shape it sends.
    """
    name: str
    email: str
    roleIds: list[UserRole] = Field(default_factory=lambda: [UserRole.STANDARD])


class UserUpdateRequest(BaseModel):
    """Body of `PUT /users/{user_id}`. Only the fields sent are changed."""
    name: Optional[str] = None
    email: Optional[str] = None
    roleIds: Optional[list[UserRole]] = None


# --- DTO: what the application service returns ------------------------------

class UserDTO(LinkedResource):
    """A user plus the links the caller may follow from them."""
    id: str
    external_user_id: Optional[str] = None
    name: str
    email: str
    roleIds: list[UserRole]
    created_date: datetime

    @field_serializer("created_date")
    def serialize_created_date(self, value: datetime) -> str:
        return format_utc_datetime(value)


class UserMetadata(BaseModel):
    """How the client should treat each field of `UserDTO`."""
    id: FieldMetadata
    external_user_id: FieldMetadata
    name: FieldMetadata
    email: FieldMetadata
    roleIds: FieldMetadata
    created_date: FieldMetadata


class UserTemplateMetadata(BaseModel):
    """How the client should treat each field of the create template."""
    name: FieldMetadata
    email: FieldMetadata
    roleIds: FieldMetadata


# --- Response: the envelopes the service builds -----------------------------

UserResponse = ApiResponse[UserDTO, UserMetadata]
UserListResponse = ApiResponse[list[UserDTO], UserMetadata]
UserTemplateResponse = ApiResponse[UserCreateRequest, UserTemplateMetadata]
