# Demo UI

Angular front end for **`Tutorials/fastapi-ai`**: the working AI project with
todos and tags, chats with Cloudflare Workers AI or Groq, "Ask your data",
and the social groups feature (groups, posts with Unsplash / Giphy / YouTube
media, comments, likes, timeline, admin area).

The tutorial screens (todos, tags, Cloudflare and Groq chats against the
tutorial APIs) stay in `../showcase`. This app was split out of it once the
social feature grew, so the two share the same core code (Clerk auth, the
API client, the profile-links store) but are separate apps.

## Run

```
npm install
npm start          # http://localhost:4201 (showcase keeps 4200, so both can run)
```

Start `Tutorials/fastapi-ai` on port 8001 (`apiUrl` in
`src/environments/environment.ts`). Every screen follows the links the API
hands out from `/api/me` then the user profile, so a card or menu entry only
works when the API exposes its link.

## Routes

| Path | Screen |
|---|---|
| `/` | Home: a tile per destination — todos, AI chat, Ask, timeline, groups (and admin, for admins) |
| `/profile`, `/todos`, `/tags` | Profile, todos and tags |
| `/workers-ai` | Chat sessions with Cloudflare Workers AI or Groq |
| `/ask` | Ask questions about your todos and chats in plain English |
| `/timeline` | Posts from your groups: all, following, popular |
| `/groups`, `/groups/:id`, `/groups/:id/posts/:postId` | Groups, members, followers, posts and threaded comments |
| `/admin` | Admin (admins only): social engagement insights (totals and daily charts for groups, posts, comments, likes) and maintenance tools |

## Design

Material 3, light and dark (it follows the system setting). Signed-in users
navigate with a rail on tablets and up and a drawer on phones. The rules —
tokens, palette, buttons, lists, motion — are in
[docs/frontend-conventions.md](docs/frontend-conventions.md#design-system-material-3).

## Post media

The post form's **Add media** picker searches Unsplash through the API (the
server holds that key) and Giphy straight from the browser using
`giphyApiKey` in `src/environments`. YouTube takes a pasted link or id. See
`Tutorials/fastapi-ai/docs/social-groups.md#post-media`.

## Tests and build

```
npm test
npm run build
```

## Running end-to-end tests

E2E tests use [Playwright](https://playwright.dev/) plus Clerk's official
[`@clerk/testing`](https://clerk.com/docs/guides/development/testing/playwright/overview)
helper, since this app's sign-in is fully Clerk-hosted — a plain headless
browser gets flagged by Clerk's bot detection before it ever reaches the
app.

**One-time setup:**

```bash
cp .env.example .env
```

Fill in (using the WILTECH Clerk instance at
`https://lasting-colt-8233.clerk.accounts.dev`):

- `CLERK_SECRET_KEY` — Clerk Dashboard → Configure → API Keys → "Secret
  keys". Real secret — never commit `.env`.
- `CLERK_PUBLISHABLE_KEY` — same dashboard page (also already hardcoded in
  `src/environments/environment.ts`; `@clerk/testing` needs it as an env
  var too).
- `E2E_CLERK_USER_EMAIL` — an **existing** user in this Clerk instance,
  with Email/Password auth enabled, using a `+clerk_test`-tagged address
  (e.g. `e2e+clerk_test@wiltech.com` — Clerk suppresses real email delivery
  to that pattern). Create this user once in the Clerk Dashboard if it
  doesn't exist yet.

**Run:**

```bash
npm run e2e        # headless
npm run e2e:ui     # Playwright's interactive UI mode
```

This spins up both the API (`resource-management-api`, via `uv run
uvicorn`) and the UI (`ng serve`) against a throwaway
`../resource-management-api/e2e-local.db` (wiped at the start of each run —
never your dev `local.db`), signs in as the configured test user via
Clerk's server-side testing token (bypassing the hosted sign-in form
entirely), promotes that user to admin in the fresh db (via
`scripts/promote_admin.py`, needed for the admin-area tests), then runs
the suite in `e2e/`.

Requires `resource-management-api`'s own Python setup (`uv sync` — see
that project's README) to already be done, since Playwright's `webServer`
shells out to `uv run uvicorn` directly.

