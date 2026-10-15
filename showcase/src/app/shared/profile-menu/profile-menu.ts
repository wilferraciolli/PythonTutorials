import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { AuthStore } from '@wiltech-labs/ngx-auth';
import { RouterLink } from '@angular/router';

import { UserSession } from '../../core/user/user-session';
import { TranslocoPipe } from '@jsverse/transloco';

// Only mounted by NavBar once `auth.isSignedIn()` is true — this component
// doesn't need its own signed-out branch.
@Component({
  selector: 'app-profile-menu',
  imports: [RouterLink, MatButtonModule, MatIconModule, MatMenuModule, TranslocoPipe],
  templateUrl: './profile-menu.html',
  styleUrl: './profile-menu.scss',
})
export class ProfileMenu {
  protected readonly auth = inject(AuthStore);
  protected readonly session = inject(UserSession);

  protected async signOut(): Promise<void> {
    await this.auth.signOut();
  }
}
