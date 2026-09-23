ALTER TABLE chats ADD COLUMN provider TEXT NOT NULL DEFAULT 'cloudflare';
ALTER TABLE chats ADD COLUMN model TEXT NOT NULL DEFAULT '@cf/meta/llama-3.1-8b-instruct';