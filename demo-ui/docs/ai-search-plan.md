# AI search over chat history: frontend plan

Companion to the backend plan in `Tutorials/fastapi-cloudflare-ai/docs/ai-search-plan.md`. That document explains the
approach (embeddings + Vectorize, RAG, hybrid keyword search) and the `POST /search` API this page consumes.

## Summary of the approach

Users have chat sessions (name + messages). Sending all of it to an AI is not viable, so the backend embeds each
message on write, stores vectors in Cloudflare Vectorize (filtered by `user_id`), and at query time retrieves only the
top-K relevant snippets. The frontend only needs to call one search endpoint and render the results.

## Plan

- Add a route `features/workers-ai/search/` next to `chat-list` and `chat-thread` (register in `app.routes.ts`).
- Add `search.store.ts` using signals, following the pattern in `chats.store.ts`.
- UI:
  - Search box plus a **find / ask** toggle.
  - Result list: each hit shows the snippet with the query highlighted, the chat name and the date.
  - Clicking a hit opens `chat-thread` scrolled to that message (`chatId`, `messageId`).
  - In `ask` mode, show the synthesized answer on top with its sources listed below.
- Handle loading, empty and error states; debounce or submit-on-enter to avoid needless embedding calls.
- Follow `frontend-conventions.md` in this folder.

## API contract (from the backend)

`POST /search` with `{ query, mode: "find" | "ask", limit }`

Response `_data`: hits `{ chatId, chatTitle, messageId, snippet, score, createdDate }`; `ask` mode also returns `answer`.

## Phasing

1. **MVP**: search page in `find` mode.
2. **Phase 2**: `ask` mode with citations.
3. **Phase 3**: date filters ("last week"), scroll-to-message polish.
