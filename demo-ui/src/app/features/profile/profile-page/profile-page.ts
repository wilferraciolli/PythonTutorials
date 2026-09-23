import { Component, inject } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';

import { CurrentUserStore } from '../../../core/user/current-user.store';

// Read-only — /me's fields (name/email/roleIds) are all marked `readOnly`
// in the API's own metadata (me_service.py); there is no PATCH /me to edit
// them against.
@Component({
  selector: 'app-profile-page',
  imports: [MatCardModule, MatChipsModule],
  templateUrl: './profile-page.html',
  styleUrl: './profile-page.scss',
})
export class ProfilePage {
  protected readonly currentUser = inject(CurrentUserStore);
}
