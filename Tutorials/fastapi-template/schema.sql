-- Consolidated snapshot of migrations/*.sql (001, 002). Keep in sync when adding a migration.

-- 001_create_users_table.sql
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

-- 002_settings.sql
CREATE TABLE IF NOT EXISTS region_settings (
    id                      TEXT PRIMARY KEY,
    owner_type              TEXT NOT NULL,
    timezone                TEXT NOT NULL,
    language                TEXT NOT NULL,
    currency                TEXT NOT NULL,
    theme                   TEXT NOT NULL
);

INSERT OR IGNORE INTO region_settings (id, owner_type, timezone, language, currency, theme)
VALUES ('92aaba5a-d56d-4128-8140-96f138e817bf', 'SYSTEM', 'Europe/London', 'en-GB', 'GBP', 'light');

CREATE TABLE IF NOT EXISTS configuration_settings (
    id                      TEXT PRIMARY KEY,
    setting_type            TEXT NOT NULL,
    enabled                 BOOLEAN NOT NULL
);

INSERT OR IGNORE INTO configuration_settings (id, setting_type, enabled)
VALUES ('e41ee356-fe48-4d22-a4e1-680149c6c31d', 'AUTH', 1);
