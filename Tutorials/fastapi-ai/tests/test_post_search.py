"""
Step 5: AI over posts and comments (docs/social-groups.md "How it plugs into
AI search and Ask"). The embedder is a fake with three topic axes; what is
tested is the server side: indexing upkeep, and above all that every search
and every tool only sees groups the caller could open in the app.
"""
import json

import pytest
from fastapi.testclient import TestClient

from assistant.tools.social_tools import build_social_tools
from core.security.auth import AuthenticatedUser, get_authenticated_user
from groups.enums import GroupVisibility
from groups.posts.schemas import PostUpdate
from groups.schemas import GroupUpdate
from groups.social_query_repository import SocialQueryRepository
from assistant.assistant_service import AssistantService
from groups.posts.post_search_service import PostSearchService
from social import ADMIN, MEMBER, NEWS_ID, OUTSIDER, OWNER, make_social

AXES = [("bike", "cycle", "lane"), ("pizza", "recipe", "cook"), ("rain", "storm", "weather")]


async def fake_embed(texts):
    out = []
    for text in texts:
        low = text.lower()
        vector = [float(sum(w in low for w in words)) for words in AXES]
        out.append(vector if any(vector) else [0.01, 0.01, 0.01])
    return out


async def broken_embed(texts):
    raise RuntimeError("Workers AI is down")


def searcher(embed=fake_embed):
    return lambda db: PostSearchService(db, embed, "fake-model")


@pytest.fixture
async def s(tmp_path):
    return await make_social(tmp_path, search=searcher())


def titles(matches):
    return [m["title"] for m in matches]


# --- search


async def test_finds_posts_by_meaning_not_just_keywords(s):
    group_id = await s.group()
    await s.post(group_id, title="Cycle lanes on Main St", body="Finally some paint on the road")
    await s.post(group_id, title="Pizza night", body="Best recipe?")

    matches = await s.posts.search.search(OUTSIDER, "bike")  # public group: anyone can find it
    assert titles(matches)[0] == "Cycle lanes on Main St"
    assert matches[0]["keywordMatch"] is False  # "bike" isn't in the text: found by meaning


async def test_a_comment_match_returns_its_post(s):
    group_id = await s.group()
    post = await s.post(group_id, title="Council meeting notes", body="Agenda below")
    await s.comment(group_id, post["id"], body="The new bike lane is great")

    [match] = [m for m in await s.posts.search.search(MEMBER, "cycle") if m["title"] == "Council meeting notes"]
    assert match["matching_comment"] == "The new bike lane is great"


async def test_lots_of_comments_do_not_outrank_a_relevant_post(s):
    group_id = await s.group()
    chatty = await s.post(group_id, title="Pizza night", body="Best recipe?")
    for body in ("Margherita", "Pepperoni", "Cook it hot", "Thin crust"):
        await s.comment(group_id, chatty["id"], body=body)
    await s.post(group_id, title="Storm warning", body="Heavy rain tonight")

    assert titles(await s.posts.search.search(MEMBER, "weather", group_id))[0] == "Storm warning"


async def test_private_group_posts_never_leak(s):
    private = await s.group(GroupVisibility.PRIVATE, name="Secret riders")
    await s.post(private, title="Secret bike route", body="Through the park")

    assert "Secret bike route" not in titles(await s.posts.search.search(OUTSIDER, "bike"))
    assert "Secret bike route" in titles(await s.posts.search.search(MEMBER, "bike"))
    assert "Secret bike route" in titles(await s.posts.search.search(ADMIN, "bike"))  # admins see all


async def test_making_a_group_private_hides_it_from_search_at_once(s):
    group_id = await s.group()
    await s.post(group_id, title="Bike swap", body="Saturday")
    assert "Bike swap" in titles(await s.posts.search.search(OUTSIDER, "bike"))

    await s.groups.update_group(OWNER, group_id, GroupUpdate(visibility=GroupVisibility.PRIVATE))
    assert "Bike swap" not in titles(await s.posts.search.search(OUTSIDER, "bike"))


