-- Owned by the same shared database as todos. IF NOT EXISTS keeps it a no-op where they already exist.
CREATE TABLE IF NOT EXISTS tags (
    id                      TEXT PRIMARY KEY,
    resource_id             TEXT NOT NULL,
    tag                     TEXT NOT NULL,
    created_date            TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_resource_tag ON tags(resource_id, tag);

-- Joins tags to the resources they're attached to, so a tag can be shown
-- (and searched) by its resource's human-readable name instead of a raw
-- resource_id. LEFT JOIN so a tag on an unrecognised/deleted resource still
-- comes back (resource_name is just NULL) rather than disappearing.
--
-- todos is the only taggable resource today. When a second one exists,
-- extend this with `UNION ALL` against that table the same way, keeping
-- one row per tag.
CREATE VIEW IF NOT EXISTS tag_resource_view AS
SELECT
    tags.id             AS tag_id,
    tags.tag            AS tag_name,
    tags.resource_id    AS resource_id,
    todos.title          AS resource_name,
    tags.created_date   AS created_date
FROM tags
LEFT JOIN todos ON todos.id = tags.resource_id;
