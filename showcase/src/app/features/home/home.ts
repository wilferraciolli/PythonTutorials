import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { RouterLink } from '@angular/router';

// Index of the tutorial projects this showcase app hosts (todos,
// workers-ai, ...). Always shows every card — no sign-in gate here; each
// links to a guarded route, and authGuard bounces a signed-out visitor
// back here, where the nav bar's own "Sign in" button (see nav-bar.html)
// is the only place that flow lives now.
@Component({
  selector: 'app-home',
  imports: [RouterLink, MatButtonModule, MatCardModule, MatIconModule],
  templateUrl: './home.html',
  styleUrl: './home.scss',
})
export class Home {}
