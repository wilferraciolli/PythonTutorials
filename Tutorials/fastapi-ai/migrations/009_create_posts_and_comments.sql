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
    deleted_date TEXT
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
