from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel, Field, SerializerFunctionWrapHandler, model_serializer


# Shared HATEOAS-style link, reused by any response DTO
class Link(BaseModel):
    """A single navigation link describing a related action on a resource."""
    href: str
    method: str = "GET"


class MessageType(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class Message(BaseModel):
    """One entry in `_messages`: something useful to tell the client or user."""
    type: MessageType
    value: str


class EmbeddedRef(BaseModel):
    """
    An embedded reference to another resource — `id` plus its display
    `value` — so a client can render a human-readable name without a
    second round trip to look it up. Same `id`/`value` shape the API
    already uses for metadata option lists (e.g. Todo's `state` values).
    """
    id: str
    value: str


class FieldMetadata(BaseModel):
    """
    Describes how a client should treat one field of a resource: whether it
    is read-only, hidden or mandatory, the allowed `values` for a choice
    field, and size limits (`maxLength` for text, `maxItems` for lists,
    `min`/`max`/`default` for numbers). Unset flags are omitted from the
    response.
    """
    readOnly: Optional[bool] = None
    hidden: Optional[bool] = None
    mandatory: Optional[bool] = None
    maxLength: Optional[int] = None
    maxItems: Optional[int] = None
    min: Optional[int] = None
    max: Optional[int] = None
    default: Optional[int] = None
    values: Optional[list[EmbeddedRef]] = None

    @model_serializer(mode="wrap")
    def _omit_unset_flags(self, handler: SerializerFunctionWrapHandler):
        return {key: value for key, value in handler(self).items() if value is not None}


class NoMetadata(BaseModel):
    """`_metadata` for a response whose fields have no client rules: `{}`."""


class LinkedResource(BaseModel):
    """
    Base class adding a `links` map to any response DTO.

    Any model that inherits this gets a `links: Dict[str, Link]` field for free,
    so the same Link shape/behavior is shared across Todo, Tag, and any
    future resource - no copy-pasting the field definition each time.
    """
    links: Dict[str, Link] = Field(default_factory=dict)
