-- One embedding per chat message, used for AI search over a user's chats.
-- A row's presence means the message is indexed. `embedding` is a JSON
-- array of floats (L2-normalised), so cosine similarity is a dot product.
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
