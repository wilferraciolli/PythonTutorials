"""
The example questions people actually type, checked against the tools they map to:
"how many todos did I create last quarter", "how many are tagged important",
"todos about the tax return". The model is scripted; what is tested is the
server side (period maths, filters, tags, embeddings search, index upkeep).
"""
import json
from datetime import date, datetime, timezone

import pytest

from assistant.date_tools import build_date_tools, resolve_period
from assistant.todo_tools import build_todo_tools
from database import SQLiteDatabase
from repositories.tag_repository import TagRepository
from repositories.todo_repository import TodoRepository
from resource_vector_store import ResourceVectorStore
from services.assistant_service import AssistantService
from services.tag_service import TagService
from services.todo_search_service import TodoSearchService
from services.todo_service import TodoService
from models import TodoCreate

NOW = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)  # Q2 2026


@pytest.mark.parametrize(
    "period,today,expected",
    [
        ("last_quarter", date(2026, 6, 15), (date(2026, 1, 1), date(2026, 3, 31))),
        ("last_quarter", date(2026, 1, 10), (date(2025, 10, 1), date(2025, 12, 31))),
        ("this_quarter", date(2026, 6, 15), (date(2026, 4, 1), date(2026, 6, 30))),
        ("last_month", date(2026, 3, 5), (date(2026, 2, 1), date(2026, 2, 28))),
        ("last_month", date(2026, 1, 5), (date(2025, 12, 1), date(2025, 12, 31))),
        ("last_year", date(2026, 6, 15), (date(2025, 1, 1), date(2025, 12, 31))),
        ("this_week", date(2026, 6, 17), (date(2026, 6, 15), date(2026, 6, 21))),  # Wed -> Mon..Sun
        ("last_7_days", date(2026, 6, 15), (date(2026, 6, 9), date(2026, 6, 15))),
    ],
)
def test_resolve_period(period, today, expected):
    assert resolve_period(period, today) == expected


def test_unknown_period():
    with pytest.raises(ValueError):
        resolve_period("next_decade", date(2026, 1, 1))


async def fake_embed(texts):
    axes = [("tax", "hmrc", "self-assessment"), ("garden", "lawn", "plant")]
    out = []
    for text in texts:
        low = text.lower()
        vector = [float(sum(w in low for w in words)) for words in axes]
        out.append(vector if any(vector) else [0.01, 0.01])
    return out


class Scripted:
    def __init__(self, turns):
        self.turns = list(turns)

    async def complete(self, model, messages, tools):
        return self.turns.pop(0) if self.turns else {"content": "done", "tool_calls": []}


def call(name, **arguments):
    return {"content": None, "tool_calls": [{"id": f"c-{name}", "name": name, "arguments": json.dumps(arguments)}]}


@pytest.fixture
async def env(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "t.db"))
    for uid in ("u1", "u2"):
        await db.execute(
            "INSERT INTO users (id, name, email, created_date) VALUES (?, ?, ?, ?)",
            (uid, uid, f"{uid}@x.io", "2026-01-01T00:00:00Z"),
        )

    rows = [
        # id, user, title, description, created, tags
        ("t1", "u1", "File HMRC self-assessment", None, "2026-02-10T09:00:00+00:00", ["important"]),
        ("t2", "u1", "Mow the lawn", "front and back", "2026-03-31T23:30:00+00:00", []),  # last day of Q1
        ("t3", "u1", "Book dentist", None, "2026-04-01T00:00:00+00:00", ["Important"]),  # first day of Q2
        ("t4", "u1", "Plan holiday", None, "2025-12-31T10:00:00+00:00", []),  # Q4 2025
        ("t5", "u2", "Someone else's tax thing", None, "2026-02-01T00:00:00+00:00", ["important"]),
    ]
    for tid, uid, title, desc, created, tags in rows:
        await db.execute(
            "INSERT INTO todos (id, user_id, title, description, complete_by, state, created_date) "
            "VALUES (?, ?, ?, ?, ?, 'NEW', ?)",
            (tid, uid, title, desc, "2026-12-01T00:00:00+00:00", created),
        )
        for tag in tags:
            await db.execute(
                "INSERT INTO tags (id, resource_id, tag) VALUES (?, ?, ?)", (f"{tid}-{tag}", tid, tag)
            )

    repo = TodoRepository(db)
    search = TodoSearchService(repo, ResourceVectorStore(db, "todo"), fake_embed, "fake")
    await search.index_todos(await repo.list_for_user("u1") + await repo.list_for_user("u2"))
    tools = [*build_todo_tools(repo, lambda: NOW, search=search), *build_date_tools(lambda: NOW)]

    def make(turns):
        return AssistantService(Scripted(turns), "m", "groq", tools, now=lambda: NOW)

    return db, repo, search, make


