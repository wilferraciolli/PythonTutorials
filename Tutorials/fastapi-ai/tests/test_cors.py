"""The app reads CORS_ORIGINS per request (EnvCORSMiddleware itself is tested in wiltech-labs-core)."""
from fastapi.testclient import TestClient

PAGES = "https://demo-ui-2pk.pages.dev"


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
