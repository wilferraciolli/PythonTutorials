import { Component, computed, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { ILink } from '@wiliamferraciolli/ngx-api-client';
import { RouterLink } from '@angular/router';

import { AuthStore } from '../../core/auth/auth.store';
import { CurrentUserStore } from '../../core/user/current-user.store';
import { DESTINATIONS, Destination } from '../../shared/destinations';

// Index of the tutorial projects this showcase app hosts (todos,
// workers-ai, ...). Always shows every card — no sign-in gate here; each
// links to a guarded route, and authGuard bounces a signed-out visitor
// back here, where the app bar's own "Sign in" button (see nav-bar.html)
// and the hero's are the only places that flow lives.
@Component({
  selector: 'app-home',
  imports: [RouterLink, MatButtonModule, MatIconModule],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {
  protected readonly auth = inject(AuthStore);
  protected readonly currentUser = inject(CurrentUserStore);

  protected readonly heading = computed(() => {
    if (!this.auth.isSignedIn()) return 'A FastAPI backend, run through a real app';
    const firstName = this.currentUser.me()?.name?.trim().split(/\s+/)[0];
    return firstName ? `Welcome back, ${firstName}` : 'Welcome back';
  });

  // Each Python project advertises its own link on the user profile (see
  // user_profile_service.py); a card whose link isn't there shows 'Not
  // found' instead of a dead link. The admin card is only shown to admins
  // at all (their profile has the link). demo-ui talks to fastapi-ai only,
  // which serves both AI providers from one AI card; the single-provider
  // projects live in showcase.
  protected readonly cards = computed<HomeCard[]>(() =>
    DESTINATIONS.filter(
      (destination) =>
        destination.homeCard !== false &&
        (!destination.adminOnly || !!this.currentUser.link('admin')),
    ).map((destination) => ({
      ...destination,
      error: destination.linkName
        ? this.missingLink(this.currentUser.link(destination.linkName))
        : null,
    })),
  );

  protected signIn(): void {
    void this.auth.signIn();
  }

  private missingLink(link: ILink | undefined): string | null {
    if (!this.auth.isSignedIn()) return null;
    if (this.currentUser.errorMessage()) return 'Not found';
    if (this.currentUser.profile() && !link) return 'Not found';
    return null;
  }
}

interface HomeCard extends Destination {
  error: string | null;
}
