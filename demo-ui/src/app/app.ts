import { BreakpointObserver, Breakpoints } from '@angular/cdk/layout';
import { A11yModule } from '@angular/cdk/a11y';
import { Component, computed, inject, signal } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { RouterOutlet } from '@angular/router';
import { map } from 'rxjs';

import { environment } from '../environments/environment';
import { AuthStore } from './core/auth/auth.store';
import { NavBar } from './shared/nav-bar/nav-bar';
import { NavMenu } from './shared/nav-menu/nav-menu';

// The Material 3 adaptive shell. Signed-in visitors get destinations as a
// navigation rail on medium windows and up (>= 600px) and as a modal
// navigation drawer, opened from the top app bar, on compact ones. A
// signed-out visitor has nowhere to navigate to, so the shell is just the
// bar and the page.
@Component({
  selector: 'app-root',
  imports: [RouterOutlet, A11yModule, NavBar, NavMenu],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly version = environment.version;
  protected readonly auth = inject(AuthStore);

  // Breakpoints.XSmall is (max-width: 599.98px) — the M3 compact window class.
  protected readonly compact = toSignal(
    inject(BreakpointObserver)
      .observe(Breakpoints.XSmall)
      .pipe(map((state) => state.matches)),
    { requireSync: true },
  );

  protected readonly showRail = computed(() => this.auth.isSignedIn() && !this.compact());
  protected readonly showMenuButton = computed(() => this.auth.isSignedIn() && this.compact());

  protected readonly menuOpen = signal(false);

  protected openMenu(): void {
    this.menuOpen.set(true);
  }

  protected closeMenu(): void {
    this.menuOpen.set(false);
  }
}
