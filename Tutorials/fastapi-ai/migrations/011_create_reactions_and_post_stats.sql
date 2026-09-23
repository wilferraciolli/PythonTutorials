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

-- Backfill posts that already exist (e.g. the seeded News posts).
INSERT OR IGNORE INTO post_stats (post_id, like_count, comment_count, score, updated_date)
SELECT
    p.id,
    0,
    (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.deleted_date IS NULL),
    (SELECT COUNT(*) FROM comments c WHERE c.post_id = p.id AND c.deleted_date IS NULL) * 2,
    strftime('%Y-%m-%dT%H:%M:%SZ', 'now')
FROM posts p;
