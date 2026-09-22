import { version } from '../../package.json';

// Swapped in for the `production` build configuration via `fileReplacements`
// in angular.json. TODO: swap clerkPublishableKey for a `pk_live_` key once a
// production Clerk instance exists — still pointing at the dev/test instance,
// which is also what the deployed Worker verifies against today.
// apiUrl is the deployed Worker: wrangler.jsonc's `name` is fastapi-todo-d1.
export const environment = {
  production: true,
  apiUrl: 'https://fastapi-todo-d1.wiliam334.workers.dev',
  clerkPublishableKey: 'pk_test_b25lLXB5dGhvbi00ODYxLmNsZXJrLmFjY291bnRzLmRldiQ',
  clerkJwtTemplate: 'wiltech-dev-api',
  version,
};
