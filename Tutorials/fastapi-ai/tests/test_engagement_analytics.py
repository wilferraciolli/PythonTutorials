"""
Engagement analytics API (docs/social-groups.md "Engagement analytics"):
groups, posts, comments and likes created per UTC day, admins only.
"""
from datetime import date

import pytest
from fastapi.testclient import TestClient

from core.security.auth import AuthenticatedUser, get_authenticated_user
from core.config.database import SQLiteDatabase
from admin.analytics.engagement_repository import EngagementRepository
from admin.analytics.engagement_service import EngagementAnalyticsService

TODAY = date(2026, 9, 24)


@pytest.fixture
async def db(tmp_path):
    db = SQLiteDatabase(str(tmp_path / "engagement.db"))
    # The migrations seed the News group with content dated relative to the
    # real clock; clear it so only this test's rows are counted.
    for table in ("groups", "posts", "comments", "reactions"):
        await db.execute(f"DELETE FROM {table}")
    return db


async def add(db, table, created, n=1):
    for i in range(n):
        key = f"{table}-{created}-{i}"
        if table == "groups":
            await db.execute(
                "INSERT INTO groups (id, name, visibility, created_date) VALUES (?, ?, 'PUBLIC', ?)",
                (key, key, created),
            )
        elif table == "posts":
            await db.execute(
                "INSERT INTO posts (id, group_id, author_id, title, body, created_date, updated_date) "
                "VALUES (?, 'g', 'u', 't', 'b', ?, ?)",
                (key, created, created),
            )
        elif table == "comments":
            await db.execute(
                "INSERT INTO comments (id, post_id, author_id, body, created_date, updated_date) "
                "VALUES (?, 'p', 'u', 'b', ?, ?)",
                (key, created, created),
            )
        else:
            await db.execute(
                "INSERT INTO reactions (user_id, target_type, target_id, created_date) VALUES (?, 'post', ?, ?)",
                (key, key, created),
            )


def service(db):
    return EngagementAnalyticsService(EngagementRepository(db), today=lambda: TODAY)


async def test_counts_each_day_of_the_window_and_fills_empty_days(db):
    await add(db, "groups", "2026-09-24T08:00:00+00:00")
    await add(db, "posts", "2026-09-24T09:00:00Z", n=3)
    await add(db, "posts", "2026-09-20T23:59:59Z")
    await add(db, "comments", "2026-08-26T00:00:00Z", n=2)  # first day of a 30-day window
    await add(db, "likes", "2026-09-10T12:00:00Z", n=4)

    result = await service(db).engagement(30)

    assert (result["from"], result["to"], result["days"]) == ("2026-08-26", "2026-09-24", 30)
    assert len(result["daily"]) == 30
    assert result["daily"][0] == {"date": "2026-08-26", "groups": 0, "posts": 0, "comments": 2, "likes": 0}
    assert result["daily"][-1] == {"date": "2026-09-24", "groups": 1, "posts": 3, "comments": 0, "likes": 0}
    assert result["totals"] == {"groups": 1, "posts": 4, "comments": 2, "likes": 4}


async def test_the_previous_window_is_totalled_for_comparison_and_not_counted_now(db):
    await add(db, "posts", "2026-08-25T12:00:00Z", n=5)  # the day before the window
    await add(db, "posts", "2026-07-27T00:00:00Z")  # first day of the previous window
    await add(db, "posts", "2026-07-26T23:00:00Z")  # before both windows

    result = await service(db).engagement(30)
    assert result["totals"]["posts"] == 0
    assert result["previousTotals"]["posts"] == 6


async def test_days_are_kept_between_7_and_90(db):
    assert (await service(db).engagement(1))["days"] == 7
    assert (await service(db).engagement(365))["days"] == 90
    assert len((await service(db).engagement(365))["daily"]) == 90


async def test_the_response_names_the_metrics(db):
    response = service(db).build_response(await service(db).engagement(30))
    assert response["_metadata"]["metric"]["values"][0] == {"id": "groups", "value": "Groups created"}
    assert response["_metaLinks"]["self"].href.endswith("/admin/analytics/engagement?days=30")


# --- API wiring


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_MODE", "sqlite")
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "api.db"))
    from main import app

    who = {"user": AuthenticatedUser(id="clerk-a", name="Alice", email="a@x.io", role_ids=[], claims={})}
    app.dependency_overrides[get_authenticated_user] = lambda: who["user"]
    yield TestClient(app), who
    app.dependency_overrides.clear()


def test_api_is_admin_only_and_linked_from_the_admin_hub(client):
    http, who = client
    http.get("/api/me")
    assert http.get("/api/admin/analytics/engagement").status_code == 403

    who["user"] = AuthenticatedUser(id="clerk-z", name="Zed", email="z@x.io", role_ids=["ADMIN"], claims={})
    http.get("/api/me")
    hub = http.get("/api/admin").json()
    link = hub["_metaLinks"]["engagementAnalytics"]["href"]

    group = http.post("/api/groups", json={"name": "Cyclists"}).json()["_data"]["group"]
    http.post(group["links"]["createPost"]["href"], json={"title": "Lanes", "body": "Yes!"})

    response = http.get(f"{link}?days=7")
    assert response.status_code == 200
    engagement = response.json()["_data"]["engagement"]
    assert engagement["days"] == 7 and len(engagement["daily"]) == 7
    assert engagement["totals"]["groups"] >= 1 and engagement["totals"]["posts"] >= 1
    assert engagement["daily"][-1]["posts"] >= 1
