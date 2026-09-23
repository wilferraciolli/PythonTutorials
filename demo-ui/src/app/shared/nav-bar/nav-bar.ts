import { Component, inject, input, output, signal } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink } from '@angular/router';

import { AuthStore } from '../../core/auth/auth.store';
import { ProfileMenu } from '../profile-menu/profile-menu';

// App-wide top app bar, mounted once in app.html — the one place a
// signed-out visitor finds "Sign in" and a signed-in one finds the account
// menu, instead of every page rolling its own header. Destinations live in
// the navigation rail / drawer (NavMenu); on compact windows this bar
// carries the button that opens the drawer.
@Component({
  selector: 'app-nav-bar',
  imports: [RouterLink, MatButtonModule, MatIconModule, ProfileMenu],
  templateUrl: './nav-bar.html',
  styleUrl: './nav-bar.scss',
  host: { '(window:scroll)': 'onScroll()' },
})
export class NavBar {
  protected readonly auth = inject(AuthStore);

  /** Show the navigation-drawer button (signed in, compact window). */
  readonly showMenuButton = input(false);
  readonly menuRequested = output<void>();

  // M3 top app bars sit on the page surface and pick up a tonal container
  // once content scrolls beneath them.
  protected readonly scrolled = signal(false);

  protected onScroll(): void {
    this.scrolled.set(window.scrollY > 0);
  }

  protected signIn(): void {
    void this.auth.signIn();
  }
}
