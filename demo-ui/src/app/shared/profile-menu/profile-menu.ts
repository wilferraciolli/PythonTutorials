import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { RouterLink } from '@angular/router';

import { AuthStore } from '../../core/auth/auth.store';
import { CurrentUserStore } from '../../core/user/current-user.store';

// Only mounted by NavBar once `auth.isSignedIn()` is true — this component
// doesn't need its own signed-out branch.
@Component({
  selector: 'app-profile-menu',
  imports: [RouterLink, MatButtonModule, MatIconModule, MatMenuModule],
  templateUrl: './profile-menu.html',
  styleUrl: './profile-menu.scss',
})
export class ProfileMenu {
  protected readonly auth = inject(AuthStore);
  protected readonly currentUser = inject(CurrentUserStore);

  protected async signOut(): Promise<void> {
    await this.auth.signOut();
  }
}
