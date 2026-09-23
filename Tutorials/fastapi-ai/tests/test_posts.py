"""
Social groups: posts and the seeded News group (docs/social-groups.md).
Comments are in test_post_comments.py, likes and stats in test_likes.py.
"""
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from auth import AuthenticatedUser, get_authenticated_user
from errors import ForbiddenError, NotFoundError
from models import GroupVisibility, PostCreate, PostUpdate
from repositories.user_repository import UserRepository
from social import ADMIN, MEMBER, NEWS_ID, OUTSIDER, OWNER, make_social


@pytest.fixture
async def s(tmp_path):
    return await make_social(tmp_path)


# --- seed


async def test_news_group_is_seeded_public_and_ownerless_with_posts(s):
    access = await s.groups.get_visible(OUTSIDER, NEWS_ID)
    assert access.group["name"] == "News"
    assert access.group["visibility"] == "PUBLIC" and access.group["owner_id"] is None

    _, rows = await s.posts.list_posts(OUTSIDER, NEWS_ID)
    assert len(rows) == 10
    assert [r["created_date"] for r in rows] == sorted((r["created_date"] for r in rows), reverse=True)
    assert s.posts.to_post(OUTSIDER, access, rows[0]).authorName == "System"

    # post_stats was backfilled for the seeded posts: the cycle-lanes post has 3 comments
    lanes = next(r for r in rows if r["title"] == "City approves new cycle lanes")
    assert lanes["comment_count"] == 3 and lanes["score"] == 6


async def test_outsiders_can_read_news_but_not_post(s):
    with pytest.raises(ForbiddenError):
        await s.post(NEWS_ID, caller=OUTSIDER)
    assert (await s.post(NEWS_ID, caller=ADMIN))["title"] == "Bike lanes"  # admins post anywhere


# --- posts


async def test_title_and_body_are_required():
    with pytest.raises(ValidationError):
        PostCreate(title="", body="x")
    with pytest.raises(ValidationError):
        PostCreate(title="x")  # type: ignore[call-arg]


async def test_members_post_and_list_newest_first(s):
    group_id = await s.group()
    first = await s.post(group_id, title="First")
    second = await s.post(group_id, caller=OWNER, title="Second")

    _, rows = await s.posts.list_posts(OUTSIDER, group_id)
    assert [r["id"] for r in rows] == [second["id"], first["id"]]
    assert first["like_count"] == 0 and first["comment_count"] == 0


async def test_private_group_posts_are_hidden_from_outsiders(s):
    group_id = await s.group(GroupVisibility.PRIVATE, name="Secret")
    row = await s.post(group_id)

    with pytest.raises(NotFoundError):
        await s.posts.list_posts(OUTSIDER, group_id)
    with pytest.raises(NotFoundError):
        await s.posts.get_post(OUTSIDER, group_id, row["id"])
    assert (await s.posts.get_post(ADMIN, group_id, row["id"]))[1]["id"] == row["id"]


async def test_a_post_cannot_be_reached_through_another_group(s):
    private_id = await s.group(GroupVisibility.PRIVATE, name="Secret")
    public_id = await s.group(name="Open")
    row = await s.post(private_id)

    with pytest.raises(NotFoundError):
        await s.posts.get_post(OUTSIDER, public_id, row["id"])


async def test_only_the_author_edits(s):
    group_id = await s.group()
    row = await s.post(group_id)

    for caller in (OWNER, ADMIN):
        with pytest.raises(ForbiddenError):
            await s.posts.update_post(caller, group_id, row["id"], PostUpdate(title="changed"))
    _, updated = await s.posts.update_post(MEMBER, group_id, row["id"], PostUpdate(title="Better title"))
    assert updated["title"] == "Better title" and updated["body"] == "Thoughts?"


async def test_delete_by_author_owner_or_admin_and_it_is_soft(s):
    group_id = await s.group()
    await s.groups.join(OUTSIDER, group_id)
    rows = [await s.post(group_id) for _ in range(3)]

    with pytest.raises(ForbiddenError):  # another member
        await s.posts.delete_post(OUTSIDER, group_id, rows[0]["id"])

    await s.posts.delete_post(MEMBER, group_id, rows[0]["id"])  # author
    await s.posts.delete_post(OWNER, group_id, rows[1]["id"])  # group owner
    await s.posts.delete_post(ADMIN, group_id, rows[2]["id"])  # admin

    _, listed = await s.posts.list_posts(MEMBER, group_id)
    assert listed == []
    access, deleted = await s.posts.get_post(MEMBER, group_id, rows[0]["id"])
    shown = s.posts.to_post(MEMBER, access, deleted)
    assert shown.isDeleted and shown.title == "[deleted]" and shown.authorName is None
    assert set(shown.links) == {"self", "group", "comments"}


