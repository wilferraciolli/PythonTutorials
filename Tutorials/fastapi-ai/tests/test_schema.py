"""
schema.sql (applied by hand to D1) must build the same database as the
migrations (applied automatically to local SQLite). A fresh D1 created from
an out-of-date schema.sql silently lacks tables: that is how `todos` went
missing and every todo tool failed.
"""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = "010_seed_news_group.sql"  # data, not schema


def describe(conn: sqlite3.Connection) -> dict:
    objects = conn.execute(
        "SELECT type, name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' AND name != 'schema_migrations'"
    ).fetchall()
    shape = {}
    for kind, name in objects:
        if kind == "table":
            columns = conn.execute(f"PRAGMA table_info({name})").fetchall()
            shape[(kind, name)] = sorted((c[1], c[2].upper(), c[3], c[5]) for c in columns)
        else:
            shape[(kind, name)] = None
    return shape


def test_schema_sql_matches_the_migrations(tmp_path):
    migrated = sqlite3.connect(tmp_path / "migrated.db")
    for migration in sorted((ROOT / "migrations").glob("*.sql")):
        if migration.name != SEED:
            migrated.executescript(migration.read_text(encoding="utf-8"))

    from_schema = sqlite3.connect(tmp_path / "schema.db")
    from_schema.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))

    expected, actual = describe(migrated), describe(from_schema)
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    assert not missing, f"schema.sql is missing {missing}"
    assert not extra, f"schema.sql has objects no migration creates: {extra}"
    for key in expected:
        assert actual[key] == expected[key], f"{key} differs between schema.sql and the migrations"


def test_schema_sql_can_be_run_twice(tmp_path):
    # It's re-run by hand on D1, so every statement must be IF NOT EXISTS.
    conn = sqlite3.connect(tmp_path / "twice.db")
    script = (ROOT / "schema.sql").read_text(encoding="utf-8")
    conn.executescript(script)
    conn.executescript(script)
