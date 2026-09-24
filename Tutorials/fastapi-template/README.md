# FastAPI Template — portable FastAPI starter (SQLite + Cloudflare D1 + Workers)

This is a **starting point**, not a tutorial deliverable — copy this folder to
begin a new Python FastAPI project instead of rebuilding the same scaffolding
each time. It already has:

- **Clerk JWT authentication** wired into every route except `/api/health`.
- **A portable `Database` protocol** — local SQLite for uvicorn/Docker, a
  Cloudflare D1 binding, or D1-over-HTTP, all through the same interface
  (`src/core/config/database.py`). Business logic never touches SQLite or D1 directly.
- **A working example resource** (`user_router.py`) built through the full
  router -> service -> repository -> database layering, so you can see the
  pattern before repeating it for your own domain.
- **A standard response envelope** (`_data`, `_metadata`, `_metaLinks`) with
  HATEOAS-style links, built in the service layer.
- Routes mounted under `/api`, `pyproject.toml`/`uv.lock`, Docker, and a
  `wrangler.jsonc` ready for `pywrangler dev` / `wrangler deploy`.

See [`fastapi-cloudflare-d1`](../fastapi-cloudflare-d1) and
[`fastapi-cloudflare-ai`](../fastapi-cloudflare-ai) for what a project built
from this template looks like once it grows real domain resources (or, for
the AI one, a Workers AI integration).

## Status

Template only — not deployed anywhere. `wrangler.jsonc`'s `name` is
`fastapi-template` and its `compatibility_date` is a placeholder; update both
when you start a real project from this.

> **Runs on port 8001 — same as every other Python tutorial project in this
> repo** (`fastapi-cloudflare-d1`, `fastapi-cloudflare-ai`, ...). Keep it that
> way: the `showcase` Angular app's API base URL is a single fixed value, not
> one per backend, so only one of these services is ever meant to run
> locally at a time. Don't give a new project its own port.

## Project Structure

Code is organised by domain, not by file type: each package holds its own
router, service, repository and schemas.

```
fastapi-template/
├── src/
│   ├── entry.py                      # FastAPI app + Workers ASGI entrypoint
│   ├── main.py                       # Plain FastAPI app for uvicorn/Docker; wires
│   │                                  # routers + the Clerk auth dependency
│   ├── core/                         # Cross-cutting, no domain knowledge
│   │   ├── common/
│   │   │   ├── api_response.py       # ApiResponse envelope + API_PREFIX
│   │   │   ├── base_dto.py           # Link, LinkedResource, EmbeddedRef, FieldMetadata
│   │   │   └── serializers.py        # UTC date formatting
│   │   ├── config/
│   │   │   ├── config.py             # Runtime config from Worker env / .env / OS env
│   │   │   └── database.py           # SQLite, D1 binding, and D1 HTTP adapters + migrations
│   │   └── security/
│   │       └── auth.py               # Clerk JWT verification (JWKS fetch/cache)
│   ├── metrics/
│   │   └── status_router.py          # /api/health
│   ├── shared/                       # Data owned by several domains
│   │   └── settings/
│   │       ├── region/               # region_settings table: enums, models, repository
│   │       └── configuration/        # configuration_settings table: enums, schemas, repository
│   └── users/
│       ├── user_router.py            # /api/users CRUD — copy this pattern per resource
│       ├── user_service.py
│       ├── user_repository.py        # Raw parameterized SQL via the Database protocol
│       ├── schemas.py
│       ├── enums.py
│       ├── profiles/                 # /api/me and /api/users/{id}/profile
│       └── settings/                 # /api/users/{id}/settings — reference for the
│                                      # typed Model / Request / DTO / Response layers
├── migrations/
│   ├── 001_create_users_table.sql   # Auto-applied against local SQLite
│   └── 002_settings.sql
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── schema.sql                    # Consolidated snapshot of the migrations above,
│                                  # applied manually to D1 via wrangler if used
├── wrangler.jsonc                # Worker config — no bindings by default; see comment inside
├── pyproject.toml
├── uv.lock
└── .gitignore
```

## Code conventions

The full rules live in [`../PYTHON_APP_CONVENTIONS.md`](../PYTHON_APP_CONVENTIONS.md).
The ones you'll hit first when adding a resource:

**One class per layer, named for the layer.** `users/settings/` is the
reference implementation:

| Layer | Suffix | Example | Built by |
|---|---|---|---|
| Database row (entity) | `Model` | `RegionSettingModel` in `models.py` | repository |
| Request body | `Request` | `UserSettingsUpdateRequest` in `schemas.py` | client; FastAPI validates it |
| What the service returns | `DTO` | `UserSettingsDTO` in `schemas.py` (with `links`) | application service |
| Field rules for the client | `Metadata` | `UserSettingsMetadata` in `schemas.py` | application service |
| HTTP response envelope | `Response` | `UserSettingsResponse = ApiResponse[UserSettingsDTO, UserSettingsMetadata]` in `schemas.py` | application service |

The classes don't inherit from each other. A Request holds only the fields the
client may change; the DTO adds what the server decides (`id`, `links`, ...).

**Every non-delete response uses the generic envelope** in
`core/common/api_response.py`, so a resource never defines its own
`_data`/`_metadata` classes:

```python
# user_settings_service.py — metadata gets the DTO, so business rules can
# change it based on the resource's current state
def build_response(self, user_settings: UserSettingsDTO) -> UserSettingsResponse:
    return UserSettingsResponse.of(
        USER_SETTINGS_DATA_NAME,
        user_settings,
        self.build_metadata(user_settings),
    )

# user_settings_router.py
return service.build_response(user_settings)
```

