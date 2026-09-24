from typing import Optional

from pydantic import BaseModel

from core.common.api_response import ApiResponse
from core.common.base_dto import FieldMetadata, LinkedResource
from core.security.roles import UserRole


# --- DTO: what the application services return ------------------------------

class MeDTO(LinkedResource):
    """The signed-in user, plus the `userProfile` link the UI starts from."""
    id: str
    name: str
    email: Optional[str] = None
    roleIds: list[UserRole]


class MeMetadata(BaseModel):
    """How the client should treat each field of `MeDTO`."""
    id: FieldMetadata
    name: FieldMetadata
    email: FieldMetadata
    roleIds: FieldMetadata


class UserProfileDTO(LinkedResource):
    """A user as seen from the profile page, plus every link the UI follows."""
    id: str
    externalId: Optional[str] = None
    name: str
    email: Optional[str] = None
    roleIds: list[UserRole]


class UserProfileMetadata(BaseModel):
    """How the client should treat each field of `UserProfileDTO`."""
    id: FieldMetadata
    name: FieldMetadata
    roleIds: FieldMetadata


# --- Response: the envelopes the services build -----------------------------

MeResponse = ApiResponse[MeDTO, MeMetadata]
UserProfileResponse = ApiResponse[UserProfileDTO, UserProfileMetadata]
