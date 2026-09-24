import { Component, computed, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink } from '@angular/router';

import { CurrentUserStore } from '../../../core/user/current-user.store';

// Read-only — /me's fields (name/email/roleIds) are all marked `readOnly`
// in the API's own metadata (me_service.py); there is no PATCH /me to edit
// them against.
//
// The settings buttons follow the user profile's links: `userSettings` is
// only on your own profile, `systemSettings` only for admins. No link, no
// button — the UI never decides who is an admin itself.
@Component({
  selector: 'app-profile-page',
  imports: [RouterLink, MatButtonModule, MatCardModule, MatChipsModule, MatIconModule],
  templateUrl: './profile-page.html',
  styleUrl: './profile-page.scss',
})
export class ProfilePage {
  protected readonly currentUser = inject(CurrentUserStore);

  protected readonly canEditOwnSettings = computed(() => !!this.currentUser.link('userSettings'));
  protected readonly canEditSystemSettings = computed(
    () => !!this.currentUser.link('systemSettings'),
  );
}
