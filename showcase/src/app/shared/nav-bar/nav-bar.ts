import { Component, inject } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { AuthStore } from '../../core/auth/auth.store';
import { CurrentUserStore } from '../../core/user/current-user.store';
import { I18nStore, Locale } from '../../core/i18n/i18n.store';
import { ProfileMenu } from '../profile-menu/profile-menu';

// Short on-control label per locale — the full name (e.g. "English (UK)")
// stays available via `title`/aria-label, this is just what's visible on
// the toggle itself.
const LOCALE_SHORT: Record<Locale, string> = { 'en-GB': 'EN', 'el-GR': 'GR' };

// App-wide chrome, present on every route (mounted once in app.html) — the
// one place a signed-out visitor finds "Sign in" and a signed-in one finds
// primary navigation + the profile menu, instead of every shell rolling
// its own header.
@Component({
  selector: 'app-nav-bar',
  imports: [RouterLink, RouterLinkActive, ProfileMenu],
  templateUrl: './nav-bar.html',
  styleUrl: './nav-bar.scss',
})
export class NavBar {
  protected readonly auth = inject(AuthStore);
  protected readonly currentUser = inject(CurrentUserStore);
  protected readonly i18n = inject(I18nStore);

  protected signIn(): void {
    void this.auth.signIn();
  }

  protected setLocale(locale: Locale): void {
    this.i18n.setLocale(locale);
  }

  protected shortCode(locale: Locale): string {
    return LOCALE_SHORT[locale];
  }
}
