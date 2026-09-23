import { version } from '../../package.json';

// Dev defaults (used by `ng serve` and any build without an explicit
// `production` configuration). Non-secret config only — the Clerk key
// below is a *publishable* key, designed by Clerk to ship in the client
// bundle (unlike a real API key/credential, which never belongs here).
//
// The Clerk instance here must be the one the API verifies against:
// fastapi-cloudflare-d1's wrangler.jsonc points CLERK_JWKS_URL at
// one-python-4861.clerk.accounts.dev, so this is that instance's
// publishable key (it is just base64 of the frontend API domain).
// apiUrl matches the port the local API runs on — see that project's
// README ("uvicorn ... --port 8001") and docker-compose.yml.
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8001',
  clerkPublishableKey: 'pk_test_b25lLXB5dGhvbi00ODYxLmNsZXJrLmFjY291bnRzLmRldiQ',
  clerkJwtTemplate: 'wiltech-dev-api',
  // Giphy app "WilTech". Giphy is searched straight from the browser (post
  // media picker), so this key ships in the bundle like the Clerk one; limit
  // it in the Giphy dashboard. Empty hides the GIF tab.
  giphyApiKey: 'Q9nb56erJnyXSwYchtFi7EYYVNsei69j',
  version,
};
