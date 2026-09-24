"""
Chats through the API without calling an AI: create, list, rename, delete,
and that nobody but the owner gets in.
"""
import pytest
from fastapi.testclient import TestClient

from core.security.auth import AuthenticatedUser, get_authenticated_user

ALICE = AuthenticatedUser(id="clerk-a", name="Alice", email="a@x.io", role_ids=[], claims={})
BOB = AuthenticatedUser(id="clerk-b", name="Bob", email="b@x.io", role_ids=["ADMIN"], claims={})


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_MODE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "api.db"))
    monkeypatch.setenv("CF_AI_MODEL", "cf-model")
    monkeypatch.setenv("GROQ_MODEL", "groq-model")
    from chats.chat_router import get_chat_search_service
    from main import app

    who = {"user": ALICE}
    app.dependency_overrides[get_authenticated_user] = lambda: who["user"]
    app.dependency_overrides[get_chat_search_service] = lambda: None
    yield TestClient(app), who
    app.dependency_overrides.clear()


def test_chat_crud_and_ownership(client):
    http, who = client
    me = http.get("/api/me").json()["_data"]["me"]
    links = http.get(me["links"]["userProfile"]["href"]).json()["_data"]["userProfile"]["links"]

    listed = http.get(links["aiChats"]["href"]).json()
    assert listed["_data"]["chats"] == [] and listed["_metadata"] == {}
    create = listed["_metaLinks"]["createChat"]["href"]

    created = http.post(create, json={"provider": "groq"})
    assert created.status_code == 201
    body = created.json()
    chat = body["_data"]["chat"]
    assert chat["title"] == "New chat" and chat["model"] == "groq-model" and chat["messages"] == []
    assert body["_metadata"] == {"title": {"maxLength": 60}}
    assert {"self", "updateTitle", "sendMessage", "delete"} <= chat["links"].keys()

    renamed = http.put(chat["links"]["updateTitle"]["href"], json={"title": "  Trip   plans "}).json()
    assert renamed["_data"]["chat"]["title"] == "Trip plans"

    who["user"] = BOB  # an admin is still not the owner
    assert http.get(chat["links"]["self"]["href"]).status_code == 403
    assert http.delete(chat["links"]["delete"]["href"]).status_code == 403

    who["user"] = ALICE
    assert http.delete(chat["links"]["delete"]["href"]).status_code == 204
    assert http.get(chat["links"]["self"]["href"]).status_code == 404
