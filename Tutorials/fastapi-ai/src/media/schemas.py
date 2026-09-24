from typing import Optional

from pydantic import BaseModel, Field

from core.common.api_response import ApiResponse
from core.common.base_dto import NoMetadata
from media.enums import MediaType


# --- Request: what the client sends -----------------------------------------

class MediaRefRequest(BaseModel):
    """What a client sends to attach media: the provider and its id. The server looks up the rest."""
    type: MediaType
    id: str = Field(min_length=1, max_length=100)


# --- DTO: what the service returns ------------------------------------------

class MediaSearchResultDTO(BaseModel):
    """One Unsplash photo from a search; send {type, id} back to attach it."""
    type: MediaType
    id: str
    title: Optional[str] = None
    previewUrl: str
    url: str
    authorName: Optional[str] = None
    authorUrl: Optional[str] = None


# --- Response: the envelope the service builds ------------------------------

MediaSearchResponse = ApiResponse[list[MediaSearchResultDTO], NoMetadata]
