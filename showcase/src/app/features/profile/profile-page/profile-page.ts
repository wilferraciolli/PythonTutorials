import { Component, inject } from '@angular/core';
import { RouterLink } from '@angular/router';

import { I18nStore } from '../../../core/i18n/i18n.store';
import { CurrentUserStore } from '../../../core/user/current-user.store';
import { wardLabel } from '../../../core/i18n/labels';

@Component({
  selector: 'app-profile-page',
  imports: [RouterLink],
  templateUrl: './profile-page.html',
  styleUrl: './profile-page.scss',
})
export class ProfilePage {
  protected readonly currentUser = inject(CurrentUserStore);
  protected readonly i18n = inject(I18nStore);
  protected readonly wardLabel = wardLabel;

  constructor() {
    // Deduped against any in-flight load (see CurrentUserStore) — safe to
    // call even though App already triggers this on sign-in.
    void this.currentUser.ensureLoaded();
  }
}
