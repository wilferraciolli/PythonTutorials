# Ask your data (AI assistant with tools)

Goal: let a user ask questions about **any** of their data in plain English:

- "Show me where I asked about Java" — fuzzy, about meaning
- "How many todos are overdue?" — exact, needs counting
- "How many are new, and which is due first?" — several lookups in one question

> **Status:** built and tested with a scripted fake model (11 tests). Not yet run against
> a real Groq / Workers AI model, and no Angular page yet.

## Why embeddings alone are not enough

Embeddings answer "find things *like* this". They cannot count, filter by date or
compare — an LLM guessing "you have 7 overdue todos" from a few retrieved snippets
would be making it up. So there are two kinds of question and two kinds of tool:

| Question | Right tool | How |
|---|---|---|
| "where did I ask about java?" | `search_chats` | embeddings + keyword ([details](how-ai-search-works.md)) |
| "how many todos are overdue?" | `count_todos` | a plain query; the database does the counting |
| "what's due first?" | `list_todos` | a plain query, sorted |

The LLM's job is only to **pick the tools and write the answer**; the numbers always
come from the database.

## How a question is answered

`POST /api/users/{id}/assistant/ask` with `{"question": "...", "provider": "groq"}`

```mermaid
sequenceDiagram
    actor U as User
    participant R as assistant router
    participant A as AssistantService
    participant L as LLM (Groq or Workers AI)
    participant T as Tools
    participant D as Database

    U->>R: "how many todos are overdue?"
    R->>R: caller must own {user_id} (403 otherwise)
    R->>A: ask(user_id, question)
    A->>L: system prompt (today's date) + question + tool list
    L-->>A: call count_todos(overdue=true)
    A->>T: run as user_id from the URL
    T->>D: SELECT the user's todos
    D-->>T: rows
    T-->>A: {"count": 2}
    A->>L: tool result
    L-->>A: "You have 2 overdue todos."
    A-->>U: answer + toolCalls (what it ran)
```

The loop repeats while the model keeps asking for tools (up to 5 steps), so
"how many are new **and** which is due first?" becomes two tool calls in one answer.

## How a question is mapped to data (no embedding of the question involved)

Choosing what to look at is **not** done by embeddings or keyword rules. It is done by
the LLM through *tool calling*:

1. Every request sends the model the list of tools: each has a **name, a plain-English
   description and a JSON schema** for its arguments (see `assistant/todo_tools.py`).
2. The model reads the question and those descriptions and replies, instead of text,
   with "call `count_todos` with `{"overdue": true}`". That is a structured request,
   not free text, so the server can validate it.
3. The server runs the matching handler with the user id from the URL and sends the
   result back; the model either asks for more tools or writes the final answer.

So the descriptions **are** the mapping: they are the only thing telling the model that
"overdue" means `count_todos(overdue=true)`. Write them like documentation for a new
colleague. Words like "overdue" are turned into arguments by the model; the *meaning* of
overdue (past `complete_by` and not `CLOSED`) is fixed in code, so it is always
consistent.

Embeddings are used in exactly one place: the `search_chats` tool, to rank chat messages
against the search text. Todos and tags are **not** embedded; they are queried directly.

### When would a resource need embedding?

| The question is about... | Use | Example |
|---|---|---|
| Exact fields: counts, states, dates | A query tool | "how many are overdue?" |
| Free text you must match by meaning | Embeddings | "todos about the tax return" when titles say "HMRC self-assessment" |
| Both | Both, in one tool | "overdue todos about tax" |

Embed a resource only if it has free text worth matching by meaning (a todo's title and
description, a note). Reuse the same pieces as chats: a row in `message_embeddings`-style
table per resource, written when it is created or edited and removed when it is deleted,
searched by a `search_todos` tool. Counting and filtering stay in SQL either way.

## Adding a new data source

A source is just a `Tool`: a name, a description the model reads, a JSON schema for the
arguments, and an async handler.