async def test_deleted_user_shows_as_deleted_user(s):
    group_id = await s.group()
    row = await s.post(group_id)
    await UserRepository(s.db).delete("member")

    access, fresh = await s.posts.get_post(OWNER, group_id, row["id"])
    assert s.posts.to_post(OWNER, access, fresh).authorName == "[deleted user]"


async def test_deleting_a_group_removes_everything_in_it(s):
    group_id = await s.group()
    row = await s.post(group_id)
    comment = await s.comment(group_id, row["id"])
    await s.posts.like(OWNER, group_id, row["id"])
    await s.comments.like(OWNER, group_id, row["id"], comment["id"])

    await s.groups.delete_group(OWNER, group_id)
    for table, column, value in [
        ("posts", "group_id", group_id),
        ("comments", "post_id", row["id"]),
        ("post_stats", "post_id", row["id"]),
        ("reactions", "target_id", row["id"]),
        ("reactions", "target_id", comment["id"]),
    ]:
        assert await s.db.fetch_all(f"SELECT 1 FROM {table} WHERE {column} = ?", (value,)) == []


# --- API wiring


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_MODE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "api.db"))
    from main import app

    who = {"user": AuthenticatedUser(id="clerk-a", name="Alice", email="a@x.io", role_ids=[], claims={})}
    app.dependency_overrides[get_authenticated_user] = lambda: who["user"]
    yield TestClient(app), who
    app.dependency_overrides.clear()


def test_api_posts_comments_and_likes(client):
    http, who = client
    news = http.get(f"/api/groups/{NEWS_ID}/posts").json()
    assert len(news["_data"]["posts"]) == 10 and "createPost" not in news["_metaLinks"]

    group = http.post("/api/groups", json={"name": "Cyclists"}).json()["_data"]["group"]
    assert http.post(group["links"]["createPost"]["href"], json={"title": "x"}).status_code == 422

    created = http.post(group["links"]["createPost"]["href"], json={"title": "Lanes", "body": "Yes!"})
    assert created.status_code == 201
    post = created.json()["_data"]["post"]
    assert post["authorName"] == "Alice" and {"update", "delete", "addComment", "like"} <= post["links"].keys()

    top = http.post(post["links"]["addComment"]["href"], json={"body": "Top"}).json()["_data"]["comment"]
    http.post(top["links"]["reply"]["href"], json={"body": "Reply", "parentCommentId": top["id"]})
    comments = http.get(post["links"]["comments"]["href"]).json()["_data"]["comments"]
    assert [c["parentCommentId"] for c in comments] == [None, top["id"]]

    liked = http.put(post["links"]["like"]["href"]).json()["_data"]["post"]
    assert liked["likedByMe"] and liked["likeCount"] == 1 and liked["commentCount"] == 2
    assert "unlike" in liked["links"]

    comment_liked = http.put(top["links"]["like"]["href"]).json()["_data"]["comment"]
    assert comment_liked["likeCount"] == 1 and comment_liked["likedByMe"]

    assert http.delete(post["links"]["delete"]["href"]).status_code == 204
    assert http.get(post["links"]["self"]["href"]).json()["_data"]["post"]["title"] == "[deleted]"


def test_api_admin_area_is_linked_from_an_admins_profile_only(client):
    http, who = client

    def profile():
        me = http.get("/api/me").json()["_data"]["me"]
        return http.get(me["links"]["userProfile"]["href"]).json()["_data"]["userProfile"]

    assert "admin" not in profile()["links"]
    assert http.get("/api/admin").status_code == 403
    assert http.post("/api/admin/post-stats/rebuild").status_code == 403

    who["user"] = AuthenticatedUser(id="clerk-z", name="Zed", email="z@x.io", role_ids=["ADMIN"], claims={})
    admin = http.get(profile()["links"]["admin"]["href"]).json()
    assert [t["id"] for t in admin["_data"]["admin"]["tools"]] == ["rebuildPostStats", "reindexPostSearch"]

    rebuilt = http.post(admin["_metaLinks"]["rebuildPostStats"]["href"])
    assert rebuilt.status_code == 200 and rebuilt.json()["_data"]["postStats"]["rebuilt"] == 10
