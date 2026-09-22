import { HttpClient } from '@angular/common/http';
import { computed, inject } from '@angular/core';
import { patchState, signalStore, withComputed, withMethods, withState } from '@ngrx/signals';
import { firstValueFrom } from 'rxjs';

import { Envelope, Links, unwrapData } from '../api/envelope';
import { environment } from '../../../environments/environment';

export interface Me {
  id: string;
  name: string;
  email: string | null;
  roleIds: string[];
  links: Links;
}

type MeEnvelope = Envelope<Me>;

interface CurrentUserState {
  me: Me | null;
  loading: boolean;
  loaded: boolean;
}

const initialState: CurrentUserState = { me: null, loading: false, loaded: false };

// App-wide state (like AuthStore) — every route needs to know the caller's
// role and their `myTodos` link, not just one feature. Auth (Clerk) only
// proves *who* signed in; this is the app's own `/me`, which the backend
// auto-provisions a `users` row for on first sight of a given Clerk
// identity (see me_service.py).
export const CurrentUserStore = signalStore(
  { providedIn: 'root' },
  withState(initialState),
  withComputed(({ me }) => ({
    isAdmin: computed(() => me()?.roleIds?.includes('ADMIN') ?? false),
    // The API never wants this URL built by hand — it hands it out as a
    // link on `/me` precisely so the UI doesn't have to know the
    // `/users/{id}/todos` shape. See todos.store.ts.
    myTodosHref: computed(() => me()?.links?.['myTodos']?.href),
  })),
  withMethods((store) => {
    const http = inject(HttpClient);
    let inFlight: Promise<Me> | null = null;

    async function load(): Promise<Me> {
      patchState(store, { loading: true });
      const response = await firstValueFrom(http.get<MeEnvelope>(`${environment.apiUrl}/me`));
      const me = unwrapData(response, 'me') as Me;
      patchState(store, { me, loading: false, loaded: true });
      return me;
    }

    return {
      // The nav bar, guards, and every page that needs the role/links all
      // call this independently — dedupe concurrent callers onto the same
      // in-flight request instead of firing one GET /me each.
      async ensureLoaded(): Promise<Me> {
        if (store.loaded() && store.me()) {
          return store.me() as Me;
        }
        if (!inFlight) {
          inFlight = load().finally(() => {
            inFlight = null;
          });
        }
        return inFlight;
      },

      reset(): void {
        patchState(store, initialState);
      },
    };
  }),
);
