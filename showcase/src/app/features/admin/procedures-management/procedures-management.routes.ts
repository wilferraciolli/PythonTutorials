import { Routes } from '@angular/router';

import { ProcedureForm } from './procedure-form/procedure-form';
import { ProceduresList } from './procedures-list/procedures-list';
import { ProceduresManagementShell } from './procedures-management-shell/procedures-management-shell';

export const proceduresManagementRoutes: Routes = [
  {
    path: '',
    component: ProceduresManagementShell,
    children: [
      { path: '', component: ProceduresList },
      { path: 'new', component: ProcedureForm },
      { path: ':id/edit', component: ProcedureForm },
    ],
  },
];
