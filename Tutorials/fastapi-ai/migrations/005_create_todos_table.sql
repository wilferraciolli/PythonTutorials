-- Same table the fastapi-cloudflare-d1 project owns (shared D1 database).
-- Created here only so the AI assistant's todo tools work on a fresh local
-- SQLite file; IF NOT EXISTS makes it a no-op against the shared D1.
CREATE TABLE IF NOT EXISTS todos (
    id                      TEXT PRIMARY KEY,
    user_id                 TEXT NOT NULL,
    title                   TEXT NOT NULL,
    description             TEXT,
    complete_by             TEXT NOT NULL,
    state                   TEXT NOT NULL DEFAULT 'NEW',
    created_date            TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_todos_user_id ON todos(user_id);
