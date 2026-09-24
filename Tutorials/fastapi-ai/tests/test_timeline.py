"""Social groups: the timeline (ALL, FOLLOWING, POPULAR) with its 1-year window."""
from datetime import datetime, timedelta, timezone

import pytest
from social import ADMIN, MEMBER, NEWS_ID, OUTSIDER, OWNER, make_social

from groups.enums import GroupVisibility
from timeline.enums import TimelineType
from timeline.timeline_repository import TimelineRepository
from timeline.timeline_service import TimelineService

ALL, FOLLOWING, POPULAR = TimelineType.ALL, TimelineType.FOLLOWING, TimelineType.POPULAR


@pytest.fixture
async def s(tmp_path):
    social = await make_social(tmp_path)
    social.timeline = TimelineService(TimelineRepository(social.db), social.posts)
    return social


async def titles(s, caller, timeline_type=ALL, limit=100):
    return [row.title for row in await s.timeline.list_posts(caller, timeline_type, limit)]


async def backdate(s, post_id, days):
    when = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    await s.db.execute("UPDATE posts SET created_date = ? WHERE id = ?", (when, post_id))


async def test_all_is_every_visible_post_newest_first(s):
    public_id = await s.group(name="Cyclists")
    await s.post(public_id, title="Public post")

    feed = await s.timeline.list_posts(OUTSIDER, ALL)
    assert feed[0].title == "Public post"  # newer than every seeded News post
    assert len(feed) == 11  # plus the 10 News posts
    dates = [row.created_date for row in feed]
    assert dates == sorted(dates, reverse=True)


async def test_private_posts_only_for_members_and_admins(s):
    private_id = await s.group(GroupVisibility.PRIVATE, name="Secret")
    await s.post(private_id, title="Secret post")

    assert "Secret post" not in await titles(s, OUTSIDER)
    assert "Secret post" in await titles(s, MEMBER)
    assert "Secret post" in await titles(s, ADMIN)


async def test_following_only_shows_followed_groups(s):
    cyclists = await s.group(name="Cyclists")
    runners = await s.group(name="Runners")
    await s.post(cyclists, title="Bikes")
    await s.post(runners, title="Shoes")

    assert await titles(s, OUTSIDER, FOLLOWING) == []
    await s.groups.follow(OUTSIDER, cyclists)
    assert await titles(s, OUTSIDER, FOLLOWING) == ["Bikes"]

    await s.groups.follow(OUTSIDER, NEWS_ID)
    feed = await titles(s, OUTSIDER, FOLLOWING)
    assert feed[0] == "Bikes" and len(feed) == 11


async def test_members_follow_automatically_and_can_unfollow(s):
    cyclists = await s.group(name="Cyclists")
    await s.post(cyclists, title="Bikes")
    assert await titles(s, MEMBER, FOLLOWING) == ["Bikes"]

    await s.groups.unfollow(MEMBER, cyclists)
    assert await titles(s, MEMBER, FOLLOWING) == []


async def test_a_stale_follow_of_a_private_group_never_leaks(s):
    private_id = await s.group(GroupVisibility.PRIVATE, name="Secret")
    await s.post(private_id, title="Secret post")
    # Simulate a follower row left behind for someone who is no longer a member.
    await s.db.execute(
        "INSERT INTO group_followers (group_id, user_id, created_date) VALUES (?, 'outsider', '2026-01-01T00:00:00Z')",
        (private_id,),
    )
    assert await titles(s, OUTSIDER, FOLLOWING) == []


async def test_popular_orders_by_score_then_newest(s):
    group_id = await s.group()
    quiet = await s.post(group_id, title="Quiet")
    liked = await s.post(group_id, title="Two likes")
    discussed = await s.post(group_id, title="One comment and one like")

    await s.posts.like(OWNER, group_id, liked.id)
    await s.posts.like(MEMBER, group_id, liked.id)  # score 2
    await s.comment(group_id, discussed.id)
    await s.posts.like(OWNER, group_id, discussed.id)  # score 3

    feed = await s.timeline.list_posts(MEMBER, POPULAR)
    ours = [row.title for row in feed if row.group_id == group_id]
    assert ours == ["One comment and one like", "Two likes", "Quiet"]
    # Two seeded News posts have 3 comments each (score 6): the tie goes to the newer one.
    assert [row.title for row in feed[:2]] == ["What are you reading this month?", "City approves new cycle lanes"]
    assert quiet.score == 0


async def test_one_year_window_applies_to_every_type(s):
    group_id = await s.group()
    old = await s.post(group_id, title="Old")
    recent = await s.post(group_id, title="Recent")
    await s.comment(group_id, old.id)
    await s.comment(group_id, old.id)  # popular, but too old
    await backdate(s, old.id, 400)
    await backdate(s, recent.id, 300)

    for timeline_type in (ALL, FOLLOWING, POPULAR):
        feed = await titles(s, MEMBER, timeline_type)
        assert "Old" not in feed and "Recent" in feed


async def test_deleted_posts_are_left_out_and_limit_applies(s):
    group_id = await s.group()
    gone = await s.post(group_id, title="Gone")
    await s.posts.delete_post(MEMBER, group_id, gone.id)
    assert "Gone" not in await titles(s, MEMBER)
    assert len(await s.timeline.list_posts(MEMBER, ALL, limit=3)) == 3


async def test_response_links_follow_the_callers_place_in_each_group(s):
    group_id = await s.group()
    await s.post(group_id, title="Mine", caller=MEMBER)

    rows = await s.timeline.list_posts(MEMBER, ALL)
    body = await s.timeline.build_response(MEMBER, ALL, rows)
    posts = {post.title: post for post in body.data["posts"]}

    assert {"update", "delete", "like", "addComment"} <= posts["Mine"].links.keys()
    news = posts["Welcome to News"]
    assert news.authorName == "System" and not {"like", "addComment", "delete"} & news.links.keys()
    assert set(body.meta_links) == {"self", "timelineAll", "timelineFollowing", "timelinePopular"}


def test_api_timeline(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient

    from core.security.auth import AuthenticatedUser, get_authenticated_user

    monkeypatch.setenv("DATABASE_MODE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "api.db"))
    from main import app

    user = AuthenticatedUser(id="clerk-a", name="Alice", email="a@x.io", role_ids=[], claims={})
    app.dependency_overrides[get_authenticated_user] = lambda: user
    try:
        http = TestClient(app)
        me = http.get("/api/me").json()["_data"]["me"]
        profile = http.get(me["links"]["userProfile"]["href"]).json()["_data"]["userProfile"]

        everything = http.get(profile["links"]["timelineAll"]["href"])
        assert everything.status_code == 200 and len(everything.json()["_data"]["posts"]) == 10
        assert http.get(profile["links"]["timelineFollowing"]["href"]).json()["_data"]["posts"] == []
        popular = http.get(profile["links"]["timelinePopular"]["href"]).json()["_data"]["posts"]
        assert [p["title"] for p in popular[:2]] == ["What are you reading this month?", "City approves new cycle lanes"]
        assert http.get("/api/timeline/posts?type=NEWEST").status_code == 422
    finally:
        app.dependency_overrides.clear()
