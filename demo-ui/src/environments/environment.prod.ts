import { version } from '../../package.json';

// Swapped in for the `production` build configuration via `fileReplacements`
// in angular.json. TODO: swap clerkPublishableKey for a `pk_live_` key once a
// production Clerk instance exists — still pointing at the dev/test instance,
// which is also what the deployed Worker verifies against today.
// apiUrl is the deployed Worker: fastapi-ai's wrangler.jsonc `name` is fastapi-ai.
export const environment = {
  production: true,
  apiUrl: 'https://fastapi-ai.wiliam334.workers.dev',
  clerkPublishableKey: 'pk_test_b25lLXB5dGhvbi00ODYxLmNsZXJrLmFjY291bnRzLmRldiQ',
  clerkJwtTemplate: 'wiltech-dev-api',
  // Browser-side Giphy key (see environment.ts).
  giphyApiKey: 'Q9nb56erJnyXSwYchtFi7EYYVNsei69j',
  version,
};
