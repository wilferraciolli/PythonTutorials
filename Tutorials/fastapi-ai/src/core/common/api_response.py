from typing import Any, Dict, List, Optional

from core.common.base_dto import Link

# Must match the prefix main.py mounts every router under, so hrefs built
# here are actually followable rather than 404ing against the unprefixed path.
API_PREFIX = "/api"


def envelope(
    data_name: str,
    data: Any,
    metadata: Dict[str, Any],
    meta_links: Optional[Dict[str, Link]] = None,
    messages: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Wrap endpoint payloads in the API's standard response shape."""
    response = {
        "_data": {
            data_name: data,
        },
        "_metadata": metadata,
        "_metaLinks": meta_links or {},
    }

    if messages:
        response["_messages"] = messages

    return response
