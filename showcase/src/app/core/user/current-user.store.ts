import { Injectable, computed, inject } from '@angular/core';
import { ApiClientService, ILink } from '@wiliamferraciolli/ngx-api-client';

import { AuthStore } from '../auth/auth.store';
import { describeApiError } from '../api/api-error';
import { environment } from '../../../environments/environment';

export interface Me {
  id: string;
  name: string;
  email: string | null;
  roleIds: string[];
  links: Record<string, ILink>;
}

// `/users/{id}/profile` — the navigation hub. `/me` only says who the
// caller is and links here; every feature link lives on this.
export interface UserProfile {
  id: string;
  externalId: string | null;
  name: string;
  email: string | null;
  roleIds: string[];
  links: Record<string, ILink>;
}

// App-wide state (like AuthStore) — every route needs the caller's role
// and the links on their user profile, not just one feature. Backed directly by
// ApiClientService.resource(): the URL depends on auth.isSignedIn(), so
// httpResource naturally (re)fetches on sign-in and clears on sign-out —
// no manual ensureLoaded()/reset() bookkeeping needed, unlike a
// signalStore built on a plain subscribe().
@Injectable({ providedIn: 'root' })
export class CurrentUserStore {
  private readonly api = inject(ApiClientService);
  private readonly auth = inject(AuthStore);

  private readonly meResource = this.api.resource<'me', Me>('me', () =>
    this.auth.isSignedIn() ? `${environment.apiUrl}/me` : undefined,
  );

  readonly me = this.meResource.value;

  // /me hands out one link, `userProfile` (its href carries the user id),
  // and the profile resource follows it — never a hand-built URL. Both are
  // resources of this store, so sign-out clears the chain.
  private readonly profileResource = this.api.resource<'userProfile', UserProfile>('userProfile', () =>
    this.api.resolve(this.me()?.links?.['userProfile']),
  );

  readonly profile = this.profileResource.value;
  readonly loading = computed(() => this.meResource.isLoading() || this.profileResource.isLoading());

  // Drives the app-wide banner in app.html — /me underpins the whole app
  // (nav bar, myTodosLink below), so a signed-in visitor would otherwise
  // just see a permanent "Loading…" with no indication the API is down.
  readonly errorMessage = computed(() => {
    const error = this.meResource.error() ?? this.profileResource.error();
    return error ? describeApiError(error, "Couldn't load your account.") : null;
  });

  readonly isAdmin = computed(() => this.me()?.roleIds?.includes('ADMIN') ?? false);

  // Any link the user profile hands out, by name (`todos`,
  // `cloudflareChats`, `groqChats`, `aiChats`, ...). The API never wants
  // these URLs built by hand — it owns their shape (and, going forward,
  // whether this caller may see them). See todos.store.ts.
  link(name: string): ILink | undefined {
    return this.profile()?.links?.[name];
  }

  readonly myTodosLink = computed<ILink | undefined>(() => this.link('todos'));
}
