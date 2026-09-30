import { Injectable, computed, inject } from '@angular/core';
import { CurrentUserStore } from '@wiltech-labs/ngx-region-settings';
import { type ILink } from '@wiltech-labs/ngx-api-client';

import { ApiErrors } from '../api/api-error';

/**
 * App-level user session wrapper. Provides isAdmin, myTodosLink and errorMessage
 * on top of the library's CurrentUserStore.
 */
@Injectable({ providedIn: 'root' })
export class UserSession {
  private readonly currentUser = inject(CurrentUserStore);
  private readonly apiErrors = inject(ApiErrors);

  readonly me = this.currentUser.me;
  readonly profile = this.currentUser.profile;
  readonly loading = this.currentUser.loading;
  readonly error = this.currentUser.error;

  // Drives the app-wide banner in app.html — /me underpins the whole app
  // (nav bar, myTodosLink below), so a signed-in visitor would otherwise
  // just see a permanent "Loading…" with no indication the API is down.
  readonly errorMessage = computed(() => {
    const error = this.error();
    return error ? this.apiErrors.describe(error, 'errors.loadAccount') : null;
  });

  readonly isAdmin = computed(() => this.me()?.roleIds?.includes('ADMIN') ?? false);

  // Any link the user profile hands out, by name (`todos`,
  // `cloudflareChats`, `groqChats`, `aiChats`, ...). The API never wants
  // these URLs built by hand — it owns their shape (and, going forward,
  // whether this caller may see them). See todos.store.ts.
  link(name: string): ILink | undefined {
    return this.currentUser.link(name);
  }

  readonly myTodosLink = computed<ILink | undefined>(() => this.link('todos'));
}
