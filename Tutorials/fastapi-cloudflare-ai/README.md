# FastAPI Cloudflare Workers AI — portable FastAPI with SQLite + Workers AI

This app keeps the same portability pattern as the sibling
[`fastapi-cloudflare-d1`](../fastapi-cloudflare-d1) project:

- **Local uvicorn/Docker** uses SQLite through the shared `Database` protocol
  for user records.
- **Cloudflare Workers** can use the native D1 binding (`env.DB`) through the
  same protocol, and reaches **Workers AI** through the native `env.AI`
  binding declared in `wrangler.jsonc`.

The repository layer does not know whether the database is SQLite or
Cloudflare D1, and application code that calls Workers AI should stay behind
its own small adapter, the same way `database.py` abstracts SQLite vs. D1.

## Status

✅ **Working end to end, locally.** Auth, user records, and a ChatGPT-style
`/api/chats` feature (list chats, open one, send a message, get an AI reply)
are all wired up and tested against real Workers AI. Not yet deployed — see
"Deploying to Cloudflare" below once you're ready.

> **Runs on port 8001 — same as every other Python tutorial project in this
> repo** (`fastapi-cloudflare-d1`, `fastapi-template`, ...). The `showcase`
> Angular app's API base URL is a single fixed value, not one per backend, so
> only one of these services is ever meant to run locally at a time. Stop
> whichever one is running before starting this one.

## Why a separate project?

Same reasoning as `fastapi-cloudflare-d1`: routers, services, DTOs, the
response envelope, metadata/links/templates, UUIDs, and UTC date formatting
are reused patterns, not reinvented per project, so this app can move to
Docker, Render, or another host without touching business logic.

## Project Structure

```
fastapi-cloudflare-ai/
├── src/
│   ├── entry.py                 # FastAPI app + Workers ASGI entrypoint
│   ├── main.py                  # Plain FastAPI app for uvicorn/Docker; wires
│   │                             # routers + the Clerk auth dependency
│   ├── auth.py                  # Clerk JWT verification (JWKS fetch/cache)
│   ├── database.py              # SQLite, D1 binding, and D1 HTTP adapters
│   ├── config.py                # Runtime config from Worker env / .env / OS env
│   ├── api_response.py          # Shared response envelope model + API_PREFIX
│   ├── ai.py                    # Portable AI protocol: REST (AiHttpAdapter) vs. env.AI binding
│   ├── models.py                # Pydantic DTOs and UTC date formatting
│   ├── repositories/
│   │   ├── user_repository.py
│   │   └── chat_repository.py
│   ├── services/
│   │   ├── user_service.py          # /api/users CRUD
│   │   ├── user_profile_service.py  # /api/users/{id}/profile navigation hub
│   │   ├── me_service.py            # /api/me — maps the Clerk identity to a users row
│   │   └── chat_service.py          # /api/chats — talks to Workers AI via ai.py
│   └── routers/
│       ├── health.py
│       ├── me.py
│       ├── user_profile.py
│       ├── users.py
│       └── chats.py
├── migrations/
│   ├── 001_create_users_table.sql   # Auto-applied against local SQLite
│   └── 002_create_chats_tables.sql  # chats + chat_messages
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── schema.sql                    # Consolidated snapshot of the migrations above,
│                                  # applied manually to D1 via wrangler if used
├── wrangler.jsonc                # Worker config + Workers AI binding + D1 binding
├── pyproject.toml
├── uv.lock
└── .gitignore
```

## Prerequisites (one-time machine setup)

