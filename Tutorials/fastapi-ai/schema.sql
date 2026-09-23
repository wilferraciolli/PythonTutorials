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

-- Search embeddings for any resource (todos, ...)
-- Embeddings for any user-owned resource that has free text worth searching by
-- meaning (todos today; notes, tags, ... later). One row per resource;
-- `resource_type` says which table `resource_id` points into. `embedding` is a
-- JSON array of floats (L2-normalised). Chat messages keep their own table
-- (message_embeddings).
CREATE TABLE IF NOT EXISTS resource_embeddings (
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    model TEXT NOT NULL,
    embedding TEXT NOT NULL,
    created_date TEXT NOT NULL,
    PRIMARY KEY (resource_type, resource_id)
);

CREATE INDEX IF NOT EXISTS idx_resource_embeddings_user_type
    ON resource_embeddings(user_id, resource_type);

-- Social groups: see docs/social-groups.md.
-- owner_id is optional: a group carries on when its owner's user is deleted.
CREATE TABLE IF NOT EXISTS groups (
    id           TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    description  TEXT,
    visibility   TEXT NOT NULL DEFAULT 'PUBLIC' CHECK (visibility IN ('PUBLIC', 'PRIVATE')),
    owner_id     TEXT,
    created_by   TEXT,
    created_date TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_groups_name ON groups(name COLLATE NOCASE);

CREATE TABLE IF NOT EXISTS group_members (
    group_id    TEXT NOT NULL,
    user_id     TEXT NOT NULL,
    joined_date TEXT NOT NULL,
    PRIMARY KEY (group_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_id);

-- Independent of membership: people can follow a public group without joining,
-- and members can unfollow without leaving.
CREATE TABLE IF NOT EXISTS group_followers (
    group_id     TEXT NOT NULL,
    user_id      TEXT NOT NULL,
    created_date TEXT NOT NULL,
    PRIMARY KEY (group_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_group_followers_user ON group_followers(user_id);

-- Posts and threaded comments in social groups: see docs/social-groups.md.
-- author_id NULL means "System" (seeded content). A deleted user's id is kept,
-- so their old posts show as "[deleted user]" instead of "System".
-- Deleting a post or comment is a soft delete (deleted_date) so replies keep their parent.
CREATE TABLE IF NOT EXISTS posts (
    id           TEXT PRIMARY KEY,
    group_id     TEXT NOT NULL,
    author_id    TEXT,
    title        TEXT NOT NULL,
    body         TEXT NOT NULL,
    created_date TEXT NOT NULL,
    updated_date TEXT NOT NULL,
    deleted_date TEXT,
    -- Optional media (migration 012). A D1 that already has `posts` needs
    -- migrations/012_add_post_media.sql run once, since CREATE IF NOT EXISTS skips it.
    media_type        TEXT CHECK (media_type IN ('UNSPLASH', 'GIPHY', 'YOUTUBE')),
    media_id          TEXT,
    media_url         TEXT,
    media_title       TEXT,
    media_author_name TEXT,
    media_author_url  TEXT
);

CREATE INDEX IF NOT EXISTS idx_posts_group_created ON posts(group_id, created_date);
CREATE INDEX IF NOT EXISTS idx_posts_created ON posts(created_date);

CREATE TABLE IF NOT EXISTS comments (
    id                TEXT PRIMARY KEY,
    post_id           TEXT NOT NULL,
    parent_comment_id TEXT,
    author_id         TEXT,
    body              TEXT NOT NULL,
    created_date      TEXT NOT NULL,
    updated_date      TEXT NOT NULL,
    deleted_date      TEXT
);

CREATE INDEX IF NOT EXISTS idx_comments_post ON comments(post_id, created_date);

-- Likes and post popularity: see docs/social-groups.md.

-- One like per user per post or comment (the primary key stops double likes).
CREATE TABLE IF NOT EXISTS reactions (
    user_id      TEXT NOT NULL,
    target_type  TEXT NOT NULL CHECK (target_type IN ('post', 'comment')),
    target_id    TEXT NOT NULL,
    created_date TEXT NOT NULL,
    PRIMARY KEY (user_id, target_type, target_id)
);

CREATE INDEX IF NOT EXISTS idx_reactions_target ON reactions(target_type, target_id);

-- Each post's counts and popularity score, kept up to date by the services
-- whenever a like or comment changes, so POPULAR doesn't count on every request.
-- score = comment_count * 2 + like_count (a comment or reply is worth 2, a like 1).
CREATE TABLE IF NOT EXISTS post_stats (
    post_id       TEXT PRIMARY KEY,
    like_count    INTEGER NOT NULL DEFAULT 0,
    comment_count INTEGER NOT NULL DEFAULT 0,
    score         INTEGER NOT NULL DEFAULT 0,
    updated_date  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_post_stats_score ON post_stats(score);

-- Seed data (the News group and its dummy posts) lives in migrations/010_seed_news_group.sql;
-- on D1 run it once: npx wrangler d1 execute wiltech-db --remote --file=./migrations/010_seed_news_group.sql
-- then, as an admin, call POST /api/admin/post-stats/rebuild so the seeded posts get their comment counts.
