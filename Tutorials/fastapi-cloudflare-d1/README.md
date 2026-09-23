# FastAPI TODO API — portable FastAPI with SQLite + Cloudflare D1

This TODO API keeps the app code portable:

- **Local uvicorn/Docker** uses SQLite through the shared `Database` protocol.
- **Cloudflare Workers** uses the native D1 binding (`env.DB`) through the same
  protocol.
- **Optional non-Worker hosting** can still talk to Cloudflare D1 via HTTP.

The repository layer does not know whether the database is SQLite, Cloudflare
D1 binding, or D1 HTTP.

## Status

✅ **Cloudflare deployment**: https://fastapi-todo-d1.wiliam334.workers.dev

Verified working with Cloudflare D1 and portable local SQLite mode.

> **Runs on port 8001 — same as every other Python tutorial project in this
> repo** (`fastapi-cloudflare-ai`, `fastapi-template`, ...). The `showcase`
> Angular app's API base URL is a single fixed value, not one per backend, so
> only one of these services is ever meant to run locally at a time. Stop
> whichever one is running before starting this one.

## Why a separate project?

The project started as a Cloudflare D1 Worker app, but the database access is
now behind a small adapter interface. That means the same routers, services,
DTOs, response envelope, metadata, links, templates, UUIDs, and UTC date
formatting can be reused if the app later moves to Docker, Render, or another
host.

## Project Structure

```
fastapi-cloudflare-d1/
├── src/
│   ├── entry.py                 # FastAPI app + Workers ASGI entrypoint
│   ├── main.py                  # Plain FastAPI app for uvicorn/Docker; wires
│   │                             # routers + the Clerk auth dependency
│   ├── auth.py                  # Clerk JWT verification (JWKS fetch/cache)
│   ├── database.py              # SQLite, D1 binding, and D1 HTTP adapters
│   ├── config.py                # Runtime config from Worker env / .env / OS env
│   ├── api_response.py          # Shared response envelope model
│   ├── models.py                # Pydantic DTOs and UTC date formatting
│   ├── utils.py                 # TodoUtils (overdue / due-soon helpers)
│   ├── repositories/
│   │   ├── tag_repository.py    # Reads via tag_resource_view (see below)
│   │   ├── todo_repository.py   # Raw parameterized SQL via Database protocol
│   │   └── user_repository.py
│   ├── services/
│   │   ├── tag_service.py
│   │   ├── todo_service.py      # Business logic, metadata, links, auto-tagging
│   │   ├── user_service.py      # /users CRUD
│   │   ├── user_profile_service.py  # /users/{id}/profile navigation hub
│   │   └── me_service.py        # /me — maps the Clerk identity to a users row
│   └── routers/
│       ├── health.py
│       ├── me.py
│       ├── tags.py
│       ├── todos.py
│       ├── user_profile.py
│       └── users.py
├── migrations/                   # Auto-applied, in order, against local SQLite
│   ├── 001_create_users.sql
│   ├── 002_create_tables.sql     # todos + tags tables
│   └── 003_create_tag_resource_view.sql  # tag_resource_view (tag ↔ resource join)
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── schema.sql                    # Consolidated snapshot of the migrations above,
│                                  # applied manually to D1 via wrangler
├── wrangler.jsonc                 # Worker config + D1 binding
├── pyproject.toml
└── .gitignore
```

## Prerequisites (one-time machine setup)

