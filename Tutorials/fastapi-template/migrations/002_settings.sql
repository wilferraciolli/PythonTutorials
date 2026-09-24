CREATE TABLE IF NOT EXISTS region_settings (
    id                      TEXT PRIMARY KEY,
    owner_type              TEXT NOT NULL,
    timezone                TEXT NOT NULL,
    language                TEXT NOT NULL,
    currency                TEXT NOT NULL,
    theme                   TEXT NOT NULL
);

INSERT INTO region_settings (id, owner_type, timezone, language, currency,theme)
VALUES ('92aaba5a-d56d-4128-8140-96f138e817bf', 'SYSTEM', 'Europe/London', 'en-GB', 'GBP', 'light');


CREATE TABLE IF NOT EXISTS configuration_settings (
    id                      TEXT PRIMARY KEY,
    setting_type            TEXT NOT NULL,
    enabled                 BOOLEAN NOT NULL
);

INSERT INTO configuration_settings (id, setting_type, enabled)
VALUES ('e41ee356-fe48-4d22-a4e1-680149c6c31d', 'AUTH', 1);
