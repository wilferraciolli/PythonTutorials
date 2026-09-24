-- Region settings (timezone, language, currency, theme). One SYSTEM row holds
-- the defaults (admins change it at /admin/settings); a user who saves their
-- own gets a USER row whose id is their user id, and falls back to SYSTEM
-- until then (or after resetting).
CREATE TABLE IF NOT EXISTS region_settings (
    id                      TEXT PRIMARY KEY,
    owner_type              TEXT NOT NULL,
    timezone                TEXT NOT NULL,
    language                TEXT NOT NULL,
    currency                TEXT NOT NULL,
    theme                   TEXT NOT NULL
);

INSERT INTO region_settings (id, owner_type, timezone, language, currency, theme)
VALUES ('92aaba5a-d56d-4128-8140-96f138e817bf', 'SYSTEM', 'Europe/London', 'en-GB', 'GBP', 'light');