| Tool | Why | Install |
|---|---|---|
| Node.js + npm | Runs `wrangler` (the Cloudflare CLI) | https://nodejs.org (LTS) |
| `uv` | Python package/venv manager used by this project | PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` <br> Git Bash / Linux / macOS: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker | Optional local SQLite container workflow | https://www.docker.com/products/docker-desktop/ |
| A free Cloudflare account | Optional: hosts the Worker + D1 database | https://dash.cloudflare.com/sign-up |

> **Corporate proxy / TLS-inspecting network note:** if `uv` fails with
> `invalid peer certificate: UnknownIssuer`, set `$env:UV_NATIVE_TLS = "true"`
> (PowerShell) before running `uv` commands, so it trusts the OS certificate
> store instead of its bundled roots. If `curl` fails with
> `schannel: ... CRYPT_E_NO_REVOCATION_CHECK`, add `--ssl-no-revoke` to the
> curl command. Both are local-network quirks, not problems with the deployed
> API — other machines/browsers work fine.

> After installing `uv`, restart your terminal (or `source ~/.bashrc` in Git
> Bash) so the updated `PATH` picks up `~/.local/bin` where it installs.

## Authentication

Every endpoint except `/health` requires a Clerk-issued JWT:
`Authorization: Bearer <token>`. `auth.py` verifies it against
`CLERK_JWKS_URL`/`CLERK_AUDIENCE` (from `.env` or `wrangler.jsonc` `vars`) —
there is no dev bypass, so a plain `curl` with no header gets `401 Unauthorized`
on every route below. Optionally set `CLERK_AUTHORIZED_PARTIES` (comma-separated frontend origins) to also require the token's `azp` claim to match one of them.

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

# Cloudflare Workers native binding
DATABASE_MODE=d1_binding

# Optional: non-Worker host using Cloudflare D1 over HTTP
DATABASE_MODE=d1_http
CF_ACCOUNT_ID=...
CF_D1_DATABASE_ID=...
CF_D1_API_TOKEN=...
```

Do not keep multiple `DATABASE_MODE=` lines active in the same `.env`; the last
one wins.

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

## Running locally with Cloudflare D1 emulation

Local dev uses a **local D1 emulation** (a SQLite file wrangler manages under
`.wrangler/state/`) — no Cloudflare login or real database required.

```powershell
# 1. Install Python dependencies into a local .venv
uv sync

# 2. (Corporate proxy only) allow uv/wrangler to use OS-trusted certs
$env:UV_NATIVE_TLS = "true"

# 3. Create the todos table in the LOCAL D1 emulation
#    (only needed once, or again if you delete .wrangler/state)
npx wrangler d1 execute todo-db --local --file=./schema.sql

# 4. Start the local dev server
uv run pywrangler dev
```

Server runs at `http://127.0.0.1:8787`. Try it:
```powershell
curl.exe http://127.0.0.1:8787/health
curl.exe http://127.0.0.1:8787/docs        # Swagger UI in a browser

# Everything past here needs a bearer token — see "Authentication" above.
$token = "<paste-a-clerk-jwt-here>"
curl.exe http://127.0.0.1:8787/users/<user-id>/todos -H "Authorization: Bearer $token"
```

To create a todo (PowerShell quoting is finicky with inline JSON, so use a
temp file):
```powershell
'{"title":"Test","description":"Local test","complete_by":"2026-12-31T23:59:59"}' |
  Out-File -Encoding utf8 -NoNewline body.json
curl.exe -X POST http://127.0.0.1:8787/users/<user-id>/todos `
  -H "Content-Type: application/json" -H "Authorization: Bearer $token" --data-binary "@body.json"
