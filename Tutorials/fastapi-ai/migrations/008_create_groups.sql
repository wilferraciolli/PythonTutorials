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
