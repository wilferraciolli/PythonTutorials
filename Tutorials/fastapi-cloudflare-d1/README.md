# FastAPI TODO API — Cloudflare Python Workers + D1

This is the Cloudflare-deployable version of the TODO API. It reuses the same
Pydantic models/business-logic shape as the local SQLAlchemy tutorial project
(`../fastapi-learning`), but the data layer is rewritten to talk to
**Cloudflare D1** via a binding instead of a SQLAlchemy connection string.

## Status

✅ **Deployed and live**: https://fastapi-todo-d1.wiliam334.workers.dev

Verified working both locally (D1 emulation) and in production (real D1
database `todo-db`): health check, full CRUD (POST/GET/PUT/PATCH/DELETE), and
`/docs` Swagger UI all confirmed.

## Why a separate project?

D1 has no connection string — it's only reachable from inside a Cloudflare
Worker via `env.DB`. That means the repository layer, the dev server
(`wrangler`/`pywrangler` instead of `uvicorn`), and the dependency management
(`pyproject.toml` + `uv` instead of `requirements.txt` + `venv`) are all
different. Keeping it as a separate project avoids breaking the working local
`fastapi-learning` tutorial.

## Project Structure

```
fastapi-cloudflare-d1/
├── src/
│   ├── entry.py                 # FastAPI app + Workers ASGI entrypoint
│   ├── models.py                # Pydantic models (TodoCreate, TodoUpdate, Todo, TodoState)
│   ├── utils.py                 # TodoUtils (overdue / due-soon helpers)
│   ├── repositories/
│   │   └── todo_repository.py   # Raw SQL via env.DB binding (NOT SQLAlchemy)
│   ├── services/
│   │   └── todo_service.py      # Business logic, async, calls the repository
│   └── routers/
│       ├── health.py
│       └── todos.py             # Async endpoints; extracts env from Request.scope
├── schema.sql                    # CREATE TABLE todos (...)
├── wrangler.jsonc                 # Worker config + D1 binding
├── pyproject.toml                 # Python deps (fastapi, workers-py, workers-runtime-sdk)
└── .gitignore
```

## Prerequisites (one-time machine setup)

| Tool | Why | Install |
|---|---|---|
| Node.js + npm | Runs `wrangler` (the Cloudflare CLI) | https://nodejs.org (LTS) |
| `uv` | Python package/venv manager used by this project | PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` |
| A free Cloudflare account | Hosts the Worker + D1 database | https://dash.cloudflare.com/sign-up |

> **Corporate proxy / TLS-inspecting network note:** if `uv` fails with
> `invalid peer certificate: UnknownIssuer`, set `$env:UV_NATIVE_TLS = "true"`
> (PowerShell) before running `uv` commands, so it trusts the OS certificate
> store instead of its bundled roots. If `curl` fails with
> `schannel: ... CRYPT_E_NO_REVOCATION_CHECK`, add `--ssl-no-revoke` to the
> curl command. Both are local-network quirks, not problems with the deployed
> API — other machines/browsers work fine.

## Running Locally

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
curl.exe http://127.0.0.1:8787/todos
```

To create a todo (PowerShell quoting is finicky with inline JSON, so use a
temp file):
```powershell
'{"title":"Test","description":"Local test","complete_by":"2026-12-31T23:59:59"}' |
  Out-File -Encoding utf8 -NoNewline body.json
curl.exe -X POST http://127.0.0.1:8787/todos -H "Content-Type: application/json" --data-binary "@body.json"
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

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/todos` | List all todos |
| GET | `/todos/{id}` | Get one todo |
| POST | `/todos` | Create a todo (`title`, optional `description`, `complete_by`) |
| PUT | `/todos/{id}` | Full update of a todo |
| PATCH | `/todos/{id}/state/{state}` | Update only the state (`NEW`, `ACTIVE`, `CLOSED`) |
| DELETE | `/todos/{id}` | Delete a todo (returns `204 No Content`) |
| GET | `/docs` | Interactive Swagger UI |
| GET | `/openapi.json` | OpenAPI schema |

## Known Beta Caveats

- **Python Workers are in beta.** The exact shape of D1 row objects returned
  by `.first()` / `.all()` is based on the documented JS-equivalent API;
  repository `_get()` helpers defensively handle both dict-like and
  attribute-like access, but if a `workers-py` version update changes this
  shape, that's the first place to check.
- No traditional SQLAlchemy ORM — all SQL in `todo_repository.py` is raw and
  parameterized via `.bind(...)` to avoid SQL injection.
- `env` (and therefore `env.DB`) is only available per-request
  (`request.scope["env"]`), not as a global/startup-time object — this is why
  `get_todo_service` in `routers/todos.py` takes a `Request` and builds a
  fresh repository/service per call, instead of using a global engine like
  the SQLAlchemy version does.
