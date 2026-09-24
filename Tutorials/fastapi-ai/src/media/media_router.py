from typing import Any

from fastapi import APIRouter, Depends, Query

from core.common.api_response import envelope
from media.media_providers import MediaProviders
from fastapi import Request

from core.config.config import get_config

# Unsplash search for the media picker: the server holds the access key.
# (Giphy is searched straight from the browser; YouTube needs no search.)
# The picked {type, id} goes to a post's create or .../media endpoint.
router = APIRouter(prefix="/media", tags=["media"])

MAX_RESULTS = 30


def get_media_providers(request: Request) -> MediaProviders:
    """Post media lookups with the server's Unsplash key (Unsplash routes answer 503 without it)."""
    return MediaProviders(get_config(request, "UNSPLASH_ACCESS_KEY"))


@router.get("/unsplash/search")
async def search_unsplash(
    q: str = Query(min_length=1, max_length=100),
    limit: int = Query(20, ge=1, le=MAX_RESULTS),
    providers: MediaProviders = Depends(get_media_providers),
) -> dict[str, Any]:
    results = await providers.search_unsplash(q.strip(), limit)
    return envelope(data_name="media", data=results, metadata={}, meta_links={})
