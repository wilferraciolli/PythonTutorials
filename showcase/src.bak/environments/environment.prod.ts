import { version } from '../../package.json';

// Swapped in for the `production` build configuration via `fileReplacements`
// in angular.json. TODO: swap clerkPublishableKey for a `pk_live_` key once a
// production Clerk instance exists — still pointing at the dev/test instance.
export const environment = {
  production: true,
  apiUrl: 'https://resource-management-api.wiliam334.workers.dev',
  clerkPublishableKey: 'pk_test_bGFzdGluZy1jb2x0LTgyMzMuY2xlcmsuYWNjb3VudHMuZGV2JA',
  version,
};
