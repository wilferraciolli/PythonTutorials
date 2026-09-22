import { Component, effect, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { AuthStore } from './core/auth/auth.store';
import { CurrentUserStore } from './core/user/current-user.store';
import { environment } from '../environments/environment';
import { NavBar } from './shared/nav-bar/nav-bar';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, NavBar],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly auth = inject(AuthStore);
  private readonly currentUser = inject(CurrentUserStore);
  protected readonly version = environment.version;

  constructor() {
    // Fetches the app-specific profile/role as soon as Clerk confirms a
    // session, and clears it on sign-out — every route needs to know the
    // role (admin-gating, the profile menu), not just one that happens to
    // visit /profile or /admin first.
    effect(() => {
      if (this.auth.isSignedIn()) {
        void this.currentUser.ensureLoaded();
      } else {
        this.currentUser.reset();
      }
    });
  }
}