| Tool | Why | Install |
|---|---|---|
| Node.js + npm | Runs `wrangler` (the Cloudflare CLI) | https://nodejs.org (LTS) |
| `uv` | Python package/venv manager used by this project | PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` <br> Git Bash / Linux / macOS: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker | Optional local SQLite container workflow | https://www.docker.com/products/docker-desktop/ |
| A free Cloudflare account | Required to actually call Workers AI (even in local `wrangler dev` — see below) | https://dash.cloudflare.com/sign-up |

> **Corporate proxy / TLS-inspecting network note:** if `uv` fails with
> `invalid peer certificate: UnknownIssuer`, set `$env:UV_NATIVE_TLS = "true"`
> (PowerShell) before running `uv` commands, so it trusts the OS certificate
> store instead of its bundled roots. If `curl` fails with
> `schannel: ... CRYPT_E_NO_REVOCATION_CHECK`, add `--ssl-no-revoke` to the
> curl command.

> After installing `uv`, restart your terminal (or `source ~/.bashrc` in Git
> Bash) so the updated `PATH` picks up `~/.local/bin` where it installs.

## Authentication

Every endpoint except `/api/health` requires a Clerk-issued JWT:
`Authorization: Bearer <token>`. `auth.py` verifies it against
`CLERK_JWKS_URL`/`CLERK_AUDIENCE` (from `.env` or `wrangler.jsonc` `vars`) —
there is no dev bypass, so a plain `curl` with no header gets `401 Unauthorized`
on every route below.

The `showcase` Angular app handles sign-in end to end. To call the API
directly (`curl`, Swagger's "Try it out", etc.), sign in through that app and
copy the bearer token it sends — e.g. from your browser's Network tab on any
request to this API — into your own request.

## Database modes

Set **one active** `DATABASE_MODE` at a time:

```env
# Local uvicorn/Docker
DATABASE_MODE=sqlite
DATABASE_PATH=./local.db

# Cloudflare Workers native binding — wrangler.jsonc already has a
# d1_databases block (its own "wiltech-db" database, not shared with
# fastapi-cloudflare-d1's todo-db)
DATABASE_MODE=d1_binding

# Optional: non-Worker host using Cloudflare D1 over HTTP
DATABASE_MODE=d1_http
CF_ACCOUNT_ID=...
CF_D1_DATABASE_ID=...
CF_D1_API_TOKEN=...
```

Do not keep multiple `DATABASE_MODE=` lines active in the same `.env`; the
last one wins.

## Running locally with SQLite and uvicorn

This mode does not use Wrangler or Cloudflare. Migrations are applied
automatically from `migrations/` the first time the SQLite file is opened.

```powershell
uv sync

Copy-Item .env.example .env
# Keep DATABASE_MODE=sqlite in .env

uv run uvicorn main:app --app-dir src --host 127.0.0.1 --port 8001 --reload
```

Server runs at `http://127.0.0.1:8001`.

## Running locally with Docker + SQLite

```powershell
Copy-Item .env.example .env
docker compose up --build
```

The SQLite database lives in the named Docker volume `sqlite-data` at
`/data/local.db`, so it behaves the same on Windows, macOS, and Linux.

## Running locally against real Workers AI

Unlike D1, **Workers AI has no local emulator** — `wrangler dev` routes
`env.AI` calls to the real Cloudflare Workers AI API against your account
(small per-request usage costs may apply once billing kicks in; the free
tier covers light experimentation).

```powershell
# 1. Install Python dependencies into a local .venv
uv sync

# 2. (Corporate proxy only) allow uv/wrangler to use OS-trusted certs
$env:UV_NATIVE_TLS = "true"

# 3. Log in once so wrangler can reach your account's AI binding
npx wrangler login

# 4. Start the local dev server
uv run pywrangler dev
```

Server runs at `http://127.0.0.1:8787`. Try it:
```powershell
curl.exe http://127.0.0.1:8787/api/health
curl.exe http://127.0.0.1:8787/docs        # Swagger UI in a browser
```

Press `x` in the `wrangler dev` terminal to stop the server cleanly.

## Deploying to Cloudflare (steps you need to take)

These steps require an interactive browser login and only need to be done
**once per machine/account**. After that, redeploying is a single command.

