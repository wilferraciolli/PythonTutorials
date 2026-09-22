import { Component, computed, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink } from '@angular/router';

import { AuthStore } from '../../core/auth/auth.store';

// Public landing page — the app's only route. Doubles as the place to
// sanity-check the Clerk round-trip against the FastAPI/D1 backend: sign
// in here and the interceptor starts attaching a token to API calls (see
// auth.store.ts, auth.interceptor.ts).
@Component({
  selector: 'app-home',
  imports: [RouterLink, MatButtonModule, MatCardModule, MatIconModule],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {
  protected readonly auth = inject(AuthStore);

  // Email is the label Clerk always has for a signed-in user; the name
  // fields are optional in the dashboard's default sign-up flow, so fall
  // back rather than render "Signed in as undefined".
  protected readonly signedInAs = computed(
    () => this.auth.user()?.primaryEmailAddress?.emailAddress ?? 'your account',
  );

  protected signIn(): void {
    void this.auth.signIn();
  }

  protected signOut(): void {
    void this.auth.signOut();
  }
}
