# AI search over chat history: plan

> **Bigger picture:** search over chats is now one *tool* of a general "ask your data" assistant that can also
> answer exact questions such as "how many todos are overdue?" — see [ask-your-data.md](ask-your-data.md).

> **Status:** MVP backend built — see [how-ai-search-works.md](how-ai-search-works.md) for diagrams and
> [architecture.md](architecture.md) for the big picture. Differences from this plan: vectors are stored
> in the app database (`DatabaseVectorStore`) instead of Cloudflare Vectorize (the `VectorStore` protocol
> allows swapping it in later); search routes are `/api/users/{user_id}/chats/search` and
> `.../search/reindex`. Still to do: `ask` mode, chunking, the Angular page.

Goal: let a user query their own chat data in natural language, e.g. "show me where I asked about Java".

Sending all messages to the LLM is not viable (thousands of tokens per user, growing forever). Instead we use
**RAG (retrieval-augmented generation)**: search first with embeddings, then give the AI only the few relevant snippets.

## How it works

```
Write path (on every new message)
  message -> chunk -> embed (Workers AI bge model) -> store vector + metadata in Vectorize

Query path
  "where did I ask about java?"
    -> embed the question
    -> Vectorize top-K search, filtered by user_id  (~10-20 snippets)
    -> (optional) LLM turns the snippets into an answer
    -> return answer + source links (chat id, message id)
```

Token cost stays flat regardless of how much history a user has.

## Design decisions

### 1. Vector store: Cloudflare Vectorize

- Fits the existing Cloudflare stack; has a Workers binding and a REST API; supports metadata filtering.
- Vector ID = message ID.
- Metadata: `user_id`, `chat_id`, `message_id`, `role`, `created_date`.
- Snippet text lives in D1, not in Vectorize metadata (metadata has a size limit).
- **Every query filters by `user_id`.** This is the multi-tenancy guard. Take `user_id` from the Clerk token, never from the request body.

### 2. Embedding model

`@cf/baai/bge-base-en-v1.5` (768 dimensions, cosine), called through the existing `AI` adapter (`run(model, inputs)`).

```
npx wrangler vectorize create chat-messages --dimensions=768 --metric=cosine
```

### 3. What to embed

- One vector per message; split messages over ~500 tokens into chunks.
- Very short messages ("ok thanks") embed poorly: skip them, or embed a user message together with the assistant reply as one unit.
- Also embed the chat title so queries like "my java session" match by name.

### 4. Hybrid search (keyword + vector)

"Where did I ask about *java*" is partly an exact-keyword query, and pure embeddings can be fuzzy on exact terms.

- D1 supports SQLite FTS5: run FTS5 on `chat_messages.content` and vector search in parallel.
- Merge with reciprocal rank fusion (~15 lines).
- MVP may start with vector only, then add FTS5.

### 5. Answer generation is optional

| Mode | Behaviour | LLM needed |
|------|-----------|------------|
| `find` | Ranked list of matching messages: chat name, snippet, date | No (fast, cheap) |
| `ask` | Top-K snippets passed to the LLM for a synthesized answer with citations | Yes |

Build `find` first.

## Backend plan (this project)

Follows the router -> service -> repository -> adapter layering in `PYTHON_APP_CONVENTIONS.md`.

1. **Adapter** `src/vector_store.py`: `VectorStore` protocol with `upsert`, `query`, `delete_by_ids`.
   Implementations: `VectorizeBindingAdapter` and `VectorizeHttpAdapter` (REST), mirroring `AiBindingAdapter` / `AiHttpAdapter` in `src/ai.py`.
   Add a `vectorize` binding to `wrangler.jsonc`.
2. **Embedding helper**: `embed(texts) -> list[list[float]]`, batched, using the existing AI adapter.
3. **Indexing service** `src/services/search_index_service.py`:
   - Hook into `ChatService` after `add_message`; on chat delete remove the vectors; on rename re-embed the title.
   - Run in the background (`ctx.waitUntil` in Workers) so chat latency is unaffected.
   - Add an `indexed_at` column to `chat_messages` to track state.
4. **Backfill** (endpoint or script): index existing messages in batches (Vectorize upserts up to 1000 vectors per call).
5. **Search endpoint** `POST /search` with `{ query, mode: "find" | "ask", limit }`:
   - Standard `_data` envelope.
   - `_data` = hits `{ chatId, chatTitle, messageId, snippet, score, createdDate }`; `ask` mode also returns `answer`.
6. **FTS5 migration** (phase 2): virtual table plus triggers to keep it in sync with `chat_messages`.

## Phasing

1. **MVP**: Vectorize, embed on write, backfill, `/search` in `find` mode, Angular search page.
2. **Phase 2**: hybrid FTS5 and `ask` mode with citations.
3. **Phase 3**: chunking for long messages, re-ranking, date filters ("last week"), delete/rename sync hardening.

## Risks and notes

- **Python Workers and bindings**: calling the Vectorize binding from Python goes through JS interop and can be awkward. Build the HTTP adapter alongside it (as done for AI and D1) and verify the binding works before relying on it.
- **Cost/limits**: embeddings are cheap; Vectorize and Workers AI free-tier limits are fine for a showcase.
- **Privacy**: always filter by `user_id` server-side.

## Open questions

1. Find-only first, or include `ask` (LLM answers) in the MVP?
2. Initial backfill: one-off script or admin endpoint?

See also the frontend part of this plan in `showcase/docs/ai-search-plan.md`.
