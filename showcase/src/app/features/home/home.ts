import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthStore } from '../../core/auth/auth.store';

// Public landing page — no auth.guard on this route. Exists so the app has
// something to show before sign-in, and doubles as a page to sanity-check
// the Clerk integration (see auth.store.ts).
@Component({
  selector: 'app-home',
  imports: [RouterLink],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {
  protected readonly auth = inject(AuthStore);

  protected signIn(): void {
    void this.auth.signIn();
  }
}
