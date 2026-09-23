import { Component, computed, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { ILink } from '@wiliamferraciolli/ngx-api-client';
import { RouterLink } from '@angular/router';

import { AuthStore } from '../../core/auth/auth.store';
import { CurrentUserStore } from '../../core/user/current-user.store';

// Index of the tutorial projects this showcase app hosts (todos,
// workers-ai, ...). Always shows every card — no sign-in gate here; each
// links to a guarded route, and authGuard bounces a signed-out visitor
// back here, where the nav bar's own "Sign in" button (see nav-bar.html)
// is the only place that flow lives now.
@Component({
  selector: 'app-home',
  imports: [RouterLink, MatButtonModule, MatCardModule, MatIconModule],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {
  protected readonly auth = inject(AuthStore);
  protected readonly currentUser = inject(CurrentUserStore);

  protected readonly todosError = computed(() => this.missingLink(this.currentUser.myTodosLink()));

  // Each Python project advertises its own chats link on the user profile (see
  // user_profile_service.py in fastapi-cloudflare-ai / fastapi-groq-ai / fastapi-ai).
  // Only one runs locally at a time, so a card whose link isn't there
  // means "that project isn't the one answering" — same 'Not found' as todos.
  protected readonly cloudflareAiError = computed(() => this.missingLink(this.currentUser.link('cloudflareChats')));
  protected readonly groqAiError = computed(() => this.missingLink(this.currentUser.link('groqChats')));
  protected readonly aiError = computed(() => this.missingLink(this.currentUser.link('aiChats')));

  private missingLink(link: ILink | undefined): string | null {
    if (!this.auth.isSignedIn()) return null;
    if (this.currentUser.errorMessage()) return 'Not found';
    if (this.currentUser.profile() && !link) return 'Not found';
    return null;
  }
}
