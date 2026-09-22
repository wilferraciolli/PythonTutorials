import { version } from '../../package.json';

// Dev defaults (used by `ng serve` and any build without an explicit
// `production` configuration). Non-secret config only — the Clerk key
// below is a *publishable* key, designed by Clerk to ship in the client
// bundle (unlike a real API key/credential, which never belongs here).
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8001',
  clerkPublishableKey: 'pk_test_bGFzdGluZy1jb2x0LTgyMzMuY2xlcmsuYWNjb3VudHMuZGV2JA',
  version,
};
