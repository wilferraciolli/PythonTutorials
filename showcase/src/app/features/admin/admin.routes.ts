import { Routes } from '@angular/router';

import { AdminDashboard } from './admin-dashboard/admin-dashboard';
import { AdminShell } from './admin-shell/admin-shell';
import { doctorsManagementRoutes } from './doctors-management/doctors-management.routes';
import { proceduresManagementRoutes } from './procedures-management/procedures-management.routes';
import { UsersList } from './users-management/users-list/users-list';
import { wardsManagementRoutes } from './wards-management/wards-management.routes';

export const adminRoutes: Routes = [
  {
    path: '',
    component: AdminShell,
    children: [
      { path: '', component: AdminDashboard },
      { path: 'wards', children: wardsManagementRoutes },
      { path: 'doctors', children: doctorsManagementRoutes },
      { path: 'procedures', children: proceduresManagementRoutes },
      { path: 'users', component: UsersList },
    ],
  },
];
