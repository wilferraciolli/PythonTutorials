import { Component, inject, signal } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AuthStore } from '../../core/auth/auth.store';
import { I18nStore } from '../../core/i18n/i18n.store';
import { CurrentUserStore } from '../../core/user/current-user.store';

@Component({
  selector: 'app-profile-menu',
  imports: [RouterLink],
  templateUrl: './profile-menu.html',
  styleUrl: './profile-menu.scss',
})
export class ProfileMenu {
  protected readonly auth = inject(AuthStore);
  protected readonly currentUser = inject(CurrentUserStore);
  protected readonly i18n = inject(I18nStore);

  protected readonly isOpen = signal(false);

  protected toggle(): void {
    this.isOpen.update((open) => !open);
  }

  protected close(): void {
    this.isOpen.set(false);
  }

  protected async signOut(): Promise<void> {
    this.close();
    await this.auth.signOut();
  }
}
