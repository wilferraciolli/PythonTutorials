import { Routes } from '@angular/router';

import { WardForm } from './ward-form/ward-form';
import { WardsList } from './wards-list/wards-list';
import { WardsManagementShell } from './wards-management-shell/wards-management-shell';

export const wardsManagementRoutes: Routes = [
  {
    path: '',
    component: WardsManagementShell,
    children: [
      { path: '', component: WardsList },
      { path: 'new', component: WardForm },
      { path: ':id/edit', component: WardForm },
    ],
  },
];