Remove-Item body.json
```

Press `x` in the `wrangler dev` terminal to stop the server cleanly.

## Deploying to Cloudflare (steps you need to take)

These steps require an interactive browser login and only need to be done
**once per machine/account**. After that, redeploying is a single command
(see below).

### 1. Log into Cloudflare
```powershell
npx wrangler login
```
This opens a browser window — log in (or sign up for free) and click
"Allow".

### 2. Create the D1 database
```powershell
npx wrangler d1 create todo-db
```
This prints a `database_id` — copy it.

### 3. Update `wrangler.jsonc`
Paste the real ID into the `d1_databases` block:
```jsonc
"d1_databases": [
  {
    "binding": "DB",
    "database_name": "todo-db",
    "database_id": "<paste-your-real-id-here>"
  }
]
```
> The `binding` **must stay `"DB"`** — the code reads `request.scope["env"].DB`.
> In Cloudflare Worker mode you can omit `DATABASE_MODE`; the app defaults to
> `d1_binding` when `env.DB` exists.

### 4. Apply the schema to the remote (real) database
```powershell
npx wrangler d1 execute todo-db --remote --file=./schema.sql
```
You'll be asked to confirm (`Y`) since this touches the live database.

### 5. Deploy
```powershell
npx wrangler deploy
```
Wrangler prints your live URL, e.g.:
```
https://fastapi-todo-d1.<your-subdomain>.workers.dev
```
This is **always-on** — no cold starts, no sleep policy, generous free daily
request quota.

### Redeploying after future code changes
Once steps 1–4 are done, every future change is just:
```powershell
npx wrangler deploy
```

### Verifying the live deployment
```powershell
curl.exe --ssl-no-revoke https://fastapi-todo-d1.<your-subdomain>.workers.dev/health
curl.exe --ssl-no-revoke https://fastapi-todo-d1.<your-subdomain>.workers.dev/docs
```

## API Reference

All paths require a bearer token (see "Authentication" above) except
`/health`, `/docs`, and `/openapi.json`.

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/me` | Current user — upserted from the Clerk token's identity on first call |
| GET | `/users` | List users |
| GET | `/users/search` | Search users by name or email (`?q=`); no `q` returns everyone |
| GET | `/users/template` | Create-template payload for users |
| GET | `/users/{id}` | Get one user |
| POST | `/users` | Create a user |
| PUT | `/users/{id}` | Update a user |
| DELETE | `/users/{id}` | Delete a user (returns `204 No Content`) |
| GET | `/users/{id}/profile` | **Where links live.** `/me` only returns the `userProfile` link; this returns the user (`id`, `externalId`, `name`, `email`, `roleIds`) plus every link the UI follows, built from the `{id}` in the path. `UserProfileService.can_view_profile` is the seam for "may the caller see this user's resources?" |
| GET | `/users/{user_id}/todos` | List all todos for a user |
| GET | `/users/{user_id}/todos/template` | Create-template payload for todos |
| GET | `/users/{user_id}/todos/{id}` | Get one todo |
| POST | `/users/{user_id}/todos` | Create a todo (`title`, optional `description`, `complete_by`) |
| PUT | `/users/{user_id}/todos/{id}` | Full update of a todo |
| PATCH | `/users/{user_id}/todos/{id}/state/{state}` | Update only the state (`NEW`, `ACTIVE`, `CLOSED`) |
| DELETE | `/users/{user_id}/todos/{id}` | Delete a todo (returns `204 No Content`) |
| GET | `/tags` | List tags, optionally filtered by `resource_id` |
| GET | `/tags/search?tag=` | Search tags by tag name *or* the tagged resource's name |
| GET | `/tags/template` | Create-template payload for tags |
| GET | `/tags/{id}` | Get one tag |
| POST | `/tags` | Create a tag for a resource (`resource_id`, `tag`) |
| DELETE | `/tags/{id}` | Delete a tag (returns `204 No Content`) |
| GET | `/docs` | Interactive Swagger UI |
| GET | `/openapi.json` | OpenAPI schema |

Every Tag response embeds `resource: {id, value}` — the tagged resource's
display name, resolved through the `tag_resource_view` SQL view (todos are
the only taggable resource today; see `migrations/003_create_tag_resource_view.sql`).
`resource` is `null` when the resource can't be resolved (e.g. it's been
deleted); `/tags/search` matches against both the tag text and that resolved
name, so searching `"groceries"` can surface a tag literally named `"urgent"`
if it's attached to a todo titled "Buy groceries".

## Known Beta Caveats

- **Python Workers are in beta.** The exact shape of D1 row objects returned
  by `.first()` / `.all()` is based on the documented JS-equivalent API;
  repository `_get()` helpers defensively handle both dict-like and
  attribute-like access, but if a `workers-py` version update changes this
  shape, that's the first place to check.
- No traditional SQLAlchemy ORM — repository SQL is raw and parameterized.
- `env` (and therefore `env.DB`) is only available per-request
  (`request.scope["env"]`), not as a global/startup-time object. Routers build
  services per request through `get_database(request)`.