async def test_how_many_todos_created_last_quarter(env):
    _, _, _, make = env
    # What a good model does: resolve the period first, then filter by it.
    answer = await make(
        [
            call("date_range", period="last_quarter"),
            call("count_todos", created_from="2026-01-01", created_to="2026-03-31"),
            {"content": "2", "tool_calls": []},
        ]
    ).ask("u1", "how many todos have I created last quarter?")

    assert answer.toolCalls[0].result == {"period": "last_quarter", "from": "2026-01-01", "to": "2026-03-31"}
    # t1 (Feb) and t2 (23:30 on the last day) count; t3 (Apr 1) and t4 (Dec 2025) do not; t5 is u2's.
    assert answer.toolCalls[1].result == {"count": 2}


async def test_how_many_todos_tagged_important(env):
    _, _, _, make = env
    answer = await make([call("count_todos", tag="important"), {"content": "2", "tool_calls": []}]).ask(
        "u1", "how many todos with the tag important?"
    )
    assert answer.toolCalls[0].result == {"count": 2}  # t1 "important" + t3 "Important"; not u2's t5


async def test_tags_can_be_combined_with_dates_and_listed(env):
    _, _, _, make = env
    answer = await make(
        [
            call("count_todos", tag="important", created_from="2026-01-01", created_to="2026-03-31"),
            call("list_tags"),
            {"content": "ok", "tool_calls": []},
        ]
    ).ask("u1", "important ones from last quarter, and what tags do I have?")

    assert answer.toolCalls[0].result == {"count": 1}
    assert answer.toolCalls[1].result == {"tags": [{"tag": "Important", "count": 1}, {"tag": "important", "count": 1}]}


async def test_bad_dates_return_an_error_the_model_can_fix(env):
    _, _, _, make = env
    answer = await make([call("count_todos", created_from="last quarter"), {"content": "?", "tool_calls": []}]).ask(
        "u1", "?"
    )
    assert answer.toolCalls[0].result == {"error": "dates must be YYYY-MM-DD"}


async def test_search_todos_by_meaning_is_scoped_to_user(env):
    _, _, search, make = env
    hits = await search.search("u1", "taxes")  # shares no word with the title: meaning only
    assert hits[0]["title"] == "File HMRC self-assessment"
    assert all(hit["title"] != "Someone else's tax thing" for hit in hits)

    answer = await make([call("search_todos", query="garden work"), {"content": "x", "tool_calls": []}]).ask("u1", "?")
    assert answer.toolCalls[0].result["matches"][0]["title"] == "Mow the lawn"


async def test_todo_service_keeps_the_index_in_step(env):
    db, repo, search, _ = env
    service = TodoService(repo, TagService(TagRepository(db)), search)

    created = await service.create_todo(
        "u1",
        TodoCreate(title="Water the plant", complete_by=datetime(2027, 1, 1, tzinfo=timezone.utc)),
    )
    assert created.id in await search.store.indexed_ids("u1")
    assert "Water the plant" in [hit["title"] for hit in (await search.search("u1", "garden"))[:2]]

    assert await service.delete_todo("u1", created.id)
    assert created.id not in await search.store.indexed_ids("u1")


async def test_reindex_backfills_only_missing(env):
    db, repo, search, _ = env
    await db.execute(
        "INSERT INTO todos (id, user_id, title, complete_by, state, created_date) VALUES "
        "('t9', 'u1', 'New unindexed todo', '2026-12-01T00:00:00+00:00', 'NEW', '2026-06-01T00:00:00+00:00')"
    )
    assert await search.reindex_user("u1") == 1
    assert await search.reindex_user("u1") == 0
