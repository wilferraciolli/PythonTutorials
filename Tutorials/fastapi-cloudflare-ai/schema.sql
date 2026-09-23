CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    external_user_id TEXT UNIQUE,
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
