# Architecture overview

How the three Python projects, the Angular apps (showcase for the tutorials, demo-ui for fastapi-ai) and the shared services fit together.

## The projects

```mermaid
flowchart TB
    subgraph UI["demo-ui (Angular)"]
        Home[Home cards<br/>Cloudflare AI · Groq AI · AI]
        ChatUI[Chat UI]
    end

    subgraph Py["Python projects (only one runs on :8001 at a time)"]
        CF["fastapi-cloudflare-ai<br/>Workers AI only<br/>(reference)"]
        GQ["fastapi-groq-ai<br/>Groq only<br/>(reference)"]
        AIP["fastapi-ai<br/>both providers + chat search<br/>(where new work happens)"]
    end

    Clerk[(Clerk<br/>one instance)]
    D1[(D1 database demo-db<br/>one database)]

    Home --> ChatUI
    UI -- JWT --> Py
    UI -- sign in --> Clerk
    Py -- verify JWKS --> Clerk
    Py --> D1
```

All three share the same Clerk instance and the same database. Because the `chats`
table is shared, each project only lists and opens chats for the providers it owns
(`chats.provider`).

## How the UI finds things: `/me` → profile → links

The UI never builds a URL. `/me` only says who you are and points at your profile;
the profile holds every link, built from the user id in the path. That is also where
"may this caller see this user's resources?" belongs.

```mermaid
sequenceDiagram
    actor U as Browser
    participant Me as GET /api/me
    participant P as GET /api/users/{id}/profile
    participant C as GET /api/users/{id}/chats

    U->>Me: Bearer token (Clerk)
    Note over Me: find users row by Clerk id,<br/>create it on first call
    Me-->>U: id, name, email, roles<br/>links: self, userProfile
    U->>P: follow userProfile link
    Note over P: can_view_profile(caller, target)
    P-->>U: id, externalId, name, email, roleIds<br/>links: users, searchUsers, aiChats, aiChatSearch, …
    U->>C: follow aiChats link
    C-->>U: chats (each with self / updateTitle / sendMessage / delete links)
```

A Home card is shown only if its link (`cloudflareChats`, `groqChats`, `aiChats`) is on
the profile; otherwise it says "Not found" — meaning "that project isn't the one
answering".

## Users are created on first sign-in

```mermaid
flowchart LR
    S[User registers with Clerk] --> T[UI gets a token]
    T --> Me["GET /api/me<br/>(or any other route)"]
    Me --> Q{users row with<br/>this Clerk id?}
    Q -- yes --> A[add any new Clerk roles<br/>never remove one]
    Q -- no --> N[create users row + roles<br/>copy of the Clerk identity]
    N --> R[return it]
    A --> R
```

So the `users` table is a local copy of Clerk users who have called the API at least
once. `/me` does this, and so does `ensure_current_user` (`users/dependencies.py`), which
`main.py` runs before every other router, so a route always finds its caller. After
that, roles are ours: permissions read the saved roles, and admins grant or revoke them
through `PUT /api/users/{id}`. `GET /api/users` lists users and
`GET /api/users/search?q=` finds them by name or email.

## Layers (every project)

```mermaid
flowchart LR
    Router[Router<br/>HTTP, auth deps] --> Service[Service<br/>business rules, links,<br/>metadata, envelope]
    Service --> Repo[Repository<br/>SQL]
    Repo --> DB{{Database protocol}}
    DB --> SQLite[SQLite<br/>local / Docker]
    DB --> D1B[D1 binding<br/>in a Worker]
    DB --> D1H[D1 over HTTP<br/>anywhere]
    Service --> AIp{{AI protocol}}
    AIp --> Bind[Workers AI binding]
    AIp --> Http[Workers AI REST]
    AIp --> Groq[Groq adapter]
```

The service layer doesn't know which adapter is behind the protocols, which is what
lets the same code run locally and in a Cloudflare Worker.

The code is organised by domain (`users/`, `todos/`, `chats/`, `groups/posts/comments/`,
...), each with its router, service, repository, `models.py` (database rows),
`schemas.py` (Request, DTO, Metadata and the typed `ApiResponse`) and `constants.py`.
Cross-cutting code lives in `core/` and never imports a domain. See the README's
"Code conventions".

## Who may see what (business-logic seams)

```mermaid
flowchart TD
    Req[Request with user id in the path] --> Caller["get_caller():<br/>Clerk token → saved user + roles"]
    Caller --> Profile{{"/users/{id}/profile<br/>can_view_profile(caller, target)<br/>currently: allow"}}
    Caller --> Chats{{"/users/{id}/chats, todos, assistant, settings<br/>require_owner() / NotOwnerError<br/>owner only, not even admins, else 403"}}
    Caller --> Admin{{"/users writes, /admin/…<br/>require_admin()<br/>saved ADMIN role, else 403"}}
```

These are the places to add rules such as "admins can see anyone" or "members of a team
can see each other's chats". The profile only offers links the caller may follow:
personal ones on your own profile, admin ones to admins.

## Chat and search together

```mermaid
flowchart LR
    Send[Send message] --> Reply[LLM reply<br/>Workers AI or Groq]
    Reply --> Save[(chat_messages)]
    Save --> Idx[Embed + store vector]
    Idx --> Vec[(message_embeddings)]
    Ask[Search query] --> Vec
    Ask --> Save
```

Details: [how-ai-search-works.md](how-ai-search-works.md). For questions about any data
(todos, counts, dates) see [ask-your-data.md](ask-your-data.md).
