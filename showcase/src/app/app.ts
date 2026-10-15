import { Component, inject } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { environment } from '../environments/environment';
import { NavBar } from './shared/nav-bar/nav-bar';
import { UserSession } from './core/user/user-session';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, NavBar],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  protected readonly version = environment.version;
  protected readonly session = inject(UserSession);
}
