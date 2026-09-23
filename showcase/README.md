# Showcase

Angular front end for the Python tutorial APIs in `Tutorials/`: the todos and
tags screens talk to `fastapi-cloudflare-d1`, and the Workers AI chat screen
talks to `fastapi-cloudflare-ai`.

**Only one API runs at a time.** Every project serves on `localhost:8001`,
which is the single `apiUrl` in `src/environments/environment.ts` — start the
one that matches the screen you want to use. If the wrong one (or none) is
running, a banner across the top says the API can't be reached.

## Routes

| Path | Auth | Screen |
|---|---|---|
| `/` | Public | Home — cards linking to Todos and Workers AI (sign in from the nav bar) |
| `/profile` | Sign-in required | Current user's name/email/roles (read-only; sourced from `/me`) |
| `/todos` | Sign-in required | List the signed-in user's todos, filterable by state |
| `/todos/new`, `/todos/:id/edit` | Sign-in required | Create/edit a todo, including its tags |
| `/tags` | Sign-in required | Browse, search, create, and delete tags across every resource |
| `/workers-ai`, `/workers-ai/:chatId` | Sign-in required | Chat sessions with Cloudflare Workers AI or Groq: pick or create a session from the selector at the top, rename it, and message the model (needs `fastapi-cloudflare-ai` running) |

Signed-out visitors hitting a guarded route are redirected to `/`
(`core/auth/auth.guard.ts`). Screens follow the links the API returns in each
response (`_metaLinks`, per-resource `links`) rather than hand-built URLs —
see `ngx-api-client`'s `LinkService`/`ApiClientService`, and each API's
README for what its responses contain. The first request to a collection
has no link to follow yet, so it is built from `apiUrl` (the chat API's
routes are under `/api`).

## Running it

```bash
npm install
npm start          # ng serve -> http://localhost:4200/
```

The API origin is `apiUrl` in `src/environments/environment.ts`
(`http://localhost:8001` in dev — the port every Python project's README and
`docker-compose.yml` use).

## Auth

Clerk, via `@clerk/clerk-js` in headless mode (`src/app/core/auth/auth.store.ts`).
Three things have to line up or a token will be rejected by the API:

| Piece | Where it lives | Value |
| --- | --- | --- |
| Clerk instance | `environment.clerkPublishableKey` | `one-python-4861.clerk.accounts.dev` |
| JWKS the API verifies against | each API's `wrangler.jsonc` / `.env` (`CLERK_JWKS_URL`) | same instance's `/.well-known/jwks.json` |
| JWT template name = API audience | `environment.clerkJwtTemplate` / `CLERK_AUDIENCE` | `wiltech-dev-api` |

The publishable key is base64 of the instance's frontend API domain, so it is
derivable from the JWKS URL — it is *publishable* and belongs in the bundle.

A JWT template named `wiltech-dev-api` must exist in that Clerk instance
(Dashboard -> Configure -> JWT Templates) with `name` and `email` claims; the
default session token carries neither, and no `aud` for the API to check.

Sign-in is a full-page redirect to Clerk's hosted Account Portal — the npm
build of `clerk-js` ships without embedded UI components, so `mountSignIn()`
is not available and `redirectToSignIn()` is the entry point.

## Claude Code setup

If you're working on this UI with Claude Code, install the `frontend-design`
plugin for design guidance when building or reshaping screens:

```
/plugin install frontend-design@claude-plugins-official
```

Plugin installs are local to the machine (not synced via your account), so
this needs to be run again on each new machine.

## Tests

```bash
npm test           # vitest via ng test
```

## Building

```bash
npm run build      # -> dist/
```

`public/_redirects` sends all paths to `index.html` so client-side routing
survives a refresh on Cloudflare Pages.
