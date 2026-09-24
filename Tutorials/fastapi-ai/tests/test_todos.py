"""
Todos and tags through the API, as the showcase uses them: follow the
profile's links, create from the template, tag, and read the shapes back.
"""
import pytest
from fastapi.testclient import TestClient

from core.security.auth import AuthenticatedUser, get_authenticated_user

ALICE = AuthenticatedUser(id="clerk-a", name="Alice", email="a@x.io", role_ids=[], claims={})


@pytest.fixture
def http(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_MODE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "api.db"))
    from main import app
    from todos.todo_router import get_todo_search_service

    app.dependency_overrides[get_authenticated_user] = lambda: ALICE
    app.dependency_overrides[get_todo_search_service] = lambda: None  # no Workers AI in tests
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_todo_lifecycle_and_tags(http):
    me = http.get("/api/me").json()["_data"]["me"]
    links = http.get(me["links"]["userProfile"]["href"]).json()["_data"]["userProfile"]["links"]

    template = http.get(links["todoTemplate"]["href"]).json()
    assert set(template["_data"]["todo"]) == {"title", "description", "complete_by", "state"}
    assert template["_data"]["todo"]["complete_by"].endswith("Z")
    assert template["_metadata"]["title"] == {"mandatory": True}
    assert [value["id"] for value in template["_metadata"]["state"]["values"]] == ["NEW", "ACTIVE", "CLOSED"]

    create_url = links["todoTemplate"]["href"].removesuffix("/template")
    created = http.post(create_url, json={"title": "Tax return", "complete_by": "2099-01-31T12:00:00Z"})
    assert created.status_code == 201
    todo = created.json()["_data"]["todo"]
    assert todo["complete_by"] == "2099-01-31T12:00:00Z" and todo["state"] == "NEW"
    assert {"self", "update", "delete", "addTag", "tags"} <= todo["links"].keys()

    # NEW todos get the not-started tag; tags embed the todo's title.
    tags = http.get(todo["links"]["tags"]["href"]).json()["_data"]["tags"]
    assert [tag["tag"] for tag in tags] == ["not-started"]
    assert tags[0]["resource"] == {"id": todo["id"], "value": "Tax return"}

    started = http.put(todo["links"]["update"]["href"], json={"state": "ACTIVE"}).json()
    assert "NEW" not in [value["id"] for value in started["_metadata"]["state"]["values"]]

    listed = http.get(links["todos"]["href"]).json()
    assert [t["id"] for t in listed["_data"]["todos"]] == [todo["id"]]
    assert "todoTemplate" in listed["_metaLinks"] and listed["_messages"] == []

    assert http.delete(todo["links"]["delete"]["href"]).status_code == 204
    assert http.get(todo["links"]["self"]["href"]).status_code == 404
    assert http.get(todo["links"]["tags"]["href"]).json()["_data"]["tags"] == []


def test_tag_template_and_validation(http):
    template = http.get("/api/tags/template").json()
    assert template["_data"]["tag"] == {"resource_id": "", "tag": ""}
    assert "createTag" in template["_metaLinks"]
    assert http.post("/api/tags", json={"resource_id": "x", "tag": ""}).status_code == 422
