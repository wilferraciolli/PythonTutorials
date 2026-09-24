from typing import Any, Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from core.common.base_dto import Link, Message

# Must match the prefix main.py mounts every router under, so hrefs built
# here are actually followable rather than 404ing against the unprefixed path.
API_PREFIX = "/api"

DataT = TypeVar("DataT")
MetadataT = TypeVar("MetadataT")


class ApiResponse(BaseModel, Generic[DataT, MetadataT]):
    """
    The API's standard response envelope, typed per resource:
    `ApiResponse[UserSettingsDTO, UserSettingsMetadata]`.

    `_data` holds a single named entry, e.g. `{"userSettings": {...}}`.
    Build it with `ApiResponse.of(...)` rather than the constructor.
    """
    model_config = ConfigDict(populate_by_name=True)

    data: Dict[str, DataT] = Field(alias="_data")
    metadata: MetadataT = Field(alias="_metadata")
    meta_links: Dict[str, Link] = Field(default_factory=dict, alias="_metaLinks")
    messages: List[Message] = Field(default_factory=list, alias="_messages")

    @classmethod
    def of(
            cls,
            data_name: str,
            data: DataT,
            metadata: MetadataT,
            meta_links: Optional[Dict[str, Link]] = None,
            messages: Optional[List[Message]] = None,
    ) -> "ApiResponse[DataT, MetadataT]":
        return cls(
            data={data_name: data},
            metadata=metadata,
            meta_links=meta_links or {},
            messages=messages or [],
        )


def envelope(
    data_name: str,
    data: Any,
    metadata: Dict[str, Any],
    meta_links: Optional[Dict[str, Link]] = None,
    messages: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Untyped envelope, kept only until every domain builds an ApiResponse."""
    return {
        "_data": {data_name: data},
        "_metadata": metadata,
        "_metaLinks": meta_links or {},
        "_messages": messages or [],
    }
