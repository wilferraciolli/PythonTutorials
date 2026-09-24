"""
Post media: one Unsplash photo, Giphy GIF or YouTube video per post
(docs/social-groups.md "Post media"). Unsplash and Giphy's media host are faked
with an httpx.MockTransport, so the real request building and parsing run.
"""
import httpx
import pytest
from fastapi.testclient import TestClient

from core.security.auth import AuthenticatedUser, get_authenticated_user
from core.common.errors import AppError, ForbiddenError, NotConfiguredError, UpstreamError
from media.media_providers import MediaProviders
from groups.posts.schemas import PostCreateRequest
from media.enums import MediaType
from media.schemas import MediaRefRequest
from social import MEMBER, OWNER, make_social

PHOTO = {
    "id": "abc123",
    "alt_description": "a red bike",
    "urls": {"small": "https://images.unsplash.com/small", "regular": "https://images.unsplash.com/regular"},
    "user": {"name": "Ana Lens", "links": {"html": "https://unsplash.com/@ana"}},
    "links": {"download_location": "https://api.unsplash.com/photos/abc123/download"},
}
GIF_URL = "https://media.giphy.com/media/gif42/giphy.webp"


class FakeProviders:
    """Records what was called and answers like Unsplash and Giphy's media host do."""

    def __init__(self):
        self.calls = []

    def handler(self, request: httpx.Request) -> httpx.Response:
        self.calls.append(request)
        path = request.url.path
        if request.url.host == "media.giphy.com":
            # a keyless GET of the small still (HEAD fails in Python Workers)
            assert request.method == "GET" and "api_key" not in request.url.params
            return httpx.Response(200 if path == "/media/gif42/200_s.gif" else 403)
        assert request.headers["Authorization"] == "Client-ID unsplash-key"
        if path == "/search/photos":
            return httpx.Response(200, json={"results": [PHOTO]})
        if path == "/photos/abc123":
            return httpx.Response(200, json=PHOTO)
        if path == "/photos/abc123/download":
            return httpx.Response(200, json={"url": "..."})
        return httpx.Response(404, json={"errors": ["Couldn't find Photo"]})

    def providers(self, unsplash="unsplash-key") -> MediaProviders:
        return MediaProviders(unsplash, transport=httpx.MockTransport(self.handler))


@pytest.fixture
def fake():
    return FakeProviders()


@pytest.fixture
async def s(tmp_path, fake):
    return await make_social(tmp_path, fake.providers())


# --- providers


async def test_search_unsplash(fake):
    [photo] = await fake.providers().search_unsplash("bike", 5)
    assert photo.id == "abc123" and photo.url.endswith("/regular") and photo.previewUrl.endswith("/small")
    assert photo.authorName == "Ana Lens"
    assert photo.authorUrl == "https://unsplash.com/@ana?utm_source=wiltech&utm_medium=referral"
    assert fake.calls[0].url.params["per_page"] == "5"


async def test_unsplash_without_a_key_says_so(fake):
    with pytest.raises(NotConfiguredError):
        await fake.providers(unsplash=None).search_unsplash("bike", 5)
    with pytest.raises(NotConfiguredError):
        await fake.providers(unsplash="").resolve(MediaRefRequest(type=MediaType.UNSPLASH, id="abc123"))


async def test_giphy_and_youtube_need_no_key(fake):
    providers = fake.providers(unsplash=None)
    gif = await providers.resolve(MediaRefRequest(type=MediaType.GIPHY, id="gif42"))
    assert (gif.type, gif.id, gif.url) == (MediaType.GIPHY, "gif42", GIF_URL)

    video = await providers.resolve(MediaRefRequest(type=MediaType.YOUTUBE, id="dQw4w9WgXcQ"))
    assert (video.id, video.url) == ("dQw4w9WgXcQ", None)
    assert [c.url.host for c in fake.calls] == ["media.giphy.com"]  # YouTube is never called


