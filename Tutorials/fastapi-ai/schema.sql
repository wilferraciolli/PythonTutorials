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

CREATE TABLE IF NOT EXISTS chats (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT 'cloudflare',
    model TEXT NOT NULL DEFAULT '@cf/meta/llama-3.1-8b-instruct',
    created_date TEXT NOT NULL,
    updated_date TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_date TEXT NOT NULL,
    FOREIGN KEY (chat_id) REFERENCES chats(id)
);

CREATE INDEX IF NOT EXISTS idx_chat_messages_chat_id ON chat_messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_chats_user_id ON chats(user_id);

CREATE TABLE IF NOT EXISTS message_embeddings (
    message_id TEXT PRIMARY KEY,
    chat_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    model TEXT NOT NULL,
    embedding TEXT NOT NULL,
    created_date TEXT NOT NULL,
    FOREIGN KEY (message_id) REFERENCES chat_messages(id)
);

CREATE INDEX IF NOT EXISTS idx_message_embeddings_user_id ON message_embeddings(user_id);
CREATE INDEX IF NOT EXISTS idx_message_embeddings_chat_id ON message_embeddings(chat_id);

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