async def test_edits_reindex_and_deletes_drop_out(s):
    # Vector search always returns the nearest posts, so check the ranking, not absence.
    group_id = await s.group()
    await s.post(group_id, title="Forecast", body="Rain later")
    post = await s.post(group_id, title="Weekend", body="Anything")
    assert titles(await s.posts.search.search(MEMBER, "storm", group_id))[0] == "Forecast"

    await s.posts.update_post(MEMBER, group_id, post["id"], PostUpdate(body="Big storm and rain and weather"))
    assert titles(await s.posts.search.search(MEMBER, "storm", group_id))[0] == "Weekend"

    await s.posts.delete_post(MEMBER, group_id, post["id"])
    assert "Weekend" not in titles(await s.posts.search.search(MEMBER, "rain"))


async def test_deleting_a_group_removes_its_vectors(s):
    group_id = await s.group()
    await s.post(group_id, title="Bike club", body="Join us")
    await s.groups.delete_group(OWNER, group_id)
    rows = await s.db.fetch_all("SELECT 1 FROM resource_embeddings WHERE user_id = ?", (group_id,))
    assert rows == []


async def test_reindex_backfills_the_news_seed_once(s):
    indexed = await s.posts.search.reindex_missing()
    assert indexed == {"posts": 10, "comments": 8}
    assert await s.posts.search.reindex_missing() == {"posts": 0, "comments": 0}
    assert any(m["group_id"] == NEWS_ID for m in await s.posts.search.search(OUTSIDER, "cycle lanes"))


async def test_indexing_failures_never_fail_a_write(tmp_path):
    s = await make_social(tmp_path, search=searcher(broken_embed))
    group_id = await s.group()
    post = await s.post(group_id, title="Still saved")  # Workers AI is down, the post is not
    await s.comment(group_id, post["id"], body="So is this")
    _, rows = await s.posts.list_posts(MEMBER, group_id)
    assert [r["title"] for r in rows] == ["Still saved"]


# --- tools


def tools_for(s, caller):
    return {t.name: t for t in build_social_tools(caller, SocialQueryRepository(s.db), s.posts.search)}


async def run(s, caller, name, **args):
    return await tools_for(s, caller)[name].handler(caller.user_id, args)


async def test_count_and_list_posts_respect_visibility(s):
    public = await s.group(name="Cyclists")
    private = await s.group(GroupVisibility.PRIVATE, name="Inner circle")
    await s.post(public, title="Public one")
    await s.post(private, title="Private one")
    await s.post(private, caller=OWNER, title="Owner's private one")

    outsider = await run(s, OUTSIDER, "count_posts", mine=False)
    member = await run(s, MEMBER, "count_posts")
    assert member["count"] == outsider["count"] + 2  # 10 News + public for both; private only for members

    assert await run(s, MEMBER, "count_posts", group="inner CIRCLE") == {"count": 2}
    assert await run(s, MEMBER, "count_posts", group="Inner circle", mine=True) == {"count": 1}
    # an outsider can't even learn the private group exists
    assert "error" in await run(s, OUTSIDER, "count_posts", group="Inner circle")

    listed = await run(s, OUTSIDER, "list_posts", group="Cyclists")
    assert [p["title"] for p in listed["posts"]] == ["Public one"]


async def test_popular_posts_and_comment_counts(s):
    group_id = await s.group()
    quiet = await s.post(group_id, title="Quiet")
    busy = await s.post(group_id, title="Busy")
    await s.comment(group_id, busy["id"])
    await s.comment(group_id, busy["id"], caller=OWNER)
    await s.posts.like(OWNER, group_id, quiet["id"])

    popular = await run(s, MEMBER, "list_posts", group="Cyclists", sort="popular")
    assert [p["title"] for p in popular["posts"]] == ["Busy", "Quiet"]  # 2 comments (4) beat 1 like (1)
    assert await run(s, MEMBER, "count_comments", group="Cyclists", mine=True) == {"count": 1}
    assert "error" in await run(s, MEMBER, "list_posts", sort="random")