async def test_any_fetch_failure_is_a_502_not_a_crash():
    # In a Worker a failed fetch may not be an httpx.HTTPError; it must still be a clean 502.
    def explode(request):
        raise RuntimeError("JsException: fetch failed")

    providers = MediaProviders("key", transport=httpx.MockTransport(explode))
    with pytest.raises(UpstreamError) as err:
        await providers.resolve(MediaRefRequest(type=MediaType.GIPHY, id="gif42"))
    assert err.value.status_code == 502


async def test_attaching_an_unsplash_photo_tracks_the_download(fake):
    media = await fake.providers().resolve(MediaRefRequest(type=MediaType.UNSPLASH, id="abc123"))
    assert (media.type, media.id, media.title) == (MediaType.UNSPLASH, "abc123", "a red bike")
    assert (media.author_name, media.author_url) == (
        "Ana Lens",
        "https://unsplash.com/@ana?utm_source=wiltech&utm_medium=referral",
    )
    # the photo lookup, then a GET on its download_location with our key (checked by the fake)
    assert [(c.method, str(c.url)) for c in fake.calls] == [
        ("GET", "https://api.unsplash.com/photos/abc123"),
        ("GET", "https://api.unsplash.com/photos/abc123/download"),
    ]


async def test_searching_unsplash_does_not_track_downloads(fake):
    await fake.providers().search_unsplash("bike", 5)
    assert [c.url.path for c in fake.calls] == ["/search/photos"]


async def test_unknown_or_malformed_ids_are_rejected(fake):
    providers = fake.providers()
    for ref in (
        MediaRefRequest(type=MediaType.UNSPLASH, id="nope"),
        MediaRefRequest(type=MediaType.GIPHY, id="nope"),
        MediaRefRequest(type=MediaType.YOUTUBE, id="https://youtu.be/dQw4w9WgXcQ"),  # the id, not a URL
        MediaRefRequest(type=MediaType.YOUTUBE, id="short"),
    ):
        with pytest.raises(AppError) as err:
            await providers.resolve(ref)
        assert err.value.status_code == 400

    fake.calls.clear()
    for ref in (MediaRefRequest(type=MediaType.UNSPLASH, id="../me"), MediaRefRequest(type=MediaType.GIPHY, id="a/../b")):
        with pytest.raises(AppError):
            await providers.resolve(ref)
    assert not fake.calls  # never reaches the provider's URL path


# --- posts


async def test_create_a_post_with_media(s):
    group_id = await s.group()
    _, row = await s.posts.create_post(
        MEMBER, group_id, PostCreateRequest(title="Ride", body="Sunday", media=MediaRefRequest(type="GIPHY", id="gif42"))
    )
    access, _ = await s.posts.get_post(MEMBER, group_id, row.id)
    post = s.posts.to_dto(MEMBER, access, row)
    assert post.media.type == MediaType.GIPHY and post.media.url == GIF_URL
    assert "removeMedia" in post.links and "addMedia" not in post.links

    # someone else sees the media but can't change it
    other = s.posts.to_dto(OWNER, access, row)
    assert other.media is not None and "removeMedia" not in other.links


async def test_a_bad_media_id_saves_nothing(s):
    group_id = await s.group()
    with pytest.raises(AppError):
        await s.posts.create_post(
            MEMBER, group_id, PostCreateRequest(title="Ride", body="x", media=MediaRefRequest(type="UNSPLASH", id="nope"))
        )
    _, rows = await s.posts.list_posts(MEMBER, group_id)
    assert rows == []


