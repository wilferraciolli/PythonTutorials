CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    created_date TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id TEXT NOT NULL,
    role_id TEXT NOT NULL,
    PRIMARY KEY (user_id, role_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

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

CREATE TABLE IF NOT EXISTS tags (
    id                      TEXT PRIMARY KEY,
    resource_id             TEXT NOT NULL,
    tag                     TEXT NOT NULL,
    created_date            TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_resource_tag ON tags(resource_id, tag);
