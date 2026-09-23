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
    loadChildren: () => import('./features/workers-ai/workers-ai.routes').then((m) => m.workersAiRoutes),
  },
  {
    path: 'timeline',
    canActivate: [authGuard],
    loadComponent: () => import('./features/social/timeline-page/timeline-page').then((m) => m.TimelinePage),
  },
  {
    path: 'groups',
    canActivate: [authGuard],
    loadChildren: () => import('./features/social/social.routes').then((m) => m.groupsRoutes),
  },
  {
    // Only admins get the profile's `admin` link; the API enforces it too.
    path: 'admin',
    canActivate: [authGuard],
    loadChildren: () => import('./features/admin/admin.routes').then((m) => m.adminRoutes),
  },
  {
    path: 'ask',
    canActivate: [authGuard],
    loadChildren: () => import('./features/ask/ask.routes').then((m) => m.askRoutes),
  },
  { path: '**', redirectTo: '' },
];
