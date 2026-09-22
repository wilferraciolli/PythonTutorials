import { Routes } from '@angular/router';

// Single public route for now. The app is a front door for the FastAPI/D1
// API: sign in with Clerk, get a token. Guarded areas get added here (with
// `canActivate: [authGuard]`) as the API grows endpoints worth a screen.
export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./features/home/home').then((m) => m.Home),
  },
  { path: '**', redirectTo: '' },
];
