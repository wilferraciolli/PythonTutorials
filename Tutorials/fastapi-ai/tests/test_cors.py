"""CORS origins are read per request: Worker env (wrangler vars) first, then .env / os.environ."""
from types import SimpleNamespace

from fastapi.testclient import TestClient

from core.config.cors import allowed_origins

PAGES = "https://demo-ui-2pk.pages.dev"


def test_worker_env_wins_over_os_environ(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:4201")
    env = SimpleNamespace(CORS_ORIGINS=f"{PAGES}, http://localhost:4200")
    assert allowed_origins({"env": env}) == (PAGES, "http://localhost:4200")
    assert allowed_origins({}) == ("http://localhost:4201",)
    assert allowed_origins({"env": SimpleNamespace()}) == ("http://localhost:4201",)


def test_a_crash_is_a_500_the_browser_can_read(monkeypatch):
    # Without this the 500 has no CORS headers and the UI says "can't reach the server".
    from fastapi import FastAPI

    from core.config.cors import EnvCORSMiddleware

    monkeypatch.setenv("CORS_ORIGINS", PAGES)
    app = FastAPI()
    app.add_middleware(EnvCORSMiddleware)

    @app.post("/boom")
    async def boom():
        raise RuntimeError("unexpected")

    response = TestClient(app, raise_server_exceptions=False).post("/boom", headers={"Origin": PAGES})
    assert response.status_code == 500
    assert response.headers.get("access-control-allow-origin") == PAGES
    assert response.json() == {"detail": "Something went wrong on the server."}


def test_preflight_allows_only_listed_origins(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", PAGES)
    from main import app

    http = TestClient(app)
    headers = {"Access-Control-Request-Method": "GET", "Access-Control-Request-Headers": "authorization"}
    allowed = http.options("/api/health", headers={"Origin": PAGES, **headers})
    assert allowed.headers.get("access-control-allow-origin") == PAGES

    blocked = http.options("/api/health", headers={"Origin": "https://evil.example", **headers})
    assert "access-control-allow-origin" not in blocked.headers

    # read per request: changing the value takes effect without rebuilding the app
    monkeypatch.setenv("CORS_ORIGINS", "http://localhost:4201")
    assert "access-control-allow-origin" not in http.options(
        "/api/health", headers={"Origin": PAGES, **headers}
    ).headers