### 1. Log into Cloudflare
```powershell
npx wrangler login
```
This opens a browser window — log in (or sign up for free) and click
"Allow".

### 2. Apply the schema to the remote D1 database
The `ai` binding in `wrangler.jsonc` is account-wide and needs no setup, but
the `d1_databases` binding (`wiltech-db`) is a real database that needs its
tables created once:

```powershell
npx wrangler d1 execute wiltech-db --remote --file=./schema.sql
```
You'll be asked to confirm (`Y`) since this touches the live database.

### 3. Deploy

```powershell
npx wrangler deploy
```
Wrangler prints your live URL, e.g.:
```
https://fastapi-cloudflare-ai.<your-subdomain>.workers.dev
```

### Redeploying after future code changes
```powershell
npx wrangler deploy
```

### Verifying the live deployment
```powershell
curl.exe --ssl-no-revoke https://fastapi-cloudflare-ai.<your-subdomain>.workers.dev/api/health
curl.exe --ssl-no-revoke https://fastapi-cloudflare-ai.<your-subdomain>.workers.dev/docs
```

## API Reference

All paths are under `/api` and require a bearer token (see "Authentication"
above) except `/api/health`, `/docs`, and `/openapi.json`.

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/me` | Current user — upserted from the Clerk token's identity on first call |
| GET | `/api/users` | List users |
| GET | `/api/users/template` | Create-template payload for users |
| GET | `/api/users/{id}` | Get one user |
| POST | `/api/users` | Create a user |
| PUT | `/api/users/{id}` | Update a user |
| DELETE | `/api/users/{id}` | Delete a user (returns `204 No Content`) |
| GET | `/api/users/{id}/profile` | Navigation hub — links to that user's related resources |
| GET | `/api/chats` | List the current user's chats (title + timestamps, no messages) |
| POST | `/api/chats` | Create a new chat (title defaults to "New chat" until the first message) |
| GET | `/api/chats/{id}` | Get one chat with its full message history |
| POST | `/api/chats/{id}/messages` | Send a message; calls Workers AI, stores both messages, returns the updated chat |
| DELETE | `/api/chats/{id}` | Delete a chat and its messages (returns `204 No Content`) |
| GET | `/docs` | Interactive Swagger UI |
| GET | `/openapi.json` | OpenAPI schema |

A chat belongs to a `users` row (looked up/created from the Clerk identity —
same mapping `/me` uses), not directly to the Clerk id, and isn't nested
under `/users/{id}/...` — `chat_service.py._get_owned_chat()` checks
ownership itself, and a chat that exists but belongs to someone else reads
as `404`, not `403`, so its existence isn't leaked.

`chat_service.py.DEFAULT_MODEL` is `@cf/meta/llama-3.1-8b-instruct` —
confirmed working on a free-tier Workers AI account. Override per-request via
`AI_CHAT_MODEL` if your account has access to something else; some
newer/larger models (e.g. `@cf/moonshotai/kimi-k2.7-code`) 403 with "not
available on the Workers Free plan" until you upgrade.

## Roadmap

- No conversation length/context-window trimming — `send_message` replays
  the entire stored history as `messages` on every call, which will
  eventually hit the model's context limit on a long-running chat.
- No way to rename a chat — the title is set once, automatically, from the
  first message.

## Known Beta Caveats

- **Python Workers are in beta.** The exact shape of objects returned by the
  Workers AI binding is based on the documented JS-equivalent API; build any
  adapter defensively, the same way `database.py`'s D1 adapters handle both
  dict-like and attribute-like row access. `chat_service.py._extract_reply()`
  takes the same defensive stance on the AI response shape.
- No traditional SQLAlchemy ORM — repository SQL is raw and parameterized.
- `env` (and therefore `env.DB` / `env.AI`) is only available per-request
  (`request.scope["env"]`), not as a global/startup-time object. Routers build
  services per request through `get_database(request)`/`get_ai(request)`.
