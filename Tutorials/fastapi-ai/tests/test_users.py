"""
Users, /me and the profile through the API: who may change users, the
lockout guard, roles from Clerk vs. roles granted here, and which links a
caller is handed.
"""
import pytest
from fastapi.testclient import TestClient

from core.security.auth import AuthenticatedUser, get_authenticated_user

ALICE = AuthenticatedUser(id="clerk-a", name="Alice", email="a@x.io", role_ids=[], claims={})
ZED = AuthenticatedUser(id="clerk-z", name="Zed", email="z@x.io", role_ids=["ADMIN"], claims={})


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_MODE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "api.db"))
    from main import app

    who = {"user": ALICE}
    app.dependency_overrides[get_authenticated_user] = lambda: who["user"]
    yield TestClient(app), who
    app.dependency_overrides.clear()


def me(http) -> dict:
    return http.get("/api/me").json()["_data"]["me"]


def test_every_response_has_the_full_envelope(client):
    http, _ = client
    body = http.get("/api/me").json()
    assert set(body) == {"_data", "_metadata", "_metaLinks", "_messages"}
    assert body["_messages"] == []


def test_only_admins_change_users_or_get_write_links(client):
    http, who = client
    alice = me(http)
    users = http.get("/api/users").json()
    assert "createUser" not in users["_metaLinks"]
    assert all(set(user["links"]) == {"self"} for user in users["_data"]["users"])
    assert http.post("/api/users", json={"name": "Bob", "email": "b@x.io"}).status_code == 403
    assert http.put(f"/api/users/{alice['id']}", json={"name": "Al"}).status_code == 403
    assert http.delete(f"/api/users/{alice['id']}").status_code == 403

    who["user"] = ZED
    zed = me(http)
    users = http.get("/api/users").json()
    assert {"createUser", "userTemplate"} <= users["_metaLinks"].keys()
    links = {user["id"]: user["links"] for user in users["_data"]["users"]}
    assert "deleteUser" in links[alice["id"]] and "deleteUser" not in links[zed["id"]]

    created = http.post("/api/users", json={"name": "Bob", "email": "b@x.io"})
    assert created.status_code == 201 and created.json()["_data"]["user"]["roleIds"] == ["STANDARD"]


def test_admins_cannot_lock_themselves_out(client):
    http, who = client
    who["user"] = ZED
    zed = me(http)
    assert http.put(f"/api/users/{zed['id']}", json={"roleIds": ["STANDARD"]}).status_code == 400
    assert http.delete(f"/api/users/{zed['id']}").status_code == 400
    assert http.put(f"/api/users/{zed['id']}", json={"name": "Zed Z"}).status_code == 200


def test_a_role_granted_here_survives_a_token_without_it(client):
    http, who = client
    alice = me(http)
    who["user"] = ZED
    me(http)
    promoted = http.put(f"/api/users/{alice['id']}", json={"roleIds": ["ADMIN", "STANDARD"]})
    assert promoted.json()["_data"]["user"]["roleIds"] == ["ADMIN", "STANDARD"]

    who["user"] = ALICE  # Clerk still says nothing about ADMIN
    assert me(http)["roleIds"] == ["ADMIN", "STANDARD"]
    assert http.get("/api/admin").status_code == 200


def test_personal_links_only_on_your_own_profile(client):
    http, who = client
    alice = me(http)
    own = http.get(alice["links"]["userProfile"]["href"]).json()["_data"]["userProfile"]["links"]
    assert {"todos", "todoTemplate", "aiChats", "aiAssistant", "groups"} <= own.keys()
    assert not {"userTemplate", "admin"} & own.keys()

    who["user"] = ZED
    zed = me(http)
    theirs = http.get(f"/api/users/{alice['id']}/profile").json()["_data"]["userProfile"]["links"]
    assert not {"todos", "aiChats", "aiAssistant", "admin"} & theirs.keys()
    assert "userTemplate" in theirs
    assert http.get(f"/api/users/{alice['id']}/todos").status_code == 403
    assert "admin" in http.get(f"/api/users/{zed['id']}/profile").json()["_data"]["userProfile"]["links"]
