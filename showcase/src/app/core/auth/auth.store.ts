import { computed } from '@angular/core';
import { patchState, signalStore, withComputed, withMethods, withState } from '@ngrx/signals';
import { Clerk } from '@clerk/clerk-js';
import type { Resources } from '@clerk/shared/types';

import { environment } from '../../../environments/environment';

type ClerkUser = Clerk['user'];
type ClerkSession = Clerk['session'];

interface AuthState {
  user: ClerkUser;
  session: ClerkSession;
}

const initialState: AuthState = { user: undefined, session: undefined };

/**
 * The single source of truth for "who is signed in", backed by Clerk.
 * `init()` is called once from `provideAppInitializer` (`app.config.ts`)
 * before the app renders, so route guards and the interceptor never race a
 * not-yet-loaded Clerk instance.
 */
export const AuthStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed(({ session }) => ({
    isSignedIn: computed(() => session() != null),
  })),
  withMethods((store) => {
    let clerk: Clerk | null = null;

    return {
      /** Loads the Clerk SDK and starts tracking session changes. Call once, at startup. */
      async init(): Promise<void> {
        const instance = new Clerk(environment.clerkPublishableKey);
        await instance.load();
        clerk = instance;
        // Clerk's documented pattern for non-React ("headless") integrations
        // — exposes the instance as `window.Clerk` for tooling that expects
        // it there (e.g. `@clerk/testing`'s Playwright helpers, and this
        // project's own e2e/auth.setup.ts, both of which read it directly).
        (window as unknown as { Clerk: Clerk }).Clerk = instance;
        patchState(store, { user: instance.user, session: instance.session });

        instance.addListener(({ user, session }: Resources) => {
          patchState(store, { user, session });
        });
      },

      // The `resource-management-api` JWT template's token (Clerk Dashboard
      // -> Configure -> JWT Templates), not the default session token —
      // that default carries no custom claims (name/email) and no `aud`
      // scoping it to this API. The backend (auth.py) verifies `aud`
      // matches, and reads `name`/`email` from claims on first sign-in
      // (routers/me.py) — both require going through this named template.
      async getToken(): Promise<string | null> {
        return (await clerk?.session?.getToken({ template: 'resource-management-api' })) ?? null;
      },

      /**
       * Full-page redirect to Clerk's hosted Account Portal, then back here.
       * `clerk-js`'s npm build ships without its embedded modal UI (that's
       * only available via Clerk's React SDK) — `redirectToSignIn()` is the
       * one sign-in entry point that doesn't need it. (Mounting an embedded
       * widget via `mountSignIn()` throws "Clerk was not loaded with Ui
       * components" for this reason.)
       */
      async signIn(): Promise<void> {
        await clerk?.redirectToSignIn({ redirectUrl: window.location.href });
      },

      async signOut(): Promise<void> {
        await clerk?.signOut();
      },
    };
  }),
);
