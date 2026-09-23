import { Component, computed, inject, input, output } from '@angular/core';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink, RouterLinkActive } from '@angular/router';

import { CurrentUserStore } from '../../core/user/current-user.store';
import { DESTINATIONS } from '../destinations';

// The app's destinations as a Material 3 navigation rail (icon over label,
// for medium windows and up) or as the rows of a navigation drawer (icon
// beside label, inside the modal drawer on compact windows). Same list,
// same active state; the shell decides which shape to mount.
@Component({
  selector: 'app-nav-menu',
  imports: [RouterLink, RouterLinkActive, MatIconModule],
  templateUrl: './nav-menu.html',
  styleUrl: './nav-menu.scss',
})
export class NavMenu {
  readonly variant = input<'rail' | 'drawer'>('rail');
  /** Emits after a destination is chosen, so a modal drawer can close. */
  readonly navigated = output<void>();

  private readonly currentUser = inject(CurrentUserStore);

  protected readonly destinations = computed(() =>
    DESTINATIONS.filter(
      (destination) => !destination.adminOnly || !!this.currentUser.link('admin'),
    ),
  );
}