```mermaid
flowchart LR
    Q[Question] --> LLM{LLM picks tools}
    LLM --> T1[count_todos<br/>list_todos]
    LLM --> T2[search_chats]
    LLM -.add one.-> T3[your new tool<br/>e.g. users, tags, ...]
    T1 --> DB1[(todos)]
    T2 --> V[(message_embeddings<br/>chat_messages)]
    T3 -.-> DB3[(any table)]
    T1 --> LLM
    T2 --> LLM
    LLM --> Ans[Answer + tools used]
```

Steps: write `build_xxx_tools(...)` in `src/assistant/`, and add it to the list in
`routers/assistant.py`. No prompt or loop changes.

Tool design tips:

- Prefer a few tools with filters (`count_todos(state, overdue)`) over many narrow ones.
- Return small, JSON-friendly results (the loop truncates at 6000 characters).
- Return `{"error": "..."}` for bad arguments; the model sees it and retries.
- Keep tools **read-only**. Writes ("mark those closed") need a confirmation step; not built.

## Safety rules the server enforces

```mermaid
flowchart TD
    Q[Model asks for a tool] --> V1{Known tool?}
    V1 -- no --> E[error result to the model]
    V1 -- yes --> V2{Arguments valid JSON object?}
    V2 -- no --> E
    V2 -- yes --> H[handler runs with user_id from the URL]
    H --> R[result, truncated] --> M[back to the model]
```

- **The model never chooses whose data.** `user_id` comes from the URL (which the
  router has already checked belongs to the caller). A `user_id` in the model's
  arguments is ignored — there is a test for this.
- **Read-only** tools, so a bad prompt can leak nothing outside the user's own data
  and change nothing.
- **Prompt injection:** a chat message the model retrieves might say "ignore your
  instructions". The system prompt says tool results are data, not instructions, and
  because tools are read-only and user-scoped the worst case is a wrong answer.
- **Step limit** of 5 stops runaway loops.
- **Transparency:** the response includes `toolCalls` (name, arguments, result), so a
  UI can show "I ran `count_todos(overdue=true)` → 2".

## Provider notes

Both providers are called through their OpenAI-compatible chat-completions API
(`llm.py`), so one client serves both:

| Provider | Endpoint | Notes |
|---|---|---|
| `groq` (default) | `GROQ_BASE_URL` | `GROQ_MODEL` (gpt-oss-20b) supports tool calling well |
| `cloudflare` | `https://api.cloudflare.com/client/v4/accounts/{CF_AI_ACCOUNT_ID}/ai/v1` | Needs the REST credentials (not the binding). Small models like Llama 3.1 8B call tools less reliably |

Tool calling quality varies by model. If answers look wrong, look at `toolCalls` first:
did the model pick the right tool and arguments?

## Code map

```mermaid
flowchart TD
    R[routers/assistant.py<br/>POST /assistant/ask] --> S[services/assistant_service.py<br/>the tool loop]
    S --> LLM[llm.py<br/>OpenAICompatibleLlm]
    S --> Tools[assistant/tools.py<br/>Tool]
    R --> TT[assistant/todo_tools.py<br/>count_todos, list_todos]
    R --> CT[assistant/chat_tools.py<br/>search_chats]
    TT --> TR[repositories/todo_repository.py<br/>read-only]
    CT --> SS[services/search_service.py]
```

Todos are owned by `fastapi-cloudflare-d1` and live in the shared database; this project
only reads them (migration `005` just creates the table on a fresh local SQLite file).

## Testing

```powershell
cd Tutorials/fastapi-ai
uv run pytest
```

`tests/test_assistant.py` scripts the model's turns, so it checks the *server's*
behaviour with no network: overdue counting (including a closed past-due todo and a
`Z`-suffixed date), other users' data excluded, `user_id` in arguments ignored, bad
state / unknown tool / invalid JSON handled, chat search as a tool, step limit, and
today's date in the prompt.
