"""
Region settings through the API: your own settings are personal (not even an
admin may use someone else's), and the system defaults are admin-only.
"""
import pytest
from fastapi.testclient import TestClient

from core.security.auth import AuthenticatedUser, get_authenticated_user

ALICE = AuthenticatedUser(id="clerk-a", name="Alice", email="a@x.io", role_ids=[], claims={})
ZED = AuthenticatedUser(id="clerk-z", name="Zed", email="z@x.io", role_ids=["ADMIN"], claims={})

GREEK = {"timezone": "Asia/Nicosia", "language": "el", "currency": "EUR", "theme": "dark"}


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_MODE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "api.db"))
    from main import app

    who = {"user": ALICE}
    app.dependency_overrides[get_authenticated_user] = lambda: who["user"]
    yield TestClient(app), who
    app.dependency_overrides.clear()


def profile_links(http) -> dict:
    me = http.get("/api/me").json()["_data"]["me"]
    return http.get(me["links"]["userProfile"]["href"]).json()["_data"]["userProfile"]["links"]


def test_your_settings_fall_back_to_the_system_defaults(client):
    http, _ = client
    href = profile_links(http)["userSettings"]["href"]

    body = http.get(href).json()
    settings = body["_data"]["userSettings"]
    assert settings["owner_type"] == "SYSTEM" and settings["timezone"] == "Europe/London"
    assert {"id": "dark", "value": "dark"} in body["_metadata"]["theme"]["values"]

    saved = http.put(settings["links"]["updateSettings"]["href"], json=GREEK).json()["_data"]["userSettings"]
    assert saved["owner_type"] == "USER" and saved["language"] == "el"
    assert http.put(href, json={**GREEK, "theme": "neon"}).status_code == 422

    assert http.delete(saved["links"]["resetSettings"]["href"]).status_code == 204
    assert http.get(href).json()["_data"]["userSettings"]["owner_type"] == "SYSTEM"


def test_nobody_else_may_use_your_settings_not_even_an_admin(client):
    http, who = client
    href = profile_links(http)["userSettings"]["href"]

    who["user"] = ZED
    assert http.get(href).status_code == 403
    assert http.put(href, json=GREEK).status_code == 403
    assert http.delete(href).status_code == 403


def test_system_settings_are_admin_only(client):
    http, who = client
    assert "systemSettings" not in profile_links(http)
    assert http.get("/api/admin/settings").status_code == 403
    assert http.put("/api/admin/settings", json=GREEK).status_code == 403

    who["user"] = ZED
    href = profile_links(http)["systemSettings"]["href"]
    system = http.get(href).json()["_data"]["systemSettings"]
    updated = http.put(system["links"]["updateSettings"]["href"], json=GREEK).json()["_data"]["systemSettings"]
    assert updated["currency"] == "EUR"

    # A user who never saved their own sees the new defaults.
    who["user"] = ALICE
    mine = http.get(profile_links(http)["userSettings"]["href"]).json()["_data"]["userSettings"]
    assert mine["owner_type"] == "SYSTEM" and mine["currency"] == "EUR"
