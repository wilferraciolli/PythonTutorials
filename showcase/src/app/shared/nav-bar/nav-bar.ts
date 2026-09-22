import { Component, inject } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatToolbarModule } from '@angular/material/toolbar';
import { RouterLink } from '@angular/router';

import { AuthStore } from '../../core/auth/auth.store';
import { ProfileMenu } from '../profile-menu/profile-menu';

// App-wide chrome, mounted once in app.html — the one place a signed-out
// visitor finds "Sign in" and a signed-in one finds the profile menu,
// instead of every page rolling its own header.
@Component({
  selector: 'app-nav-bar',
  imports: [RouterLink, MatToolbarModule, MatButtonModule, ProfileMenu],
  templateUrl: './nav-bar.html',
  styleUrl: './nav-bar.scss',
})
export class NavBar {
  protected readonly auth = inject(AuthStore);

  protected signIn(): void {
    void this.auth.signIn();
  }
}
