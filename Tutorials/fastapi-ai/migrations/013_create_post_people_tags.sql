-- People tagged in a post: see docs/social-groups.md "Tagging people".
-- One row per post per tagged user. The author sets the whole list when
-- creating or editing the post; tags of a deleted user drop out of responses.
CREATE TABLE IF NOT EXISTS post_people_tags (
    post_id      TEXT NOT NULL,
    user_id      TEXT NOT NULL,
    created_date TEXT NOT NULL,
    PRIMARY KEY (post_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_post_people_tags_user ON post_people_tags(user_id);
