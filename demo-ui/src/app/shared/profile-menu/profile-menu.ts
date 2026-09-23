import { Component, computed, inject } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { RouterLink } from '@angular/router';

import { AuthStore } from '../../core/auth/auth.store';
import { CurrentUserStore } from '../../core/user/current-user.store';

// Only mounted by NavBar once `auth.isSignedIn()` is true — this component
// doesn't need its own signed-out branch. Just the account's own actions:
// the app's destinations live in the navigation rail / drawer.
@Component({
  selector: 'app-profile-menu',
  imports: [RouterLink, MatIconModule, MatMenuModule],
  templateUrl: './profile-menu.html',
  styleUrl: './profile-menu.scss',
})
export class ProfileMenu {
  protected readonly auth = inject(AuthStore);
  protected readonly currentUser = inject(CurrentUserStore);

  // The avatar shows the first letter of the profile name; until /me has
  // loaded it falls back to a generic account icon.
  protected readonly initial = computed(() => this.currentUser.me()?.name?.trim().charAt(0) ?? '');

  protected async signOut(): Promise<void> {
    await this.auth.signOut();
  }
}
