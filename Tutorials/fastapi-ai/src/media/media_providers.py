import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

import httpx

from core.common.errors import AppError, NotConfiguredError, UpstreamError
from media.enums import MediaType
from media.schemas import MediaRef, MediaSearchResult

logger = logging.getLogger(__name__)

UNSPLASH_API = "https://api.unsplash.com"
# Every Giphy GIF is served at these addresses by id, no key needed. The still
# (a few KB) is what the server fetches to check the id exists; posts show the webp.
GIPHY_MEDIA = "https://media.giphy.com/media/{id}/giphy.webp"
GIPHY_STILL = "https://media.giphy.com/media/{id}/200_s.gif"
# Unsplash's guidelines ask for these on every link back to them.
UTM = "utm_source=wiltech&utm_medium=referral"
YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
PROVIDER_ID = re.compile(r"^[A-Za-z0-9_-]+$")


@dataclass
class ResolvedMedia:
    """The posts.media_* columns for one piece of media."""

    type: MediaType
    id: str
    url: Optional[str] = None
    title: Optional[str] = None  # alt text
    author_name: Optional[str] = None
    author_url: Optional[str] = None


class MediaLookup(Protocol):
    async def search_unsplash(self, query: str, limit: int) -> List[MediaSearchResult]: ...

    async def resolve(self, ref: MediaRef) -> ResolvedMedia: ...


class MediaProviders:
    """
    Turns the {type, id} a client sends into what a post stores, so nobody can put
    an arbitrary URL on a post:

    - Unsplash: searched here (the access key stays on the server); attaching a
      photo looks it up for its URL and photographer.
    - Giphy: searched in the browser with Giphy's client key. Here the id is only
      checked (a keyless GET of the GIF's small still image) and the URL built from it.
    - YouTube: no call at all, the id is checked against the 11-character format.
    """

    def __init__(self, unsplash_key: Optional[str], transport: Optional[httpx.AsyncBaseTransport] = None) -> None:
        self.unsplash_key = unsplash_key or None
        self.transport = transport  # tests pass an httpx.MockTransport

    async def search_unsplash(self, query: str, limit: int) -> List[MediaSearchResult]:
        data = await self._unsplash("/search/photos", {"query": query, "per_page": limit})
        return [self._unsplash_result(photo) for photo in data.get("results", [])]

    async def resolve(self, ref: MediaRef) -> ResolvedMedia:
        media_id = ref.id.strip()
        if ref.type == MediaType.YOUTUBE:
            if not YOUTUBE_ID.match(media_id):
                raise AppError("A YouTube video id is the 11 characters after watch?v=")
            return ResolvedMedia(MediaType.YOUTUBE, media_id)
        if not PROVIDER_ID.match(media_id):  # it goes into the provider's URL path
            raise AppError(f"Not a valid {ref.type.value.title()} id")

        if ref.type == MediaType.GIPHY:
            # GET, not HEAD: the Python Workers HTTP layer fails on body-less HEAD replies.
            await self._request("GET", GIPHY_STILL.format(id=media_id), {}, {}, "Giphy", missing="Unknown Giphy GIF")
            return ResolvedMedia(MediaType.GIPHY, media_id, GIPHY_MEDIA.format(id=media_id))

        photo = await self._unsplash(f"/photos/{media_id}", {}, missing="Unknown Unsplash photo")
        # Unsplash API requirement: track a download whenever a photo is picked for
        # use, by calling its links.download_location with our key. Done here (the
        # photo is being attached to a post), so the key never goes to the browser.
        download = (photo.get("links") or {}).get("download_location")
        if download:
            await self._request("GET", download, {}, self._unsplash_headers(), "Unsplash")
        result = self._unsplash_result(photo)
        return ResolvedMedia(
            MediaType.UNSPLASH, result.id, result.url, result.title, result.authorName, result.authorUrl
        )

    # --- Unsplash

    def _unsplash_headers(self) -> Dict[str, str]:
        if not self.unsplash_key:
            raise NotConfiguredError("Unsplash isn't set up (UNSPLASH_ACCESS_KEY)")
        return {"Authorization": f"Client-ID {self.unsplash_key}", "Accept-Version": "v1"}

    async def _unsplash(self, path: str, params: Dict[str, Any], missing: Optional[str] = None) -> Dict[str, Any]:
        response = await self._request(
            "GET", f"{UNSPLASH_API}{path}", params, self._unsplash_headers(), "Unsplash", missing
        )
        return response.json()

    @staticmethod
    def _unsplash_result(photo: Dict[str, Any]) -> MediaSearchResult:
        urls = photo.get("urls") or {}
        user = photo.get("user") or {}
        profile = (user.get("links") or {}).get("html")
        return MediaSearchResult(
            type=MediaType.UNSPLASH,
            id=photo["id"],
            title=photo.get("alt_description") or photo.get("description"),
            previewUrl=urls.get("small") or urls.get("thumb") or urls.get("regular", ""),
            url=urls.get("regular") or urls.get("full", ""),
            authorName=user.get("name"),
            authorUrl=f"{profile}?{UTM}" if profile else None,
        )

    # --- HTTP

    async def _request(
        self,
        method: str,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, str],
        provider: str,
        missing: Optional[str] = None,
    ) -> httpx.Response:
        try:
            async with httpx.AsyncClient(timeout=10, transport=self.transport) as client:
                response = await client.request(method, url, params=params, headers=headers)
        except Exception as exc:
            # Not only httpx.HTTPError: in a Python Worker, fetch failures can surface
            # as other exception types, and they must be a 502, never an unhandled 500.
            logger.warning("%s request failed: %s %s: %r", provider, method, url.split("?")[0], exc)
            raise UpstreamError(f"{provider} didn't respond") from exc
        if response.status_code in (400, 403, 404) and missing:  # the id doesn't exist
            raise AppError(missing)
        if response.status_code >= 400:
            raise UpstreamError(f"{provider} returned {response.status_code}")
        return response
