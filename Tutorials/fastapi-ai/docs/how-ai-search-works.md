# How AI search works

Search over a user's chat history: "show me where I asked about Java".

We can't send thousands of messages to an LLM, so we **retrieve first**: turn every
message into an *embedding* (a list of numbers that captures its meaning), and at
search time find the messages whose numbers are closest to the question's.

> Chat search is one tool of the wider assistant in [ask-your-data.md](ask-your-data.md).

> **Status:** MVP is built and tested (`find` mode). Not built yet: `ask` mode (LLM
> answer with citations), Cloudflare Vectorize adapter, chunking of long messages,
> the Angular search page. See [ai-search-plan.md](ai-search-plan.md).

## The idea in one picture

```mermaid
flowchart LR
    subgraph Write["Write path (every message)"]
        M[New chat message] --> E1[Embed<br/>Workers AI bge model]
        E1 --> S[(message_embeddings)]
    end

    subgraph Read["Read path (a search)"]
        Q["'where did I ask about java?'"] --> E2[Embed the question]
        E2 --> V[Vector search<br/>closest meaning]
        Q --> K[Keyword search<br/>LIKE '%java%']
        S -.-> V
        V --> R[Merge with<br/>reciprocal rank fusion]
        K --> R
        R --> H[Ranked hits:<br/>chat title, snippet, link]
    end
```

Only the few best snippets ever leave the database, so cost and latency stay flat
however much history a user has.

## Write path: indexing a message

Happens inside `ChatService.send_message`, right after the assistant replies.

```mermaid
sequenceDiagram
    actor U as User
    participant API as chats router
    participant CS as ChatService
    participant LLM as Chat model<br/>(Workers AI or Groq)
    participant SS as SearchService
    participant AI as Workers AI<br/>(embeddings)
    participant VS as VectorStore<br/>(message_embeddings)

    U->>API: POST /users/{id}/chats/{chat}/messages
    API->>CS: send_message()
    CS->>LLM: chat history + new message
    LLM-->>CS: reply
    CS->>CS: save user + assistant messages
    CS->>SS: index_messages(both)
    SS->>AI: embed(texts)
    AI-->>SS: vectors
    SS->>VS: upsert(vectors, user_id, chat_id)
    CS-->>U: updated chat
    Note over CS,SS: Indexing is best effort: if it fails the<br/>chat still succeeds, and reindex catches up later
```

- Embeddings always come from Workers AI (`CF_EMBEDDING_MODEL`, default
  `@cf/baai/bge-base-en-v1.5`, 768 dimensions), even when a chat is answered by Groq.
- Long messages are truncated to 2000 characters for now (chunking is a later phase).
- Deleting a chat also deletes its vectors.
- `POST /users/{id}/chats/search/reindex` embeds any messages not indexed yet
  (existing history, or anything a failed call missed).

## Read path: answering a search

`GET /users/{id}/chats/search?q=java&limit=10`

```mermaid
sequenceDiagram
    actor U as User
    participant API as chats router
    participant SS as SearchService
    participant AI as Workers AI
    participant VS as VectorStore
    participant DB as chat_messages

    U->>API: GET .../chats/search?q=java
    API->>API: caller must own {user_id} (403 otherwise)
    API->>SS: search(user_id, "java")
    SS->>AI: embed("java")
    AI-->>SS: query vector
    par by meaning
        SS->>VS: closest vectors WHERE user_id = ?
        VS-->>SS: ranked message ids
    and by keyword
        SS->>DB: content LIKE '%java%' AND user_id = ?
        DB-->>SS: ranked messages
    end
    SS->>SS: reciprocal rank fusion
    SS->>DB: load top messages + chat titles
    SS-->>U: hits
```

### Why two searches?

| | Finds | Misses |
|---|---|---|
| **Vector** (meaning) | "Spring Boot", "the JVM" for the query "java" | Exact rare words, IDs, names |
| **Keyword** (`LIKE`) | Messages that literally say "java" | Anything phrased differently |

Together they cover both. Each returns a ranked list; **reciprocal rank fusion**
merges them without having to compare their incompatible scores:

```
score(message) = Σ over lists of  1 / (60 + rank in that list)
```

A message near the top of *both* lists wins; a message in only one still appears.
Each hit says whether it was also a `keywordMatch`.

### What a hit looks like

```json
{
  "_data": { "hits": [{
    "messageId": "…", "chatId": "…", "chatTitle": "Java help",
    "role": "user", "snippet": "How do I use the JVM?",
    "score": 0.0323, "keywordMatch": false,
    "created_date": "2026-01-01T00:00:00Z",
    "links": { "chat": { "href": "/api/users/{id}/chats/{chatId}", "method": "GET" } }
  }]},
  "_metaLinks": { "search": {…}, "reindex": {…} }
}
```

## Data model

```mermaid
erDiagram
    users ||--o{ chats : owns
    chats ||--o{ chat_messages : contains
    chat_messages ||--o| message_embeddings : "indexed as"
    users ||--o{ message_embeddings : "scopes (tenancy)"

    message_embeddings {
        text message_id PK
        text chat_id
        text user_id "always in the WHERE clause"
        text model "embedding model used"
        text embedding "JSON floats, L2-normalised"
        text created_date
    }
```

A row in `message_embeddings` means "this message is indexed". Vectors are stored
normalised, so cosine similarity is a plain dot product.

## Code map

```mermaid
flowchart TD
    R[routers/chats.py<br/>GET /chats/search<br/>POST /chats/search/reindex] --> SS[services/search_service.py<br/>index, reindex, search, RRF]
    CS[services/chat_service.py<br/>indexes after a reply,<br/>removes on delete] --> SS
    SS --> EMB[embeddings.py<br/>embed() via Workers AI]
    SS --> VS[vector_store.py<br/>VectorStore protocol]
    SS --> CR[repositories/chat_repository.py<br/>keyword search, message loading]
    VS --> DVS[DatabaseVectorStore<br/>SQLite / D1]
    VS -.future.-> VEC[Cloudflare Vectorize adapter]
    EMB --> AI[ai.py AI protocol]
```

`VectorStore` is a protocol, the same pattern as `Database` and `AI`: the search
service doesn't know where vectors live.

## Why the database is the vector store (for now)

The plan called for Cloudflare Vectorize. The MVP stores vectors in the same
SQLite/D1 database and ranks them in Python (brute-force cosine over **one user's**
rows), because:

- it runs the same locally and deployed, with no extra infrastructure;
- it is fully testable offline;
- one user's history (thousands of messages) is small enough for this.

When that stops being true — very large histories, or a Worker's CPU limit — add a
Vectorize adapter that implements `VectorStore`; nothing else changes.

## Running the tests

```powershell
cd Tutorials/fastapi-ai
uv run pytest
```

The tests use a fake embedder (words mapped onto a few topic axes) and a temporary
SQLite file, so they need no network or Cloudflare account. They check: finding by
meaning with no shared words, keyword matches, per-user isolation, reindex only
filling gaps, chat deletion removing vectors, blank queries and the limit.
