from typing import Optional

from pydantic import BaseModel, Field

from media.enums import MediaType


class MediaRef(BaseModel):
    """What a client sends: the provider and its id. The server looks up the rest."""
    type: MediaType
    id: str = Field(min_length=1, max_length=100)


class MediaSearchResult(BaseModel):
    """One Unsplash photo or Giphy GIF from a search; send {type, id} back to attach it."""
    type: MediaType
    id: str
    title: Optional[str] = None
    previewUrl: str
    url: str
    authorName: Optional[str] = None
    authorUrl: Optional[str] = None