async def test_date_filters(s):
    group_id = await s.group()
    await s.post(group_id, title="Today")
    await s.db.execute("UPDATE posts SET created_date = '2025-03-10T09:00:00+00:00' WHERE title = 'Today'")
    assert await run(s, MEMBER, "count_posts", group="Cyclists", created_from="2025-03-10", created_to="2025-03-10") == {"count": 1}
    assert await run(s, MEMBER, "count_posts", group="Cyclists", created_from="2025-03-11") == {"count": 0}
    assert "error" in await run(s, MEMBER, "count_posts", created_from="last tuesday")


async def test_my_groups(s):
    await s.group(name="Cyclists")
    await s.groups.follow(OUTSIDER, NEWS_ID)
    groups = {g["name"]: g for g in (await run(s, MEMBER, "my_groups"))["groups"]}
    assert groups["Cyclists"]["member"] and not groups["Cyclists"]["owner"]
    assert "News" not in groups  # MEMBER doesn't follow News
    assert [g["name"] for g in (await run(s, OUTSIDER, "my_groups"))["groups"]] == ["News"]


async def test_search_posts_tool_is_scoped(s):
    private = await s.group(GroupVisibility.PRIVATE, name="Inner circle")
    await s.post(private, title="Secret bike route")
    outsider = await run(s, OUTSIDER, "search_posts", query="bike")
    assert "Secret bike route" not in [m["title"] for m in outsider["matches"]]
    assert "error" in await run(s, OUTSIDER, "search_posts", query="bike", group="Inner circle")
    found = await run(s, MEMBER, "search_posts", query="bike", group="Inner circle")
    assert [m["title"] for m in found["matches"]] == ["Secret bike route"]


async def test_tools_refuse_another_user_id(s):
    tool = tools_for(s, MEMBER)["count_posts"]
    assert await tool.handler(OUTSIDER.user_id, {}) == {"error": "not allowed"}


class Scripted:
    def __init__(self, turns):
        self.turns = list(turns)

    async def complete(self, model, messages, tools):
        return self.turns.pop(0) if self.turns else {"content": "done", "tool_calls": []}


async def test_assistant_answers_a_social_question(s):
    group_id = await s.group()
    await s.post(group_id, title="Mine 1")
    await s.post(group_id, title="Mine 2")
    llm = Scripted(
        [
            {"content": None, "tool_calls": [{"id": "1", "name": "count_posts", "arguments": json.dumps({"mine": True})}]},
            {"content": "You have written 2 posts.", "tool_calls": []},
        ]
    )
    service = AssistantService(llm, "m", "groq", build_social_tools(MEMBER, SocialQueryRepository(s.db)))
    answer = await service.ask(MEMBER.user_id, "how many posts have I written?")
    assert answer.answer == "You have written 2 posts."
    assert answer.toolCalls[0].result == {"count": 2}


# --- admin API


def test_admin_reindex_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_MODE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "api.db"))
    from core.config.database import SQLiteDatabase
    from main import app
    from groups.posts.post_router import get_post_search_service

    db = SQLiteDatabase(str(tmp_path / "api.db"))
    who = {"user": AuthenticatedUser(id="clerk-a", name="Alice", email="a@x.io", role_ids=[], claims={})}
    app.dependency_overrides[get_authenticated_user] = lambda: who["user"]
    app.dependency_overrides[get_post_search_service] = lambda: PostSearchService(db, fake_embed, "fake-model")
    try:
        http = TestClient(app)
        assert http.post("/api/admin/post-search/reindex").status_code == 403

        who["user"] = AuthenticatedUser(id="clerk-b", name="Bo", email="b@x.io", role_ids=["ADMIN"], claims={})
        hub = http.get("/api/admin").json()
        assert "reindexPostSearch" in [t["id"] for t in hub["_data"]["admin"]["tools"]]
        result = http.post(hub["_metaLinks"]["reindexPostSearch"]["href"]).json()
        assert result["_data"]["reindexPostSearch"]["indexed"] == {"posts": 10, "comments": 8}
    finally:
        app.dependency_overrides.clear()
