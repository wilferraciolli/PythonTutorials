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
| `/` | Home: cards for todos, AI chat, Ask, timeline, groups (and admin, for admins) |
| `/profile`, `/todos`, `/tags` | Profile, todos and tags |
| `/workers-ai` | Chat sessions with Cloudflare Workers AI or Groq |
| `/ask` | Ask questions about your todos and chats in plain English |
| `/timeline` | Posts from your groups: all, following, popular |
| `/groups`, `/groups/:id`, `/groups/:id/posts/:postId` | Groups, members, followers, posts and threaded comments |
| `/admin` | Admin tools (admins only) |

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
