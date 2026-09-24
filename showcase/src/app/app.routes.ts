import { Routes } from '@angular/router';

import { authGuard } from './core/auth/auth.guard';

// The app is a front door for the FastAPI/D1 API: sign in with Clerk, get
// a token, follow the links /me hands back. Home stays public so there's
// always something to render and something to smoke-test Clerk against;
// everything past it needs a session.
export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./features/home/home').then((m) => m.Home),
  },
  {
    path: 'profile',
    canActivate: [authGuard],
    loadChildren: () => import('./features/profile/profile.routes').then((m) => m.profileRoutes),
  },
  {
    path: 'settings',
    canActivate: [authGuard],
    loadChildren: () => import('./features/settings/settings.routes').then((m) => m.settingsRoutes),
  },
  {
    path: 'todos',
    canActivate: [authGuard],
    loadChildren: () => import('./features/todos/todos.routes').then((m) => m.todosRoutes),
  },
  {
    path: 'tags',
    canActivate: [authGuard],
    loadChildren: () => import('./features/tags/tags.routes').then((m) => m.tagsRoutes),
  },
  {
    path: 'workers-ai',
    canActivate: [authGuard],
    loadChildren: () =>
      import('./features/workers-ai/workers-ai.routes').then((m) => m.workersAiRoutes),
  },
  { path: '**', redirectTo: '' },
];
