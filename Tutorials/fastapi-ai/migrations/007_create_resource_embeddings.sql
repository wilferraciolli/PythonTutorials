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
