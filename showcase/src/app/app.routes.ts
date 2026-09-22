import { Routes } from '@angular/router';

import { adminGuard } from './core/auth/admin.guard';
import { authGuard } from './core/auth/auth.guard';
import { BedBoardShell } from './features/bed-board/bed-board-shell/bed-board-shell';
import { insightsRoutes } from './features/insights/insights.routes';
import { profileRoutes } from './features/profile/profile.routes';

export const routes: Routes = [
  {
    path: '',
    loadComponent: () => import('./features/home/home').then((m) => m.Home),
  },
  { path: 'board', component: BedBoardShell, canActivate: [authGuard] },
  { path: 'profile', canActivate: [authGuard], children: profileRoutes },
  { path: 'insights', canActivate: [authGuard], children: insightsRoutes },
  {
    path: 'admin',
    canActivate: [authGuard, adminGuard],
    // Lazy — the admin area (and, since doctors-list.ts, AG Grid) is
    // sizeable and only ever needed by admin users, not the bedside staff
    // who load the bed board on every shift; keeping it out of the main
    // bundle matters more on a phone than on a desk.
    loadChildren: () => import('./features/admin/admin.routes').then((m) => m.adminRoutes),
  },
];