- The `_data` key name (`"userSettings"`) is a constant in the domain's
  `constants.py`, together with the link names.
- Shared building blocks live in `core/common/base_dto.py`: `Link`,
  `LinkedResource`, `EmbeddedRef` (an `{id, value}` option), and
  `FieldMetadata` (`readOnly` / `hidden` / `mandatory` / `values`).
- `_messages` is always present (an empty array when there's nothing to
  say). `FieldMetadata` drops its own unset flags, so routes don't need
  `response_model_exclude_none`, and a DTO's `None` fields still come back as
  `null`.

`users/user_service.py` and `users/profiles/` still use the older dict-based
`envelope()` helper; move them to `ApiResponse` when you next touch them.

## Starting a new project from this template

1. Copy this folder to `../your-new-project`.
2. Rename `name` in `pyproject.toml` and `wrangler.jsonc`.
3. Leave the port at `8001` — every project in this repo shares it on
   purpose (see the note above). Only stop-one-start-the-next, never a new
   port per project.
4. Set `compatibility_date` in `wrangler.jsonc` to today, if deploying.
5. Delete or repurpose the `users/` package: keep it if you want user
   accounts, otherwise use it (especially `users/settings/`) as the reference
   implementation and add one package per domain with its own router,
   service, repository and schemas, following the conventions above.
6. Add bindings to `wrangler.jsonc` as needed (a commented D1 example is
   already there — `database.py` supports it out of the box).
7. `uv sync`, then run locally (see below).

## Prerequisites (one-time machine setup)

| Tool | Why | Install |
|---|---|---|
| Node.js + npm | Runs `wrangler` (the Cloudflare CLI) | https://nodejs.org (LTS) |
| `uv` | Python package/venv manager used by this project | PowerShell: `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 \| iex"` <br> Git Bash / Linux / macOS: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Docker | Optional local SQLite container workflow | https://www.docker.com/products/docker-desktop/ |
| A free Cloudflare account | Optional: only needed if deploying to Workers | https://dash.cloudflare.com/sign-up |

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
on every route below. Optionally set `CLERK_AUTHORIZED_PARTIES` (comma-separated frontend origins) to also require the token's `azp` claim to match one of them. The Clerk values checked into `.env.example` point at a
shared dev instance; swap them for your own project's Clerk instance if this
stops being a throwaway/tutorial app.

## Database modes

Set **one active** `DATABASE_MODE` at a time:

```env
# Local uvicorn/Docker
DATABASE_MODE=sqlite
DATABASE_PATH=./local.db

# Cloudflare Workers native binding — requires a d1_databases block in
# wrangler.jsonc (see the commented example in that file)
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

## Running locally with Cloudflare D1 emulation

Only relevant once you've added a `d1_databases` binding to `wrangler.jsonc`.
Local dev uses a **local D1 emulation** (a SQLite file wrangler manages under
`.wrangler/state/`) — no Cloudflare login or real database required.

```powershell
uv sync
$env:UV_NATIVE_TLS = "true"   # corporate proxy only

npx wrangler d1 execute <your-db-name> --local --file=./schema.sql
uv run pywrangler dev
```

Server runs at `http://127.0.0.1:8787`. Press `x` in the `wrangler dev`
terminal to stop it cleanly.

## Deploying to Cloudflare

```powershell
npx wrangler login   # once per machine/account
npx wrangler deploy
```

If you added D1 bindings, create the database and apply the schema to the
remote database first — see `fastapi-cloudflare-d1`'s README for the full
step-by-step.

## API Reference

All paths are under `/api` and require a bearer token (see "Authentication"
above) except `/api/health`, `/docs`, and `/openapi.json`.

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/me` | Current user — upserted from the Clerk token's identity on first call |
| GET | `/api/users` | List users |
| GET | `/api/users/search` | Search users by name or email (`?q=`); no `q` returns everyone |
| GET | `/api/users/template` | Create-template payload for users |
| GET | `/api/users/{id}` | Get one user |
| POST | `/api/users` | Create a user |
| PUT | `/api/users/{id}` | Update a user |
| DELETE | `/api/users/{id}` | Delete a user (returns `204 No Content`) |
| GET | `/api/users/{id}/settings` | The user's region settings (timezone, language, currency, theme); falls back to the system defaults (`owner_type: SYSTEM`) until the user saves their own |
| PUT | `/api/users/{id}/settings` | Save the user's region settings |
| DELETE | `/api/users/{id}/settings` | Drop the user's own settings so they fall back to the system defaults (returns `204 No Content`) |
| GET | `/api/users/{id}/profile` | **Where links live.** `/me` only returns the `userProfile` link; this returns the user (`id`, `externalId`, `name`, `email`, `roleIds`) plus every link the UI follows, built from the `{id}` in the path. `UserProfileService.can_view_profile` is the seam for "may the caller see this user's resources?" |
| GET | `/docs` | Interactive Swagger UI |
| GET | `/openapi.json` | OpenAPI schema |

## Known Beta Caveats

- **Python Workers are in beta.** The exact shape of D1 row objects returned
  by `.first()` / `.all()` is based on the documented JS-equivalent API;
  `database.py`'s D1 adapters defensively handle both dict-like and
  attribute-like access, but if a `workers-py` version update changes this
  shape, that's the first place to check.
- No traditional SQLAlchemy ORM — repository SQL is raw and parameterized.
- `env` (and therefore `env.DB`) is only available per-request
  (`request.scope["env"]`), not as a global/startup-time object. Routers build
  services per request through `get_database(request)`.
