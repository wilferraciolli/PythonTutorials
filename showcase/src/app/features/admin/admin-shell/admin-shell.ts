import { Component, inject } from '@angular/core';
import { MatTabsModule } from '@angular/material/tabs';
import { RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';

import { I18nStore } from '../../../core/i18n/i18n.store';

// The route tree is now guarded by adminGuard (core/auth/admin.guard.ts),
// which checks CurrentUserStore's role — this shell itself stays a plain
// nav layout. Below the `sm` breakpoint the same 5 routes render as a
// `mat-tab-nav-bar` instead of the desktop sidebar — the sidebar's nav
// links used to wrap onto multiple rows and eat the page on narrow
// screens; a tab strip scrolls/paginates instead of wrapping.
@Component({
  selector: 'app-admin-shell',
  imports: [RouterLink, RouterLinkActive, RouterOutlet, MatTabsModule],
  templateUrl: './admin-shell.html',
  styleUrl: './admin-shell.scss',
})
export class AdminShell {
  protected readonly i18n = inject(I18nStore);
}
