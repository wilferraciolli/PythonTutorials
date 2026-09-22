import { Injectable, computed, inject } from '@angular/core';
import { ApiClientService, ILink } from '@wiliamferraciolli/ngx-api-client';

import { AuthStore } from '../auth/auth.store';
import { environment } from '../../../environments/environment';

export interface Me {
  id: string;
  name: string;
  email: string | null;
  roleIds: string[];
  links: Record<string, ILink>;
}

// App-wide state (like AuthStore) — every route needs the caller's role
// and their `myTodos` link, not just one feature. Backed directly by
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
  readonly loading = this.meResource.isLoading;

  readonly isAdmin = computed(() => this.me()?.roleIds?.includes('ADMIN') ?? false);

  // The API never wants this URL built by hand — it hands it out as a
  // link on `/me` precisely so the UI doesn't have to know the
  // `/users/{id}/todos` shape. See todos.store.ts.
  readonly myTodosLink = computed<ILink | undefined>(() => this.me()?.links?.['myTodos']);
}
