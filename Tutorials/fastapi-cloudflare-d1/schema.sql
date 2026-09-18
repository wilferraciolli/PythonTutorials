CREATE TABLE IF NOT EXISTS todos (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    title                   TEXT NOT NULL,
    description             TEXT,
    complete_by             TEXT NOT NULL,
    state                   TEXT NOT NULL DEFAULT 'NEW',
    created_date            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tags (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id             INTEGER NOT NULL,
    tag                     TEXT NOT NULL,
    created_date            TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_resource_tag ON tags(resource_id, tag);
