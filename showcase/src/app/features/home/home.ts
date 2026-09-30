import { Component, computed, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { ILink } from '@wiltech-labs/ngx-api-client';
import { AuthStore } from '@wiltech-labs/ngx-auth';
import { RouterLink } from '@angular/router';

import { TranslationService } from '../../core/i18n/translation.service';
import { UserSession } from '../../core/user/user-session';
import { TranslocoPipe } from '@jsverse/transloco';

// Index of the tutorial projects this showcase app hosts (todos,
// workers-ai, ...). Always shows every card — no sign-in gate here; each
// links to a guarded route, and authGuard bounces a signed-out visitor
// back here, where the nav bar's own "Sign in" button (see nav-bar.html)
// is the only place that flow lives now.
@Component({
  selector: 'app-home',
  imports: [RouterLink, MatButtonModule, MatCardModule, MatIconModule, TranslocoPipe],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {
  protected readonly auth = inject(AuthStore);
  protected readonly session = inject(UserSession);
  private readonly i18n = inject(TranslationService);

  protected readonly todosError = computed(() => this.missingLink(this.session.myTodosLink()));

  // Each Python project advertises its own chats link on the user profile (see
  // user_profile_service.py in fastapi-cloudflare-ai / fastapi-groq-ai / fastapi-ai).
  // Only one runs locally at a time, so a card whose link isn't there
  // means "that project isn't the one answering" — same "not found" as todos.
  protected readonly cloudflareAiError = computed(() =>
    this.missingLink(this.session.link('cloudflareChats')),
  );
  protected readonly groqAiError = computed(() =>
    this.missingLink(this.session.link('groqChats')),
  );

  private missingLink(link: ILink | undefined): string | null {
    if (!this.auth.isSignedIn()) return null;
    if (this.session.errorMessage()) return this.i18n.t('common.notFound');
    if (this.session.profile() && !link) return this.i18n.t('common.notFound');
    return null;
  }
}
