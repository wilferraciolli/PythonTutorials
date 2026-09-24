"""
End-to-end check of chat search with a fake embedding model and a temp SQLite
DB: no network, no Cloudflare account. The fake embedder maps text onto a few
topic axes, so "semantic" matches (no shared words) can be asserted.
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from core.config.database import SQLiteDatabase  # noqa: E402
from chats.chat_repository import ChatRepository  # noqa: E402
from chats.chat_search_service import ChatSearchService  # noqa: E402
from core.ai.vector_store import DatabaseVectorStore  # noqa: E402

TOPICS = [
    ("jvm", "java", "spring", "kotlin"),
    ("pasta", "recipe", "cook", "dinner"),
    ("angular", "typescript", "signal"),
]


async def fake_embed(texts):
    vectors = []
    for text in texts:
        lowered = text.lower()
        vector = [float(sum(word in lowered for word in words)) for words in TOPICS]
        vectors.append(vector if any(vector) else [0.01, 0.01, 0.01])
    return vectors


@pytest.fixture
async def env(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "test.db"))
    repo = ChatRepository(db)
    for user_id in ("u1", "u2"):
        await db.execute(
            "INSERT INTO users (id, name, email, created_date) VALUES (?, ?, ?, ?)",
            (user_id, user_id, f"{user_id}@x.io", "2026-01-01T00:00:00Z"),
        )
    service = ChatSearchService(repo, DatabaseVectorStore(db), fake_embed, "fake", ["cloudflare", "groq"])
    return db, repo, service


async def add_chat(repo, user_id, chat_id, title, messages, provider="cloudflare"):
    await repo.create_chat(chat_id, user_id, title, provider, "m", "2026-01-01T00:00:00Z")
    rows = []
    for i, (role, content) in enumerate(messages):
        rows.append(await repo.add_message(f"{chat_id}-{i}", chat_id, role, content, f"2026-01-01T00:00:0{i}Z"))
    return rows


@pytest.mark.asyncio
async def test_finds_by_meaning_and_keyword(env):
    db, repo, service = env
    java = await add_chat(repo, "u1", "c1", "Java help", [("user", "How do I use the JVM?"), ("assistant", "Use spring boot")])
    food = await add_chat(repo, "u1", "c2", "Dinner", [("user", "A pasta recipe please")])
    await service.index_messages("u1", java + food)

    hits = await service.search("u1", "kotlin")  # no shared words with the messages: pure semantic
    assert hits[0].chatId == "c1"
    assert not hits[0].keywordMatch

    hits = await service.search("u1", "pasta")
    assert hits[0].chatId == "c2" and hits[0].keywordMatch
    assert hits[0].links["chat"].href == "/api/users/u1/chats/c2"


@pytest.mark.asyncio
async def test_search_is_scoped_to_user(env):
    db, repo, service = env
    await service.index_messages("u1", await add_chat(repo, "u1", "c1", "Mine", [("user", "java secrets")]))
    await service.index_messages("u2", await add_chat(repo, "u2", "c2", "Theirs", [("user", "java notes")]))

    assert {hit.chatId for hit in await service.search("u2", "java")} == {"c2"}


@pytest.mark.asyncio
async def test_reindex_backfills_only_missing_and_delete_removes(env):
    db, repo, service = env
    rows = await add_chat(repo, "u1", "c1", "Java", [("user", "java one"), ("assistant", "java two")])
    await service.index_messages("u1", rows[:1])

    assert await service.reindex_user("u1") == 1
    assert await service.reindex_user("u1") == 0

    await service.remove_chat("c1")
    assert await service.vector_store.indexed_message_ids("u1") == set()


@pytest.mark.asyncio
async def test_blank_query_and_limit(env):
    db, repo, service = env
    assert await service.search("u1", "   ") == []
    await service.index_messages("u1", await add_chat(repo, "u1", "c1", "T", [("user", f"java {i}") for i in range(5)]))
    assert len(await service.search("u1", "java", limit=2)) == 2
