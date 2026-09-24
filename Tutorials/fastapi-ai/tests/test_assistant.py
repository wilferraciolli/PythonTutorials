"""
The assistant loop with a scripted fake LLM (no network): the "model" is a list
of turns, so we can check what the server does with tool calls — user scoping,
overdue logic, bad arguments, step limit — without depending on a real model.
"""
import json
from datetime import datetime, timezone

import pytest

from assistant.tools.chat_tools import build_chat_tools
from assistant.tools.todo_tools import build_todo_tools
from core.config.database import SQLiteDatabase
from chats.chat_repository import ChatRepository
from todos.todo_repository import TodoRepository
from assistant.assistant_service import MAX_STEPS, AssistantService
from chats.chat_search_service import SearchService
from core.ai.vector_store import DatabaseVectorStore

NOW = datetime(2026, 6, 15, 12, 0, tzinfo=timezone.utc)


class ScriptedLlm:
    def __init__(self, turns):
        self.turns = list(turns)
        self.seen = []

    async def complete(self, model, messages, tools):
        self.seen.append([dict(m) for m in messages])
        return self.turns.pop(0) if self.turns else {"content": "done", "tool_calls": []}


def call(name, **arguments):
    return {"content": None, "tool_calls": [{"id": f"call-{name}", "name": name, "arguments": json.dumps(arguments)}]}


def final(text):
    return {"content": text, "tool_calls": []}


async def fake_embed(texts):
    return [[1.0, 0.0] if "java" in t.lower() else [0.0, 1.0] for t in texts]


@pytest.fixture
async def env(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))
    for user_id in ("u1", "u2"):
        await db.execute(
            "INSERT INTO users (id, name, email, created_date) VALUES (?, ?, ?, ?)",
            (user_id, user_id, f"{user_id}@x.io", "2026-01-01T00:00:00Z"),
        )

    todos = [
        # (id, user, state, complete_by)
        ("t1", "u1", "NEW", "2026-06-01T00:00:00+00:00"),  # overdue
        ("t2", "u1", "ACTIVE", "2026-06-10T00:00:00Z"),  # overdue (Z suffix)
        ("t3", "u1", "NEW", "2026-07-01T00:00:00+00:00"),  # not due yet
        ("t4", "u1", "CLOSED", "2026-05-01T00:00:00+00:00"),  # past, but closed: not overdue
        ("t5", "u2", "NEW", "2026-01-01T00:00:00+00:00"),  # someone else's
    ]
    for todo_id, user_id, state, complete_by in todos:
        await db.execute(
            "INSERT INTO todos (id, user_id, title, complete_by, state, created_date) VALUES (?, ?, ?, ?, ?, ?)",
            (todo_id, user_id, f"todo {todo_id}", complete_by, state, "2026-01-01T00:00:00Z"),
        )

    repo = ChatRepository(db)
    search = SearchService(repo, DatabaseVectorStore(db), fake_embed, "fake", ["cloudflare", "groq"])
    tools = [*build_todo_tools(TodoRepository(db), lambda: NOW), *build_chat_tools(search)]

    def make(llm):
        return AssistantService(llm, "m", "groq", tools, now=lambda: NOW)

    return db, repo, search, make


async def test_counts_overdue_todos_for_the_path_user_only(env):
    _, _, _, make = env
    llm = ScriptedLlm([call("count_todos", overdue=True), final("You have 2 overdue todos.")])

    answer = await make(llm).ask("u1", "how many todos are overdue?")

    assert answer.answer == "You have 2 overdue todos."
    assert answer.toolCalls[0].result == {"count": 2}  # t1, t2; not closed t4, not u2's t5
    tool_message = llm.seen[1][-1]
    assert tool_message["role"] == "tool" and json.loads(tool_message["content"]) == {"count": 2}


async def test_new_count_and_model_cannot_pick_another_user(env):
    _, _, _, make = env
    llm = ScriptedLlm([call("count_todos", state="NEW", user_id="u2"), final("2")])

    answer = await make(llm).ask("u1", "how many new?")

    assert answer.toolCalls[0].result == {"count": 2}  # u1's NEW todos; the user_id argument is ignored


async def test_bad_state_returns_error_to_model_and_unknown_tool_is_reported(env):
    _, _, _, make = env
    llm = ScriptedLlm([call("count_todos", state="DONE"), call("drop_tables"), final("sorry")])

    answer = await make(llm).ask("u1", "?")

    assert "error" in answer.toolCalls[0].result
    assert "unknown tool" in answer.toolCalls[1].result["error"]


async def test_invalid_json_arguments_do_not_crash(env):
    _, _, _, make = env
    bad = {"content": None, "tool_calls": [{"id": "x", "name": "count_todos", "arguments": "{not json"}]}
    answer = await make(ScriptedLlm([bad, final("ok")])).ask("u1", "?")
    assert "invalid arguments" in answer.toolCalls[0].result["error"]


async def test_search_chats_tool_finds_messages(env):
    _, repo, search, make = env
    await repo.create_chat("c1", "u1", "Java help", "groq", "m", "2026-01-01T00:00:00Z")
    message = await repo.add_message("m1", "c1", "user", "How do I learn java?", "2026-01-01T00:00:01Z")
    await search.index_messages("u1", [message])

    llm = ScriptedLlm([call("search_chats", query="java"), final("In your 'Java help' chat.")])
    answer = await make(llm).ask("u1", "where did I ask about java?")

    assert answer.toolCalls[0].result["matches"][0]["chat_title"] == "Java help"
    assert (await make(ScriptedLlm([call("search_chats", query="java"), final("")])).ask("u2", "java?")).toolCalls[
        0
    ].result == {"matches": []}


async def test_stops_after_max_steps(env):
    _, _, _, make = env
    llm = ScriptedLlm([call("count_todos")] * (MAX_STEPS + 3))

    answer = await make(llm).ask("u1", "loop forever")

    assert len(answer.toolCalls) == MAX_STEPS
    assert "couldn't work that out" in answer.answer


async def test_system_prompt_has_todays_date(env):
    _, _, _, make = env
    llm = ScriptedLlm([final("hi")])
    await make(llm).ask("u1", "hi")
    assert "2026-06-15" in llm.seen[0][0]["content"]
