import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { AuthStore } from './core/auth/auth.store';
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
  protected readonly version = environment.version;

  // No CurrentUserStore wiring here — it's a thin ApiClientService.resource()
  // wrapper now (see current-user.store.ts): its URL reads auth.isSignedIn()
  // itself, so it fetches/clears on sign-in/out on its own, the moment
  // anything (NavBar, TodosStore, ProfilePage) injects it. Nothing to
  // trigger eagerly from here.
}