async def test_change_media_by_removing_then_adding(s):
    group_id = await s.group()
    row = await s.post(group_id)
    access, _ = await s.posts.get_post(MEMBER, group_id, row.id)
    assert s.posts.to_dto(MEMBER, access, row).media is None
    assert "addMedia" in s.posts.to_dto(MEMBER, access, row).links

    _, row = await s.posts.set_media(MEMBER, group_id, row.id, MediaRefRequest(type="YOUTUBE", id="dQw4w9WgXcQ"))
    assert s.posts.to_dto(MEMBER, access, row).media.id == "dQw4w9WgXcQ"

    _, row = await s.posts.remove_media(MEMBER, group_id, row.id)
    assert row.media_type is None and row.media_url is None

    _, row = await s.posts.set_media(MEMBER, group_id, row.id, MediaRefRequest(type="UNSPLASH", id="abc123"))
    media = s.posts.to_dto(MEMBER, access, row).media
    assert (media.authorName, media.title) == ("Ana Lens", "a red bike")


async def test_only_the_author_changes_media_and_deleted_posts_hide_it(s):
    group_id = await s.group()
    row = await s.post(group_id)
    with pytest.raises(ForbiddenError):
        await s.posts.set_media(OWNER, group_id, row.id, MediaRefRequest(type="YOUTUBE", id="dQw4w9WgXcQ"))

    await s.posts.set_media(MEMBER, group_id, row.id, MediaRefRequest(type="YOUTUBE", id="dQw4w9WgXcQ"))
    await s.posts.delete_post(OWNER, group_id, row.id)
    access, deleted = await s.posts.get_post(MEMBER, group_id, row.id)
    assert s.posts.to_dto(MEMBER, access, deleted).media is None


# --- API


@pytest.fixture
def api(tmp_path, monkeypatch, fake):
    monkeypatch.setenv("DATABASE_MODE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "api.db"))
    from main import app
    from media.media_router import get_media_providers

    user = AuthenticatedUser(id="clerk-a", name="Alice", email="a@x.io", role_ids=[], claims={})
    app.dependency_overrides[get_authenticated_user] = lambda: user
    use = {"providers": fake.providers()}
    app.dependency_overrides[get_media_providers] = lambda: use["providers"]
    yield TestClient(app), use
    app.dependency_overrides.clear()


def test_api_search_and_post_media(api):
    http, _ = api
    me = http.get("/api/me").json()["_data"]["me"]
    links = http.get(me["links"]["userProfile"]["href"]).json()["_data"]["userProfile"]["links"]
    assert "searchGiphy" not in links  # Giphy is searched from the browser

    found = http.get(links["searchUnsplash"]["href"], params={"q": "bike"}).json()["_data"]["media"]
    assert found[0]["id"] == "abc123"
    assert http.get(links["searchUnsplash"]["href"]).status_code == 422  # q is required
    assert http.get("/api/media/giphy/search?q=x").status_code == 404

    group = http.post(links["createGroup"]["href"], json={"name": "Riders"}).json()["_data"]["group"]
    post = http.post(
        group["links"]["createPost"]["href"],
        json={"title": "Ride", "body": "Sunday", "media": {"type": "GIPHY", "id": "gif42"}},
    ).json()["_data"]["post"]
    assert post["media"]["url"] == GIF_URL

    post = http.delete(post["links"]["removeMedia"]["href"]).json()["_data"]["post"]
    assert post["media"] is None
    assert http.put(post["links"]["addMedia"]["href"], json={"type": "YOUTUBE", "id": "bad"}).status_code == 400
    post = http.put(post["links"]["addMedia"]["href"], json={"type": "YOUTUBE", "id": "dQw4w9WgXcQ"}).json()
    assert post["_data"]["post"]["media"] == {
        "type": "YOUTUBE", "id": "dQw4w9WgXcQ", "url": None, "title": None, "authorName": None, "authorUrl": None
    }


def test_api_unsplash_without_a_key_is_503(api, fake):
    http, use = api
    use["providers"] = fake.providers(unsplash=None)
    response = http.get("/api/media/unsplash/search?q=bike")
    assert response.status_code == 503 and "UNSPLASH_ACCESS_KEY" in response.json()["detail"]
