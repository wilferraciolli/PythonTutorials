from typing import Any, Dict, List, Optional

from models import Link


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
